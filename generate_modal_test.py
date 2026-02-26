#!/usr/bin/env python3
"""Generate 200 modal sentences to find English prompt bugs."""
import sys
import os

os.environ["ITALIAN_DRILL_DATA_DIR"] = "/tmp/italian_drill_test_data"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "italian_drill"))

from italian_drill import (
    VERBS, TENSES, generate_sentence, VERB_MAP,
    TENSE_EN, SUBJECT_EN,
)

import random
random.seed(99)

lines = []
count = 0
attempts = 0
# Force modal-heavy generation by repeating until we get 200 modal sentences
while count < 200 and attempts < 5000:
    attempts += 1
    verb_info = random.choice(VERBS)
    verb = verb_info["infinitive"]
    difficulty_unlocked = True  # Always unlocked to get modals
    gender = random.choice(["m", "f"])

    spec = generate_sentence(verb, list(TENSES), difficulty_unlocked, gender)

    # Only keep sentences that involve modals
    has_modal = (
        spec.template in ("B", "C", "E") or  # B/C always have modals, E has implied potere
        (spec.template == "F" and spec.f_modal) or
        (spec.template == "I" and spec.reflexive_modal)
    )
    if not has_modal:
        continue

    count += 1
    it = spec.build_italian()
    en = spec.build_english()
    tense = TENSE_EN.get(spec.tense, spec.tense)
    modal = spec.modal or spec.f_modal or spec.reflexive_modal or ("potere" if spec.template == "E" else "")

    lines.append(f"{count:3d}. [{spec.template}] [{tense}] [{spec.subject}] [modal={modal}]\n     IT: {it}\n     EN: {en}\n")

with open("modal_audit.txt", "w", encoding="utf-8") as f:
    f.write("MODAL AUDIT — 200 Modal Sentences\n")
    f.write("=" * 60 + "\n\n")
    for line in lines:
        f.write(line + "\n")

print(f"Generated {count} modal sentences (from {attempts} attempts) to modal_audit.txt")
