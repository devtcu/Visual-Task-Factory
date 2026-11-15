"""Answer extraction and scoring. Plain code, no model in the loop."""
import json, re

NUM = r"[-+]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?:[eE][-+]?\d+)?|[-+]?\.\d+"


def final_line(response):
    hits = re.findall(r"FINAL ANSWER\s*[:\-]\s*(.+)", response or "", flags=re.I)
    return hits[-1].strip().strip("*`").strip() if hits else ""


def to_number(text):
    m = re.search(NUM, text.replace("−", "-"))
    return float(m.group(0).replace(",", "")) if m else None


def norm_label(text):
    return re.sub(r"[^a-z0-9]+", " ", str(text).lower()).strip()


def extract(response, task):
    """The parsed answer as a string ('' if none found)."""
    line, kind = final_line(response), task["answer_type"]
    if not line:
        return ""
    if kind in ("number", "integer"):
        v = to_number(line)
        return "" if v is None else (str(int(round(v))) if kind == "integer" and abs(v - round(v)) < 1e-9 else repr(v))
    if kind == "multiple_choice":   # only the task's own option letters count ("I think it is C" -> C, not I)
        letters = "".join(chr(65 + i) for i in range(len(task.get("options") or "ABCD")))
        m = re.match(rf"\W*([{letters}])\b", line.upper()) or list(re.finditer(rf"\b([{letters}])\b", line.upper()))[-1:] or [None]
        m = m if not isinstance(m, list) else m[0]
        return m.group(1) if m else ""
    if kind == "sequence":
        return json.dumps([norm_label(x) for x in re.split(r"\s*(?:,|->|→|>|;)\s*", line.strip("[]() .")) if norm_label(x)])
    return norm_label(line)


def is_correct(parsed, task):
    if parsed == "":
        return 0
    ref, kind = task["answer"], task["answer_type"]
    if kind == "integer":
        try: return int(float(parsed) == float(ref))
        except ValueError: return 0
    if kind == "number":
        try: v = float(parsed)
        except ValueError: return 0
        if "tolerance_abs" in task:
            return int(abs(v - ref) <= task["tolerance_abs"] + 1e-12)
        return int(abs(v - ref) <= task["tolerance_rel"] * abs(ref) + 1e-12)
    if kind == "multiple_choice":
        return int(parsed == str(ref).upper())
    if kind == "sequence":
        return int(json.loads(parsed) == [norm_label(x) for x in ref])
    return int(parsed == norm_label(ref))


def trap_hit(parsed, task):
    """Names of the predicted mistakes (called shots) whose wrong answer the parsed answer matches, under the task's tolerance."""
    if parsed == "":
        return ""
    return ",".join(name for name, v in task.get("wrong_answers", {}).items() if is_correct(parsed, {**task, "answer": v}))
