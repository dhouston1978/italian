#!/usr/bin/env python3
"""Generate 300 question sentences (template H) to verify English tense forms."""
import sys
import os

os.environ["ITALIAN_DRILL_DATA_DIR"] = "/tmp/italian_drill_test_data"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "italian_drill"))

from italian_drill import (
    VERBS, TENSES, generate_sentence, VERB_MAP,
    TENSE_EN, SUBJECT_EN,
)

import random
random.seed(77)

lines = []
count = 0
attempts = 0
while count < 300 and attempts < 8000:
    attempts += 1
    verb_info = random.choice(VERBS)
    verb = verb_info["infinitive"]
    difficulty_unlocked = True
    gender = random.choice(["m", "f"])

    spec = generate_sentence(verb, list(TENSES), difficulty_unlocked, gender)

    if spec.template != "H":
        continue

    count += 1
    it = spec.build_italian()
    en = spec.build_english()
    tense = TENSE_EN.get(spec.tense, spec.tense)
    qw_it = spec.question_word["it"] if spec.question_word else "?"

    lines.append(f"{count:3d}. [{spec.template}] [{tense}] [{spec.subject}] [{qw_it}]\n     IT: {it}\n     EN: {en}\n")

with open("question_audit.txt", "w", encoding="utf-8") as f:
    f.write("QUESTION AUDIT — 300 Question Sentences\n")
    f.write("=" * 60 + "\n\n")
    for line in lines:
        f.write(line + "\n")

print(f"Generated {count} question sentences (from {attempts} attempts) to question_audit.txt")
