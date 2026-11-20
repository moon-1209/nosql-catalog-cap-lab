"""NLU (G20): chuẩn hóa ➔ luật khẩn cấp ➔ PhoBERT (hoặc luật G14) ➔ slot từ bản đồ.

Hai chế độ cùng interface `understand(text) -> IntentResult`:
- "phobert": luật cap_cuu của G14 chạy trước; không khớp ➔ PhoBERT trên câu đã tách từ.
- "rule": toàn bộ luật G14 (để so sánh ở G23).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Protocol

from nlu import slots as slot_lib
from voice import intent as rule_intent
from voice.text_norm import normalize

EMERGENCY_RULE: rule_intent.Rule = next(r for r in rule_intent.RULES_HIGH if r[0] == "cap_cuu")


@dataclass(frozen=True)
class IntentResult:
    intent: str
    intent_conf: float
    slots: dict[str, str] = field(default_factory=dict)
    source: str = "rule"                       # "rule_emergency" | "phobert" | "rule"
    top3: list[tuple[str, float]] = field(default_factory=list)


class IntentModel(Protocol):
    def predict(self, text_seg: str) -> list[tuple[str, float]]:
        """Mọi nhãn kèm xác suất, sắp giảm dần."""


def emergency_rule(text: str) -> bool:
    """Phần cap_cuu của luật G14 (cụm từ mạnh hoặc từ đơn); khớp ➔ cap_cuu."""
    _, strong, weak = EMERGENCY_RULE
    return rule_intent.match_rule(rule_intent.tokenize(text), strong, weak) > 0


class Nlu:
    def __init__(self, mode: str, model: IntentModel | None = None,
                 segment: Callable[[str], str] | None = None) -> None:
        if mode not in ("rule", "phobert"):
            raise ValueError(f"unknown nlu mode: {mode}")
        if mode == "phobert" and (model is None or segment is None):
            raise ValueError("phobert mode needs model and segment")
        self.mode = mode
        self.model = model
        self.segment = segment

    def understand(self, text: str) -> IntentResult:
        t = normalize(text)
        if t == "":
            return IntentResult("unknown", 0.0, {}, "rule", [])
        s = slot_lib.extract(t)
        if emergency_rule(t):
            return IntentResult("cap_cuu", 1.0, s, "rule_emergency", [])
        if self.mode == "rule":
            r = rule_intent.classify(t)
            return IntentResult(r.intent, r.conf, s, "rule", [(r.intent, r.conf)])
        assert self.model is not None and self.segment is not None
        probs = self.model.predict(self.segment(t))
        top3 = [(name, float(p)) for name, p in probs[:3]]
        return IntentResult(top3[0][0], top3[0][1], s, "phobert", top3)
