from collections import Counter
import re

STOPWORDS = set(["the", "and", "of", "for", "to", "in", "with", "on", "a", "an"])

def generate_cluster_label(signals, top_k=5):
    words = []
    for s in signals:
        tokens = re.findall(r"[A-Za-z]{4,}", s["text"].lower())
        words.extend([t for t in tokens if t not in STOPWORDS])

    most_common = [w for w, _ in Counter(words).most_common(top_k)]
    return " / ".join(most_common[:3]).title()