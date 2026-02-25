# Italian Sentence Production Drill

A CLI program for practicing Italian sentence production. Drills 100 high-frequency verbs across multiple tenses, subjects, discourse frames, and sentence structures.

## Prerequisites

- **Python 3.8+**
- **openssl** (pre-installed on Mac/Linux; on Windows install [Git Bash](https://gitforwindows.org/) or [WSL](https://docs.microsoft.com/en-us/windows/wsl/install))

No pip installs required — everything uses the Python standard library.

## Running the Drill

```bash
cd italian_drill
python italian_drill.py
```

On first run you'll be asked to choose:
1. **Mode**: all / non-mastered only / review mastered / custom (pick tenses)
2. **Focus**: all / pronouns / agreement / conjugation-endings
3. **Gender**: masculine or feminine forms for io/tu with essere verbs in passato prossimo

The `italian_drill_data/` folder is created automatically on first run.

## Commands

| Command  | Description |
|----------|-------------|
| `:quit`  | Exit, save timing, show session summary, run sync |
| `:stats` | Top 10 weakest verbs, top 10 mastered, weakest tenses, weakest person/tense combos, lifetime hours |
| `:hint`  | Reveal verb infinitive + required tense (logged, does not count as correct) |
| `:flag`  | Mark current sentence as unnatural/suspect, log to flagged.jsonl, skip |
| `:help`  | Show all commands |
| `:test`  | Run conjugation self-check, print sample conjugations |

## Manual Sync to Google Sheets

```bash
python sync_to_sheets.py
```

The `.env` file is loaded automatically on `:quit` — no manual `export` needed. You can also run the sync script directly with flags:

```bash
python sync_to_sheets.py --dry-run          # Preview without writing
python sync_to_sheets.py --attempts-only     # Only append new attempts
python sync_to_sheets.py --creds /path.json  # Override credentials path
python sync_to_sheets.py --sheet SHEET_ID    # Override sheet ID
```

## Google Sheet Tabs

| Tab | Contents |
|-----|----------|
| **verbs** | One row per verb: total_attempts, correct_attempts, hint_uses, mastery_count, mastered, last_seen, accuracy_pct |
| **attempts** | Append-only log of every attempt: timestamp, verb, tense, subject, frame, english_prompt, expected, user_input, correct, hint_used |
| **tense_person** | One row per tense/person combo: attempts, correct, accuracy_pct |
| **meta** | Single data row: lifetime_minutes, lifetime_hours, total_attempts, total_correct, overall_accuracy_pct, last_sync, verbs_mastered, verbs_in_progress |
| **flagged** | All sentences flagged as unnatural via `:flag` |

## Data Files

All persisted in `italian_drill_data/` (created automatically):

- `progress.json` — per-verb mastery, lifetime stats, tense/person accuracy
- `attempts.jsonl` — one JSON record per attempt
- `flagged.jsonl` — one JSON record per flagged sentence
- `.sync_cursor` — tracks how many attempts have been synced (prevents duplicates)
