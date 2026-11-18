"""The automatic checks.

label_match:     chosen label equals the expected label (ignoring case and spaces).
confident_match: label_match AND confidence >= CONFIDENCE_THRESHOLD (the same threshold the agent uses).
"""
from config import CONFIDENCE_THRESHOLD


def _norm(label: str) -> str:
    label = (label or "").strip().lower()
    return "" if label == "none" else label  # "none" in the dataset == empty label from the model


def _correct(outputs: dict, reference_outputs: dict) -> bool:
    return _norm(outputs.get("label")) == _norm(reference_outputs.get("label"))


def label_match(outputs: dict, reference_outputs: dict) -> dict:
    return {"key": "label_match", "score": int(_correct(outputs, reference_outputs))}


def confident_match(outputs: dict, reference_outputs: dict) -> dict:
    ok = _correct(outputs, reference_outputs) and outputs.get("confidence", 0) >= CONFIDENCE_THRESHOLD
    return {"key": "confident_match", "score": int(ok)}
