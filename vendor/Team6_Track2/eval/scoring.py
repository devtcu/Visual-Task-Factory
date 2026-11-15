"""Deterministic answer extraction and scoring; no model judge."""
import json
import math
import re


def normal_label(value):
    return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()


def parse_answer(response, task):
    matches = list(re.finditer(r"FINAL\s+ANSWER\s*:\s*", response or "", re.I))
    text = response[matches[-1].end():].strip() if matches else (response or "").strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text).strip()
    if not text:
        return None
    kind = task["answer_type"]
    if kind == "sequence":
        try:
            value, _ = json.JSONDecoder().raw_decode(text)
            if isinstance(value, dict): value = value.get("placements", value.get("answer", value))
            if isinstance(value, list): return value
        except (ValueError, TypeError):
            pass
        if task["pipeline"] == "reconstruction": return None
        if not matches and len(text) > 300: return None
        if all(isinstance(v, (int, float)) for v in task["answer"]):
            return [float(n) for n in re.findall(r"[-+]?\d+(?:\.\d+)?", text)]
        return [part.strip(" \n\"'[]*.") for part in re.split(r",|;|->|→", text) if part.strip()]
    if kind in ("number", "integer"):
        if not matches and len(text) > 150: return None
        text = text.replace("−", "-").replace(",", "")
        match = re.search(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?", text)
        if not match: return None
        value = float(match.group())
        return value if math.isfinite(value) else None
    if not matches and len(text) > 300: return None
    return text.splitlines()[0].strip(" \"'`*.")


def score_answer(task, parsed, task_root=None):
    if parsed is None: return {"correct": False, "reason": "No answer could be extracted"}
    if task["pipeline"] == "reconstruction":
        from validate.visual_reconstruction.scoring import score_answer as spatial_score
        return spatial_score(task, parsed, task_root)
    expected, kind = task["answer"], task["answer_type"]
    if kind in ("number", "integer"):
        try:
            value = float(parsed); truth = float(expected)
            tolerance = 0 if kind == "integer" else float(task.get("tolerance_abs", abs(truth) * task.get("tolerance_rel", 0)))
            correct = math.isfinite(value) and abs(value - truth) <= tolerance + 1e-10
        except (TypeError, ValueError): correct = False
    elif kind == "sequence":
        if not isinstance(parsed, list): correct = False
        elif all(isinstance(v, (int, float)) for v in expected):
            try: correct = len(parsed) == len(expected) and all(float(a) == float(b) for a, b in zip(parsed, expected))
            except (TypeError, ValueError): correct = False
        else: correct = [normal_label(v) for v in parsed] == [normal_label(v) for v in expected]
    else: correct = normal_label(parsed) == normal_label(expected)
    return {"correct": bool(correct)}
