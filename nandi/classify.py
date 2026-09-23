import re

def make_classifier(rules):
    clean = {str(k): [str(x).lower() for x in v] for k, v in (rules or {}).items()}
    def classify(text):
        text = (text or "").lower()
        scores = {sector: sum(1 for term in terms if re.search(r"\b" + re.escape(term) + r"\b", text))
                  for sector, terms in clean.items()}
        if not scores or max(scores.values()) == 0:
            return "unclassified", 0.0, ["no_sector_rule_match"]
        best = max(scores, key=scores.get)
        total = sum(scores.values())
        confidence = min(1.0, scores[best] / max(1, total))
        return best, confidence, [f"keyword:{term}" for term in clean[best] if re.search(r"\b" + re.escape(term) + r"\b", text)]
    return classify
