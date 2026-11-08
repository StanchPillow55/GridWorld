import os
import json
import logging
from typing import Any, List, Optional
import numpy as np
import requests

from backend.app.controllers.base import BaseController
from backend.app.schemas import ActionProposal, ActionType

logger = logging.getLogger(__name__)


class AIController(BaseController):
    """
    Model-based AI Controller that leverages LLMs or local models
    via structured JSON prompts to propose grid control actions.
    Falls back gracefully to a simulation-guided agent when no LLM
    endpoint or API key is active.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gpt-4o-mini",
        ollama_url: Optional[str] = None
    ):
        super().__init__(name="AI Autonomous Agent")
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model_name
        self.ollama_url = ollama_url or os.getenv("OLLAMA_HOST", "http://localhost:11434")

    def _query_ollama(self, prompt: str) -> Optional[dict]:
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
            if res.status_code == 200:
                data = res.json()
                return json.loads(data.get("response", "{}"))
        except Exception:
            return None
        return None

    def _query_openai(self, prompt: str) -> Optional[dict]:
        if not self.api_key:
            return None
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
                            "You are an electrical transmission grid operator. "
                            "Analyze the grid state and propose a structured control action in JSON. "
                            "Valid action_type: 'noop', 'switch_line'. Return only valid JSON: "
                            "{\"action_type\": \"...\", \"target_id\": 0, \"rationale\": \"...\"}"
                        )
                    },
                    {"role": "user", "content": prompt}
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.1
            }
            res = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=10)
            if res.status_code == 200:
                body = res.json()
                content = body["choices"][0]["message"]["content"]
                return json.loads(content)
        except Exception as e:
            logger.warning(f"OpenAI API call failed: {e}")
            return None
        return None

    def act(self, observation: Any, legal_actions: Optional[List[Any]] = None) -> ActionProposal:
        max_rho = float(np.max(observation.rho))
        mean_rho = float(np.mean(observation.rho))
        worst_line = int(np.argmax(observation.rho))
        disconnected = [int(i) for i in np.where(~observation.line_status)[0]]

        prompt = (
            f"Current Grid Status:\n"
            f"- Peak line loading: {max_rho:.3f}\n"
            f"- Mean line loading: {mean_rho:.3f}\n"
            f"- Highest loaded line: Line {worst_line} (rho: {max_rho:.3f})\n"
            f"- Disconnected lines: {disconnected}\n"
            f"- Thermal congestion limit: 0.90\n"
            "Recommend an action (noop or switch_line)."
        )

        # 1. Try OpenAI if key is configured
        llm_resp = self._query_openai(prompt)

        # 2. Try Ollama if local instance is up
        if not llm_resp:
            llm_resp = self._query_ollama(prompt)

        # Parse LLM response if received
        if llm_resp and "action_type" in llm_resp:
            action_type_str = llm_resp.get("action_type", "noop").lower()
            target_id = llm_resp.get("target_id")
            rationale = llm_resp.get("rationale", "LLM-generated grid strategy")
            
            action_type = ActionType.NOOP
            if action_type_str == "switch_line":
                action_type = ActionType.SWITCH_LINE

            return ActionProposal(
                action_type=action_type,
                target_id=target_id,
                rationale=f"[LLM Agent] {rationale}"
            )

        # 3. Fallback: Simulation-guided autonomous reasoning
        if max_rho < 0.88 and not disconnected:
            return ActionProposal(
                action_type=ActionType.NOOP,
                rationale="[AI Autonomous Agent] Grid stability optimal (max rho < 0.88). Passive monitoring."
            )

        # Look-ahead simulation for line reconnection or relief
        if disconnected:
            for l_id in disconnected:
                try:
                    act = observation.action_space({"set_line_status": [(l_id, 1)]})
                    sim_obs, _, _, _ = observation.simulate(act)
                    if sim_obs is not None and np.max(sim_obs.rho) < 0.92:
                        return ActionProposal(
                            action_type=ActionType.SWITCH_LINE,
                            target_id=l_id,
                            rationale=f"[AI Autonomous Agent] Look-ahead simulation confirmed safe reconnection of Line {l_id} (projected rho {float(np.max(sim_obs.rho)):.2f})."
                        )
                except Exception:
                    continue

        if max_rho >= 0.90:
            try:
                act = observation.action_space({"change_line_status": [worst_line]})
                sim_obs, _, _, _ = observation.simulate(act)
                if sim_obs is not None and np.max(sim_obs.rho) < max_rho:
                    return ActionProposal(
                        action_type=ActionType.SWITCH_LINE,
                        target_id=worst_line,
                        rationale=f"[AI Autonomous Agent] High overload detected on Line {worst_line}. Topological reroute reduces peak rho to {float(np.max(sim_obs.rho)):.2f}."
                    )
            except Exception:
                pass

        return ActionProposal(
            action_type=ActionType.NOOP,
            rationale=f"[AI Autonomous Agent] Thermal loading at {max_rho:.2f}. No intervention superior to current state."
        )
