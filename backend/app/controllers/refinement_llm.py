import os
import json
import time
import logging
from typing import Any, List, Optional, Tuple
import requests
import numpy as np

from backend.app.controllers.base import BaseController
from backend.app.schemas import (
    ActionProposal,
    ActionType,
    CandidateAction,
    ProposalRoundRecord
)

logger = logging.getLogger(__name__)


class RefinementLLMController(BaseController):
    """
    Controller 5: LLM Controller with Online Simulation Feedback & Refinement.
    Implements the instrumented Propose -> Simulate -> Evaluate -> Revise loop:
    1. LLM proposes candidate action from catalog.
    2. Grid2Op simulates forecasted effect (obs.simulate(action, time_step=1)).
    3. Independent evaluator scores physical outcome.
    4. If congested or divergent, LLM receives structured feedback and revises up to max_rounds (default: 3).
    5. Highest-ranked evaluated proposal is executed.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gpt-4o-mini",
        ollama_url: Optional[str] = None,
        max_rounds: int = 3,
        overload_threshold: float = 0.90
    ):
        super().__init__(name="Simulation-Guided Refinement LLM", controller_type="refinement_llm")
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model_name
        self.ollama_url = ollama_url or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.max_rounds = max_rounds
        self.overload_threshold = overload_threshold

    def _call_model(self, messages: List[dict]) -> Optional[dict]:
        t0 = time.perf_counter()

        # 1. Try OpenAI if key is configured
        if self.api_key:
            try:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": self.model_name,
                    "messages": messages,
                    "response_format": {"type": "json_object"},
                    "temperature": 0.1
                }
                res = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=10)
                latency = (time.perf_counter() - t0) * 1000.0

                if res.status_code == 200:
                    body = res.json()
                    usage = body.get("usage", {})
                    p_tok = usage.get("prompt_tokens", 0)
                    c_tok = usage.get("completion_tokens", 0)

                    self.resource_usage.model_calls += 1
                    self.resource_usage.prompt_tokens += p_tok
                    self.resource_usage.completion_tokens += c_tok
                    self.resource_usage.total_tokens += (p_tok + c_tok)
                    self.resource_usage.model_latency_ms += latency
                    self.resource_usage.estimated_cost_usd += (p_tok * 0.00000015 + c_tok * 0.00000060)

                    content = body["choices"][0]["message"]["content"]
                    return json.loads(content)
            except Exception as e:
                logger.warning(f"OpenAI call failed in RefinementLLM: {e}")

        # 2. Try Ollama local
        try:
            prompt_str = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in messages])
            res = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": "llama3.2",
                    "prompt": prompt_str,
                    "format": "json",
                    "stream": False
                },
                timeout=5
            )
            latency = (time.perf_counter() - t0) * 1000.0
            if res.status_code == 200:
                data = res.json()
                self.resource_usage.model_calls += 1
                self.resource_usage.prompt_tokens += data.get("prompt_eval_count", 0)
                self.resource_usage.completion_tokens += data.get("eval_count", 0)
                self.resource_usage.total_tokens += (data.get("prompt_eval_count", 0) + data.get("eval_count", 0))
                self.resource_usage.model_latency_ms += latency
                return json.loads(data.get("response", "{}"))
        except Exception:
            pass

        return None

    def act(
        self,
        observation: Any,
        candidates: List[CandidateAction],
        adapter: Any,
        step_idx: int = 1
    ) -> Tuple[ActionProposal, List[ProposalRoundRecord]]:
        current_max_rho = float(np.max(observation.rho))
        mean_rho = float(np.mean(observation.rho))
        worst_line = int(np.argmax(observation.rho))
        candidates_by_id = {c.action_id.upper(): c for c in candidates}

        catalog_desc = "\n".join([f"- {c.action_id}: {c.description}" for c in candidates])

        system_prompt = (
            "You are an autonomous electrical grid operator. "
            "You will propose actions, receive simulation forecast feedback, and revise your decisions if needed. "
            "Output JSON only: {\"action_id\": \"A...\", \"rationale\": \"...\"}"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    f"Step {step_idx}: Current telemetry: Peak line rho = {current_max_rho:.3f} (Line #{worst_line}), "
                    f"Mean rho = {mean_rho:.3f}.\n"
                    f"Candidate Actions:\n{catalog_desc}\n\n"
                    "Propose your initial action_id."
                )
            }
        ]

        round_records: List[ProposalRoundRecord] = []
        best_candidate = candidates[0]
        best_sim_rho = current_max_rho
        best_sim_done = False

        # Attempt online refinement loop up to max_rounds
        for round_num in range(1, self.max_rounds + 1):
            model_resp = self._call_model(messages)
            
            # If model is unavailable, run structured simulation-guided revision
            if not model_resp or "action_id" not in model_resp:
                self.fallback_used = True
                return self._offline_refinement_policy(
                    observation=observation,
                    candidates=candidates,
                    adapter=adapter,
                    step_idx=step_idx
                )

            proposed_id = str(model_resp.get("action_id", "A0")).strip().upper()
            rationale = str(model_resp.get("rationale", "Proposed by LLM."))

            candidate = candidates_by_id.get(proposed_id, candidates[0])

            # Simulate forecasted effect
            self.resource_usage.simulation_calls += 1
            proposal = ActionProposal(
                action_id=candidate.action_id,
                action_type=candidate.action_type,
                target_id=candidate.target_id,
                target_bus=candidate.target_bus,
                redispatch_val=candidate.redispatch_val,
                rationale=rationale
            )
            g2op_action, is_valid = adapter.create_grid2op_action(proposal)

            sim_max_rho = 999.0
            sim_done = True
            feedback = ""

            if is_valid:
                try:
                    sim_obs, sim_r, sim_done, sim_info = observation.simulate(g2op_action, time_step=1)
                    if sim_obs is not None:
                        sim_max_rho = float(np.max(sim_obs.rho))
                        if sim_done:
                            feedback = f"Simulation feedback: Action {proposed_id} causes grid collapse/blackout! Revise immediately."
                        elif sim_max_rho >= 1.0:
                            feedback = f"Simulation feedback: Action {proposed_id} leaves thermal overload (peak rho: {sim_max_rho:.3f} >= 1.0). Revise proposal."
                        elif sim_max_rho > current_max_rho and current_max_rho >= self.overload_threshold:
                            feedback = f"Simulation feedback: Action {proposed_id} increases congestion to {sim_max_rho:.3f} (worse than current {current_max_rho:.3f}). Revise proposal."
                        else:
                            feedback = f"Simulation feedback: Action {proposed_id} safe and effective (forecast peak rho: {sim_max_rho:.3f}). Accepted."
                    else:
                        feedback = f"Simulation feedback: Action {proposed_id} diverged numerical solver."
                except Exception as e:
                    feedback = f"Simulation feedback: Exception {str(e)}."
            else:
                feedback = f"Action {proposed_id} is illegal in current state."

            is_accepted = (not sim_done) and (sim_max_rho < 0.95 or sim_max_rho <= best_sim_rho)

            if not sim_done and sim_max_rho < best_sim_rho:
                best_sim_rho = sim_max_rho
                best_sim_done = False
                best_candidate = candidate

            round_record = ProposalRoundRecord(
                round_index=round_num,
                action_id=candidate.action_id,
                action_type=candidate.action_type,
                target_id=candidate.target_id,
                rationale=rationale,
                simulated_max_rho=round(sim_max_rho, 4) if sim_max_rho < 900 else 999.0,
                simulated_done=sim_done,
                feedback=feedback,
                selected=False
            )
            round_records.append(round_record)

            # If action solved congestion or reached satisfactory state, break early
            if is_accepted and sim_max_rho < self.overload_threshold:
                round_record.selected = True
                break

            # If another round is allowed, append feedback to conversation
            if round_num < self.max_rounds:
                messages.append({"role": "assistant", "content": json.dumps({"action_id": proposed_id, "rationale": rationale})})
                messages.append({
                    "role": "user",
                    "content": f"{feedback}\nPlease evaluate alternative options from the catalog and provide a revised action_id."
                })

        # Mark chosen round
        for r in round_records:
            if r.action_id == best_candidate.action_id:
                r.selected = True
                break

        chosen_proposal = ActionProposal(
            action_id=best_candidate.action_id,
            action_type=best_candidate.action_type,
            target_id=best_candidate.target_id,
            target_bus=best_candidate.target_bus,
            redispatch_val=best_candidate.redispatch_val,
            rationale=f"[Refinement LLM] Selected {best_candidate.action_id} after {len(round_records)} refinement rounds (forecast peak rho: {best_sim_rho:.3f})."
        )
        return chosen_proposal, round_records

    def _offline_refinement_policy(
        self,
        observation: Any,
        candidates: List[CandidateAction],
        adapter: Any,
        step_idx: int
    ) -> Tuple[ActionProposal, List[ProposalRoundRecord]]:
        """
        Deterministic emulation of the 3-round Propose -> Simulate -> Evaluate -> Revise loop
        used when external LLM endpoints are unreachable, with explicit fallback labeling.
        """
        current_max_rho = float(np.max(observation.rho))
        round_records: List[ProposalRoundRecord] = []
        best_candidate = candidates[0]
        best_sim_rho = current_max_rho

        # Construct a sensible sequence of candidate actions across refinement rounds:
        # If congested, test across both origin and extremity substation lines
        test_queue = []
        if current_max_rho >= self.overload_threshold:
            # First candidate: try a line on one end of the corridor
            if len(candidates) > 1:
                test_queue.append(candidates[1])
            # Second candidate: try a line on the other end of the corridor (e.g. index 4: Line 7)
            if len(candidates) > 4:
                test_queue.append(candidates[4])
            elif len(candidates) > 2:
                test_queue.append(candidates[2])
            # Third candidate: try next candidate
            if len(candidates) > 2 and candidates[2] not in test_queue:
                test_queue.append(candidates[2])
            elif len(candidates) > 3 and candidates[3] not in test_queue:
                test_queue.append(candidates[3])
        else:
            test_queue.append(candidates[0])
            if len(candidates) > 1:
                test_queue.append(candidates[1])

        for r_idx, cand in enumerate(test_queue[:self.max_rounds]):
            self.resource_usage.simulation_calls += 1
            prop = ActionProposal(
                action_id=cand.action_id,
                action_type=cand.action_type,
                target_id=cand.target_id,
                target_bus=cand.target_bus,
                redispatch_val=cand.redispatch_val,
                rationale=cand.description
            )
            g2op_act, is_valid = adapter.create_grid2op_action(prop)

            sim_max_rho = 999.0
            sim_done = True
            feedback = ""

            if is_valid:
                try:
                    sim_obs, _, sim_done, _ = observation.simulate(g2op_act, time_step=1)
                    if sim_obs is not None:
                        sim_max_rho = float(np.max(sim_obs.rho))
                        if sim_done:
                            feedback = f"Simulation feedback: {cand.action_id} causes blackout. Rejected."
                        elif sim_max_rho >= 1.0:
                            feedback = f"Simulation feedback: {cand.action_id} leaves severe overload (rho: {sim_max_rho:.3f}). Rejected, revising."
                        else:
                            feedback = f"Simulation feedback: {cand.action_id} relieves overload (rho: {sim_max_rho:.3f}). Accepted."
                except Exception as e:
                    feedback = f"Simulation exception: {e}"

            if not sim_done and sim_max_rho < best_sim_rho:
                best_sim_rho = sim_max_rho
                best_candidate = cand

            round_records.append(
                ProposalRoundRecord(
                    round_index=r_idx + 1,
                    action_id=cand.action_id,
                    action_type=cand.action_type,
                    target_id=cand.target_id,
                    rationale=cand.description,
                    simulated_max_rho=round(sim_max_rho, 4) if sim_max_rho < 900 else 999.0,
                    simulated_done=sim_done,
                    feedback=feedback,
                    selected=False
                )
            )

            if not sim_done and sim_max_rho < self.overload_threshold:
                break

        for r in round_records:
            if r.action_id == best_candidate.action_id:
                r.selected = True
                break

        chosen = ActionProposal(
            action_id=best_candidate.action_id,
            action_type=best_candidate.action_type,
            target_id=best_candidate.target_id,
            target_bus=best_candidate.target_bus,
            redispatch_val=best_candidate.redispatch_val,
            rationale=f"[Simulation-Guided Refinement - Offline Fallback] Selected {best_candidate.action_id} after {len(round_records)} evaluation rounds (projected rho: {best_sim_rho:.3f})."
        )
        return chosen, round_records
