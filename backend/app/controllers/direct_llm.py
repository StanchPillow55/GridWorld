import os
import json
import time
import logging
from typing import Any, List, Optional, Tuple
import requests

from backend.app.controllers.base import BaseController
from backend.app.schemas import (
    ActionProposal,
    ActionType,
    CandidateAction,
    ProposalRoundRecord
)

logger = logging.getLogger(__name__)


class DirectLLMController(BaseController):
    """
    Controller 4: Direct LLM Controller.
    Single-shot action selection from candidate action catalog without simulation feedback or refinement.
    Tracks model calls, tokens, latency, and estimated cost.
    Strictly 0 simulation calls.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gpt-4o-mini",
        ollama_url: Optional[str] = None
    ):
        super().__init__(name="Direct LLM Controller (Single-Shot)", controller_type="direct_llm")
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model_name
        self.ollama_url = ollama_url or os.getenv("OLLAMA_HOST", "http://localhost:11434")

    def _call_model(self, prompt: str) -> Optional[dict]:
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
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You are an autonomous electrical grid operator. "
                                "Review the grid state and candidate actions, and pick exactly ONE action_id. "
                                "Output JSON only: {\"action_id\": \"A0\", \"rationale\": \"...\"}"
                            )
                        },
                        {"role": "user", "content": prompt}
                    ],
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
                    # gpt-4o-mini pricing: $0.15/1M input, $0.60/1M output
                    self.resource_usage.estimated_cost_usd += (p_tok * 0.00000015 + c_tok * 0.00000060)

                    content = body["choices"][0]["message"]["content"]
                    return json.loads(content)
            except Exception as e:
                logger.warning(f"OpenAI call failed in DirectLLM: {e}")

        # 2. Try Ollama local
        try:
            res = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": "llama3.2",
                    "prompt": prompt,
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
        import numpy as np

        max_rho = float(np.max(observation.rho))
        mean_rho = float(np.mean(observation.rho))
        worst_line = int(np.argmax(observation.rho))

        # Format prompt with candidate catalog
        catalog_desc = "\n".join([f"- {c.action_id}: {c.description}" for c in candidates])
        prompt = (
            f"Step: {step_idx}\n"
            f"Current Grid Telemetry:\n"
            f"- Peak line loading (rho): {max_rho:.3f} (Worst line: #{worst_line})\n"
            f"- Mean line loading: {mean_rho:.3f}\n"
            f"Available Candidate Actions:\n"
            f"{catalog_desc}\n\n"
            "Select the best action_id to protect grid resilience. Return JSON only: {\"action_id\": \"A...\", \"rationale\": \"...\"}"
        )

        model_resp = self._call_model(prompt)

        if model_resp and "action_id" in model_resp:
            action_id = str(model_resp.get("action_id", "A0")).strip()
            rationale = str(model_resp.get("rationale", "Direct LLM decision."))

            # Match chosen action from catalog
            for c in candidates:
                if c.action_id.lower() == action_id.lower():
                    return ActionProposal(
                        action_id=c.action_id,
                        action_type=c.action_type,
                        target_id=c.target_id,
                        target_bus=c.target_bus,
                        redispatch_val=c.redispatch_val,
                        rationale=f"[Direct LLM] {rationale}"
                    ), []

        # Explicit fallback if model is unconfigured / offline
        self.fallback_used = True
        return ActionProposal(
            action_id="A0",
            action_type=ActionType.NOOP,
            rationale="[Fallback - Offline Mode] Model endpoint unreachable; defaulting to passive monitoring (labeled as fallback)."
        ), []
