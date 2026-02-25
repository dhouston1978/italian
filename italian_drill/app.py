"""
Italian Drill — Flask Web App

Imports all game logic from italian_drill.py (conjugation engine, sentence
generation, mastery tracking, normalization, persistence).  Provides a
mobile-friendly single-page interface.
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from typing import Any, Dict

from flask import (
    Flask,
    jsonify,
    render_template,
    request,
    session,
)

# ---------------------------------------------------------------------------
# Import everything we need from the CLI module
# ---------------------------------------------------------------------------
from italian_drill import (
    ESSERE_VERBS,
    TENSE_EN,
    TENSES,
    VERB_MAP,
    VERBS,
    SentenceSpec,
    answers_match,
    append_attempt,
    append_flagged,
    check_difficulty_unlocked,
    conjugate,
    ensure_data_dir,
    format_duration,
    generate_hint,
    generate_sentence,
    get_verb_progress,
    load_progress,
    normalize,
    run_sync,
    save_progress,
    select_verb,
    update_tense_person_accuracy,
    update_verb_progress,
)

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")

# Ensure data dir exists on startup
ensure_data_dir()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_or_init_session() -> Dict[str, Any]:
    """Return the current session state, initialising defaults if needed."""
    if "session_start" not in session:
        session["session_start"] = time.time()
        session["session_total"] = 0
        session["session_correct"] = 0
        session["mode"] = "all"
        session["gender_io_tu"] = "m"
        session["allowed_tenses"] = list(TENSES)
        session["focus_mode"] = "all"
        session["correction_reps"] = 0
        session["correction_expected"] = None
        session["current_spec"] = None
    return dict(session)


def _spec_to_dict(spec: SentenceSpec) -> Dict[str, Any]:
    """Serialise a SentenceSpec into a JSON-safe dict for the session."""
    return {
        "verb": spec.verb,
        "tense": spec.tense,
        "subject": spec.subject,
        "frame_it": spec.frame["it"],
        "frame_en": spec.frame["en"],
        "template": spec.template,
        "expected_it": spec.build_italian(),
        "english_prompt": spec.build_english(),
        "gender_io_tu": spec.gender_io_tu,
        "tense_label": TENSE_EN.get(spec.tense, spec.tense),
    }


def _generate_next() -> Dict[str, Any]:
    """Pick a verb, generate a sentence, return the spec dict."""
    progress = load_progress()
    mode = session.get("mode", "all")
    allowed_tenses = session.get("allowed_tenses", list(TENSES))
    gender_io_tu = session.get("gender_io_tu", "m")
    focus_mode = session.get("focus_mode", "all")
    difficulty_unlocked = check_difficulty_unlocked(progress)

    verb = select_verb(progress, mode, allowed_tenses)
    spec = generate_sentence(
        verb, allowed_tenses, difficulty_unlocked, gender_io_tu, focus_mode
    )
    spec_dict = _spec_to_dict(spec)

    # Include verb-level stats
    vp = get_verb_progress(progress, verb)
    spec_dict["verb_acc"] = (
        f"{vp['correct_attempts']}/{vp['total_attempts']}"
        if vp["total_attempts"] > 0
        else "new"
    )

    return spec_dict


def _session_stats() -> Dict[str, Any]:
    """Current session stats for the top bar."""
    elapsed = (time.time() - session.get("session_start", time.time())) / 60
    total = session.get("session_total", 0)
    correct = session.get("session_correct", 0)
    return {
        "total": total,
        "correct": correct,
        "accuracy": round(correct / total * 100) if total > 0 else 0,
        "elapsed": format_duration(elapsed),
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.route("/")
def index():
    """Main drill page."""
    _load_or_init_session()
    return render_template("index.html")


@app.route("/settings", methods=["POST"])
def settings():
    """Save startup settings and generate the first sentence."""
    data = request.get_json(force=True)
    session["mode"] = data.get("mode", "all")
    session["gender_io_tu"] = data.get("gender_io_tu", "m")
    session["focus_mode"] = data.get("focus_mode", "all")

    tenses = data.get("allowed_tenses")
    if tenses and isinstance(tenses, list) and len(tenses) > 0:
        session["allowed_tenses"] = tenses
    else:
        session["allowed_tenses"] = list(TENSES)

    session["session_start"] = time.time()
    session["session_total"] = 0
    session["session_correct"] = 0
    session["correction_reps"] = 0
    session["correction_expected"] = None

    spec = _generate_next()
    session["current_spec"] = spec
    return jsonify({"spec": spec, "stats": _session_stats()})


@app.route("/next", methods=["POST"])
def next_sentence():
    """Generate and return the next sentence."""
    _load_or_init_session()
    session["correction_reps"] = 0
    session["correction_expected"] = None

    spec = _generate_next()
    session["current_spec"] = spec
    return jsonify({"spec": spec, "stats": _session_stats()})


@app.route("/answer", methods=["POST"])
def answer():
    """Submit an answer.  Returns correctness, hint, and correction state."""
    _load_or_init_session()
    data = request.get_json(force=True)
    user_input = data.get("answer", "").strip()
    hint_used = data.get("hint_used", False)

    # --- Correction loop mode ---
    if session.get("correction_expected"):
        expected = session["correction_expected"]
        if answers_match(user_input, expected):
            session["correction_reps"] = session.get("correction_reps", 0) + 1
            reps = session["correction_reps"]
            if reps >= 3:
                session["correction_reps"] = 0
                session["correction_expected"] = None
                return jsonify({
                    "correction": True,
                    "correction_done": True,
                    "reps": reps,
                    "stats": _session_stats(),
                })
            return jsonify({
                "correction": True,
                "correction_done": False,
                "reps": reps,
                "stats": _session_stats(),
            })
        else:
            return jsonify({
                "correction": True,
                "correction_done": False,
                "reps": session.get("correction_reps", 0),
                "correct": False,
                "expected_normalized": normalize(expected),
                "stats": _session_stats(),
            })

    # --- Normal answer evaluation ---
    spec_dict = session.get("current_spec")
    if not spec_dict:
        return jsonify({"error": "No active sentence. Call /next first."}), 400

    expected_it = spec_dict["expected_it"]
    correct = answers_match(user_input, expected_it)

    session["session_total"] = session.get("session_total", 0) + 1
    if correct:
        session["session_correct"] = session.get("session_correct", 0) + 1

    # Persist
    progress = load_progress()
    verb = spec_dict["verb"]

    if correct and not hint_used:
        update_verb_progress(progress, verb, True, False)
    elif correct and hint_used:
        update_verb_progress(progress, verb, False, True)
    else:
        update_verb_progress(progress, verb, False, hint_used)

    update_tense_person_accuracy(
        progress, spec_dict["tense"], spec_dict["subject"], correct
    )
    save_progress(progress)

    append_attempt({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "verb": verb,
        "tense": spec_dict["tense"],
        "subject": spec_dict["subject"],
        "frame": spec_dict["frame_it"],
        "english_prompt": spec_dict["english_prompt"],
        "expected": expected_it,
        "user_input": user_input,
        "correct": correct,
        "hint_used": hint_used,
    })

    result: Dict[str, Any] = {
        "correct": correct,
        "user_normalized": normalize(user_input),
        "expected_normalized": normalize(expected_it),
        "stats": _session_stats(),
    }

    if not correct:
        # Build hint
        # Reconstruct a minimal SentenceSpec for generate_hint
        hint_msg = _generate_hint_from_dict(user_input, expected_it, spec_dict)
        result["hint"] = hint_msg
        # Enter correction mode
        session["correction_reps"] = 0
        session["correction_expected"] = expected_it

    return jsonify(result)


def _generate_hint_from_dict(
    user_input: str, expected: str, spec_dict: Dict[str, Any]
) -> str:
    """Generate hint from a serialised spec dict."""
    verb = spec_dict["verb"]
    tense = spec_dict["tense"]
    subject = spec_dict["subject"]
    gender = spec_dict.get("gender_io_tu", "m")

    verb_form_expected = conjugate(verb, tense, subject, gender)
    norm_input = normalize(user_input)

    frame_it = spec_dict.get("frame_it", "")
    if frame_it and frame_it.lower().rstrip(",") not in norm_input:
        return "missing discourse frame"

    if verb_form_expected.lower() not in norm_input:
        from italian_drill import SUBJECTS as _SUBJECTS

        for t in TENSES:
            for s in _SUBJECTS:
                try:
                    form = conjugate(verb, t, s, gender)
                    if form.lower() in norm_input:
                        if t != tense and s != subject:
                            return f"wrong tense and wrong person (expected {TENSE_EN[tense]}, {subject})"
                        elif t != tense:
                            return f"wrong tense (expected {TENSE_EN[tense]})"
                        elif s != subject:
                            return f"wrong person (expected {subject})"
                except Exception:
                    pass

        if tense == "passato_prossimo":
            uses_essere = verb in ESSERE_VERBS or verb == "essere"
            if uses_essere and "ha " in norm_input:
                return "wrong auxiliary (use essere, not avere)"
            if not uses_essere and ("è " in norm_input or "sono " in norm_input):
                return "wrong auxiliary (use avere, not essere)"

        return "wrong verb conjugation"

    return "check spelling and word order"


@app.route("/hint", methods=["POST"])
def hint():
    """Log a hint use and return hint text."""
    _load_or_init_session()
    spec_dict = session.get("current_spec")
    if not spec_dict:
        return jsonify({"error": "No active sentence."}), 400

    verb = spec_dict["verb"]
    tense = spec_dict["tense"]

    # Log hint use in progress
    progress = load_progress()
    vp = get_verb_progress(progress, verb)
    vp["hint_uses"] = vp.get("hint_uses", 0) + 1
    save_progress(progress)

    hint_text = f"{verb} ({VERB_MAP[verb]['en']}) — {spec_dict['tense_label']}"
    if tense == "passato_prossimo":
        aux = "essere" if (verb in ESSERE_VERBS or verb == "essere") else "avere"
        hint_text += f" | Auxiliary: {aux}"

    return jsonify({"hint": hint_text})


@app.route("/flag", methods=["POST"])
def flag():
    """Flag the current sentence and skip to next."""
    _load_or_init_session()
    spec_dict = session.get("current_spec")
    if not spec_dict:
        return jsonify({"error": "No active sentence."}), 400

    append_flagged({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "verb": spec_dict["verb"],
        "tense": spec_dict["tense"],
        "subject": spec_dict["subject"],
        "frame": spec_dict["frame_it"],
        "english_prompt": spec_dict["english_prompt"],
        "expected": spec_dict["expected_it"],
    })

    # Generate next
    session["correction_reps"] = 0
    session["correction_expected"] = None
    spec = _generate_next()
    session["current_spec"] = spec

    return jsonify({"flagged": True, "spec": spec, "stats": _session_stats()})


@app.route("/stats")
def stats():
    """Return detailed statistics as JSON."""
    _load_or_init_session()
    progress = load_progress()
    elapsed = (time.time() - session.get("session_start", time.time())) / 60
    lifetime = progress.get("lifetime_minutes", 0.0) + elapsed

    # Verb stats
    verb_stats = []
    for v in VERBS:
        vp = progress.get("verbs", {}).get(v["infinitive"], {})
        total = vp.get("total_attempts", 0)
        correct_count = vp.get("correct_attempts", 0)
        mastered = vp.get("mastered", False)
        acc = round(correct_count / total * 100, 1) if total > 0 else None
        verb_stats.append({
            "verb": v["infinitive"],
            "en": v["en"],
            "accuracy": acc,
            "total": total,
            "mastered": mastered,
            "mastery_count": vp.get("mastery_count", 0),
        })

    attempted = [v for v in verb_stats if v["total"] > 0]
    weakest = sorted(attempted, key=lambda x: (x["accuracy"] or 100, -x["total"]))[:10]
    mastered_list = sorted(
        [v for v in verb_stats if v["mastered"]], key=lambda x: -x["total"]
    )[:10]

    # Tense accuracy
    ta = progress.get("tense_accuracy", {})
    tense_stats = []
    for t in TENSES:
        if t in ta:
            a = ta[t]["attempts"]
            c = ta[t]["correct"]
            tense_stats.append({
                "tense": TENSE_EN.get(t, t),
                "accuracy": round(c / a * 100, 1) if a > 0 else 0,
                "attempts": a,
            })

    # Person/tense combos
    tpa = progress.get("tense_person_accuracy", {})
    combo_stats = []
    for key, data in sorted(tpa.items()):
        a = data["attempts"]
        c = data["correct"]
        if a > 0:
            combo_stats.append({
                "combo": key,
                "accuracy": round(c / a * 100, 1),
                "attempts": a,
            })
    combo_stats.sort(key=lambda x: (x["accuracy"], -x["attempts"]))

    return jsonify({
        "lifetime": format_duration(lifetime),
        "session": format_duration(elapsed),
        "weakest": weakest,
        "mastered": mastered_list,
        "tense_stats": tense_stats,
        "combo_stats": combo_stats[:10],
        "session_stats": _session_stats(),
    })


@app.route("/quit", methods=["POST"])
def quit_session():
    """Save session timing, trigger sync, return summary."""
    _load_or_init_session()
    session_minutes = (time.time() - session.get("session_start", time.time())) / 60
    total = session.get("session_total", 0)
    correct = session.get("session_correct", 0)

    progress = load_progress()
    progress["lifetime_minutes"] = progress.get("lifetime_minutes", 0.0) + session_minutes
    save_progress(progress)

    # Sync if creds available
    sync_msg = ""
    if os.environ.get("GOOGLE_CREDS_PATH") and os.environ.get("ITALIAN_SHEET_ID"):
        try:
            run_sync()
            sync_msg = "Synced to Google Sheets."
        except Exception as e:
            sync_msg = f"Sync warning: {e}"

    # Reset session
    session.clear()

    return jsonify({
        "total": total,
        "correct": correct,
        "accuracy": round(correct / total * 100, 1) if total > 0 else 0,
        "session_time": format_duration(session_minutes),
        "lifetime": format_duration(progress["lifetime_minutes"]),
        "sync": sync_msg,
    })


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
