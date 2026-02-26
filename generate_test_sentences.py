#!/usr/bin/env python3
"""Generate 500 test sentences for nonsense audit."""
import sys
import os

# Set up data dir to avoid errors
os.environ["ITALIAN_DRILL_DATA_DIR"] = "/tmp/italian_drill_test_data"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "italian_drill"))

from italian_drill import (
    VERBS, TENSES, generate_sentence, VERB_MAP,
    TENSE_EN, SUBJECT_EN,
)

import random
random.seed(42)

lines = []
for i in range(500):
    verb_info = random.choice(VERBS)
    verb = verb_info["infinitive"]
    difficulty_unlocked = random.random() < 0.7
    gender = random.choice(["m", "f"])

    spec = generate_sentence(verb, list(TENSES), difficulty_unlocked, gender)
    it = spec.build_italian()
    en = spec.build_english()
    tense = TENSE_EN.get(spec.tense, spec.tense)
    subj = spec.subject

    lines.append(f"{i+1:3d}. [{spec.template}] [{tense}] [{subj}]\n     IT: {it}\n     EN: {en}\n")

with open("nonsense_audit.txt", "w", encoding="utf-8") as f:
    f.write("NONSENSE AUDIT — 500 Generated Sentences\n")
    f.write("=" * 60 + "\n\n")
    for line in lines:
        f.write(line + "\n")

print(f"Generated {len(lines)} sentences to nonsense_audit.txt")
