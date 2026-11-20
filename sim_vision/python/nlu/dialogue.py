"""Ghép NLU + policy cho STT server (G20). Trạng thái hội thoại (clarify_count, last_response) giữ theo từng kết nối.

Log info: intent, conf, source, action, nlu_ms — KHÔNG có văn bản.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from nlu import config, policy
from nlu.nlu import IntentResult, Nlu

log = logging.getLogger("nlu")


class DialogueEngine:
    def __init__(self, nlu: Nlu, threshold: float = config.CONF_THRESHOLD_DEFAULT) -> None:
        self.nlu = nlu
        self.threshold = threshold

    def __call__(self, text: str, state: dict[str, Any]) -> dict[str, Any]:
        """Trả các trường của message transcript; cập nhật `state` tại chỗ."""
        t0 = time.perf_counter()
        r: IntentResult = self.nlu.understand(text)
        p = policy.decide(r, int(state.get("clarify_count", 0)), state.get("last_response"), self.threshold)
        nlu_ms = (time.perf_counter() - t0) * 1000.0
        state["clarify_count"] = int(state.get("clarify_count", 0)) + 1 if p.action == "clarify" else 0
        if p.action != "repeat":
            state["last_response"] = p.response
        log.info("intent=%s conf=%.3f source=%s action=%s nlu_ms=%.1f", r.intent, r.intent_conf, r.source, p.action,
                 nlu_ms)
        return {"intent": r.intent, "intent_conf": round(r.intent_conf, 4), "slots": r.slots, "response": p.response,
                "action": p.action, "target": p.target, "nlu_ms": nlu_ms, "source": r.source}


def build_engine(mode: str, device: str = "auto") -> DialogueEngine:
    """mode "rule" ➔ luật G14, ngưỡng 0.6; "phobert" ➔ model G19 và ngưỡng trong threshold.json."""
    if mode == "rule":
        return DialogueEngine(Nlu("rule"), config.CONF_THRESHOLD_DEFAULT)
    from nlu.phobert_intent import PhoBertIntent
    from nlu.segment import segment

    model = PhoBertIntent(config.PHOBERT_FT_DIR, device)
    return DialogueEngine(Nlu("phobert", model, segment), model.threshold)
