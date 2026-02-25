#!/usr/bin/env python3
"""
Sync italian_drill_data/ to a Google Sheet.

Uses only the Python standard library — no pip installs required.
Signs a JWT via subprocess + openssl for service-account auth.

Usage:
    python sync_to_sheets.py
    python sync_to_sheets.py --dry-run
    python sync_to_sheets.py --attempts-only
    python sync_to_sheets.py --creds /path/to/creds.json --sheet SHEET_ID
"""

from __future__ import annotations

import argparse
import base64
import json
import math
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR / "italian_drill_data"
PROGRESS_FILE = DATA_DIR / "progress.json"
ATTEMPTS_FILE = DATA_DIR / "attempts.jsonl"
FLAGGED_FILE = DATA_DIR / "flagged.jsonl"
SYNC_CURSOR_FILE = DATA_DIR / ".sync_cursor"

SCOPES = "https://www.googleapis.com/auth/spreadsheets"
TOKEN_URL = "https://oauth2.googleapis.com/token"
SHEETS_API = "https://sheets.googleapis.com/v4/spreadsheets"

# ---------------------------------------------------------------------------
# JWT / Auth
# ---------------------------------------------------------------------------


def _b64url(data: bytes) -> str:
    """Base64url-encode without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _build_jwt(service_account: Dict[str, Any]) -> str:
    """Build a signed JWT for Google service account auth.

    Uses subprocess + openssl to do the RS256 signing.
    """
    now = int(time.time())
    header = {"alg": "RS256", "typ": "JWT"}
    payload = {
        "iss": service_account["client_email"],
        "scope": SCOPES,
        "aud": TOKEN_URL,
        "iat": now,
        "exp": now + 3600,
    }

    segments = _b64url(json.dumps(header).encode()) + "." + _b64url(json.dumps(payload).encode())

    # Write private key to a temp file for openssl
    with tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=False) as kf:
        kf.write(service_account["private_key"])
        key_path = kf.name

    try:
        result = subprocess.run(
            [
                "openssl", "dgst", "-sha256", "-sign", key_path,
            ],
            input=segments.encode(),
            capture_output=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"openssl signing failed: {result.stderr.decode()}")
        signature = result.stdout
    finally:
        os.unlink(key_path)

    return segments + "." + _b64url(signature)


def get_access_token(creds_path: str) -> str:
    """Exchange a service-account JWT for a bearer token."""
    with open(creds_path, "r", encoding="utf-8") as f:
        sa = json.load(f)

    jwt = _build_jwt(sa)

    body = urllib.parse.urlencode({
        "grant_type": "urn:ietf:params:oauth:grant_type:jwt-bearer",
        "assertion": jwt,
    }).encode()

    req = urllib.request.Request(TOKEN_URL, data=body, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())

    return data["access_token"]


# ---------------------------------------------------------------------------
# Sheets API helpers
# ---------------------------------------------------------------------------


def _sheets_request(
    method: str,
    url: str,
    token: str,
    body: Optional[Dict[str, Any]] = None,
) -> Any:
    """Make an authenticated request to the Sheets API."""
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode() if e.fp else ""
        raise RuntimeError(f"Sheets API {method} {url} → {e.code}: {err_body}") from e


def get_sheet_metadata(token: str, sheet_id: str) -> Dict[str, Any]:
    """Get spreadsheet metadata (list of tabs)."""
    url = f"{SHEETS_API}/{sheet_id}?fields=sheets.properties"
    return _sheets_request("GET", url, token)


def ensure_tabs(token: str, sheet_id: str, tab_names: List[str]) -> None:
    """Create tabs if they don't already exist."""
    meta = get_sheet_metadata(token, sheet_id)
    existing = set()
    for s in meta.get("sheets", []):
        existing.add(s["properties"]["title"])

    requests = []
    for name in tab_names:
        if name not in existing:
            requests.append({
                "addSheet": {
                    "properties": {"title": name}
                }
            })

    if requests:
        url = f"{SHEETS_API}/{sheet_id}:batchUpdate"
        _sheets_request("POST", url, token, {"requests": requests})
        print(f"  Created tabs: {[r['addSheet']['properties']['title'] for r in requests]}")


def clear_tab(token: str, sheet_id: str, tab_name: str) -> None:
    """Clear all data in a tab."""
    url = f"{SHEETS_API}/{sheet_id}/values/{urllib.parse.quote(tab_name)}!A:ZZ?fields="
    try:
        _sheets_request("DELETE", url, token)
    except RuntimeError:
        # If tab is already empty, clear may 404 — ignore
        pass


def write_tab(
    token: str,
    sheet_id: str,
    tab_name: str,
    rows: List[List[Any]],
    dry_run: bool = False,
) -> None:
    """Overwrite a tab with the given rows (including header)."""
    if dry_run:
        print(f"  [DRY RUN] Would write {len(rows)} rows to '{tab_name}'")
        if rows:
            print(f"    Header: {rows[0]}")
            if len(rows) > 1:
                print(f"    First data row: {rows[1]}")
        return

    range_str = f"{tab_name}!A1"
    url = (
        f"{SHEETS_API}/{sheet_id}/values/{urllib.parse.quote(range_str)}"
        f"?valueInputOption=USER_ENTERED"
    )
    body = {"values": rows}
    _sheets_request("PUT", url, token, body)
    print(f"  Wrote {len(rows)} rows to '{tab_name}'")


def append_tab(
    token: str,
    sheet_id: str,
    tab_name: str,
    rows: List[List[Any]],
    dry_run: bool = False,
) -> None:
    """Append rows to a tab."""
    if not rows:
        print(f"  No new rows to append to '{tab_name}'")
        return
    if dry_run:
        print(f"  [DRY RUN] Would append {len(rows)} rows to '{tab_name}'")
        if rows:
            print(f"    First row: {rows[0]}")
        return

    range_str = f"{tab_name}!A1"
    url = (
        f"{SHEETS_API}/{sheet_id}/values/{urllib.parse.quote(range_str)}:append"
        f"?valueInputOption=USER_ENTERED&insertDataOption=INSERT_ROWS"
    )
    body = {"values": rows}
    _sheets_request("POST", url, token, body)
    print(f"  Appended {len(rows)} rows to '{tab_name}'")


# ---------------------------------------------------------------------------
# Data builders
# ---------------------------------------------------------------------------


def load_progress() -> Dict[str, Any]:
    """Load progress.json."""
    if not PROGRESS_FILE.exists():
        return {}
    with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    """Load a JSONL file."""
    if not path.exists():
        return []
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def build_verbs_rows(progress: Dict[str, Any]) -> List[List[Any]]:
    """Build rows for the verbs tab."""
    header = [
        "verb", "total_attempts", "correct_attempts", "hint_uses",
        "mastery_count", "mastered", "last_seen", "accuracy_pct",
    ]
    rows = [header]
    for verb, data in sorted(progress.get("verbs", {}).items()):
        total = data.get("total_attempts", 0)
        correct = data.get("correct_attempts", 0)
        acc = round(correct / total * 100, 1) if total > 0 else 0.0
        rows.append([
            verb,
            total,
            correct,
            data.get("hint_uses", 0),
            data.get("mastery_count", 0),
            str(data.get("mastered", False)),
            data.get("last_seen", ""),
            acc,
        ])
    return rows


def build_tense_person_rows(progress: Dict[str, Any]) -> List[List[Any]]:
    """Build rows for the tense_person tab."""
    header = ["tense_person", "attempts", "correct", "accuracy_pct"]
    rows = [header]

    # Combine tense_accuracy and tense_person_accuracy
    tpa = progress.get("tense_person_accuracy", {})
    for key in sorted(tpa.keys()):
        data = tpa[key]
        a = data.get("attempts", 0)
        c = data.get("correct", 0)
        acc = round(c / a * 100, 1) if a > 0 else 0.0
        rows.append([key, a, c, acc])

    return rows


def build_meta_rows(progress: Dict[str, Any]) -> List[List[Any]]:
    """Build rows for the meta tab."""
    lifetime_min = progress.get("lifetime_minutes", 0.0)
    total_attempts = 0
    total_correct = 0
    mastered_count = 0
    in_progress_count = 0

    for data in progress.get("verbs", {}).values():
        total_attempts += data.get("total_attempts", 0)
        total_correct += data.get("correct_attempts", 0)
        if data.get("mastered", False):
            mastered_count += 1
        elif data.get("total_attempts", 0) > 0:
            in_progress_count += 1

    overall_acc = round(total_correct / total_attempts * 100, 1) if total_attempts > 0 else 0.0

    header = [
        "lifetime_minutes", "lifetime_hours", "total_attempts", "total_correct",
        "overall_accuracy_pct", "last_sync", "verbs_mastered", "verbs_in_progress",
    ]
    data_row = [
        round(lifetime_min, 1),
        round(lifetime_min / 60, 2),
        total_attempts,
        total_correct,
        overall_acc,
        datetime.now(timezone.utc).isoformat(),
        mastered_count,
        in_progress_count,
    ]
    return [header, data_row]


def build_flagged_rows(flagged: List[Dict[str, Any]]) -> List[List[Any]]:
    """Build rows for the flagged tab."""
    header = ["timestamp", "verb", "tense", "subject", "frame", "english_prompt", "expected"]
    rows = [header]
    for rec in flagged:
        rows.append([
            rec.get("timestamp", ""),
            rec.get("verb", ""),
            rec.get("tense", ""),
            rec.get("subject", ""),
            rec.get("frame", ""),
            rec.get("english_prompt", ""),
            rec.get("expected", ""),
        ])
    return rows


def build_attempts_rows(
    attempts: List[Dict[str, Any]], start_idx: int
) -> List[List[Any]]:
    """Build rows for new attempts (after cursor)."""
    header = [
        "timestamp", "verb", "tense", "subject", "frame",
        "english_prompt", "expected", "user_input", "correct", "hint_used",
    ]
    rows = []
    for rec in attempts[start_idx:]:
        rows.append([
            rec.get("timestamp", ""),
            rec.get("verb", ""),
            rec.get("tense", ""),
            rec.get("subject", ""),
            rec.get("frame", ""),
            rec.get("english_prompt", ""),
            rec.get("expected", ""),
            rec.get("user_input", ""),
            str(rec.get("correct", False)),
            str(rec.get("hint_used", False)),
        ])
    return header, rows


def load_sync_cursor() -> int:
    """Load the sync cursor (number of attempts already synced)."""
    if SYNC_CURSOR_FILE.exists():
        try:
            return int(SYNC_CURSOR_FILE.read_text().strip())
        except (ValueError, OSError):
            return 0
    return 0


def save_sync_cursor(value: int, dry_run: bool = False) -> None:
    """Save the sync cursor."""
    if dry_run:
        print(f"  [DRY RUN] Would save sync cursor: {value}")
        return
    SYNC_CURSOR_FILE.write_text(str(value))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync italian_drill_data to Google Sheets")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be written without writing")
    parser.add_argument("--attempts-only", action="store_true", help="Only append new attempts, skip snapshot tabs")
    parser.add_argument("--creds", type=str, default=None, help="Override GOOGLE_CREDS_PATH")
    parser.add_argument("--sheet", type=str, default=None, help="Override ITALIAN_SHEET_ID")
    args = parser.parse_args()

    # Resolve credentials
    creds_path = args.creds or os.environ.get("GOOGLE_CREDS_PATH", "")
    sheet_id = args.sheet or os.environ.get("ITALIAN_SHEET_ID", "")

    if not creds_path:
        print("Error: No credentials path. Set GOOGLE_CREDS_PATH or use --creds.")
        sys.exit(1)
    if not sheet_id:
        print("Error: No sheet ID. Set ITALIAN_SHEET_ID or use --sheet.")
        sys.exit(1)
    if not Path(creds_path).exists():
        print(f"Error: Credentials file not found: {creds_path}")
        sys.exit(1)

    print(f"Syncing to sheet: {sheet_id}")
    print(f"Credentials: {creds_path}")
    if args.dry_run:
        print("[DRY RUN MODE]")
    print()

    # Authenticate
    if not args.dry_run:
        print("Authenticating...")
        token = get_access_token(creds_path)
        print("  Authenticated.")
    else:
        token = "DRY_RUN_TOKEN"

    # Ensure tabs exist
    tab_names = ["verbs", "attempts", "tense_person", "meta", "flagged"]
    if not args.dry_run:
        print("Ensuring tabs exist...")
        ensure_tabs(token, sheet_id, tab_names)

    # Load local data
    progress = load_progress()
    attempts = load_jsonl(ATTEMPTS_FILE)
    flagged = load_jsonl(FLAGGED_FILE)

    cursor = load_sync_cursor()
    print(f"  Sync cursor: {cursor} (total attempts: {len(attempts)})")

    # --- Snapshot tabs ---
    if not args.attempts_only:
        print("\nWriting snapshot tabs...")

        # verbs
        verbs_rows = build_verbs_rows(progress)
        if not args.dry_run:
            clear_tab(token, sheet_id, "verbs")
        write_tab(token, sheet_id, "verbs", verbs_rows, dry_run=args.dry_run)

        # tense_person
        tp_rows = build_tense_person_rows(progress)
        if not args.dry_run:
            clear_tab(token, sheet_id, "tense_person")
        write_tab(token, sheet_id, "tense_person", tp_rows, dry_run=args.dry_run)

        # meta
        meta_rows = build_meta_rows(progress)
        if not args.dry_run:
            clear_tab(token, sheet_id, "meta")
        write_tab(token, sheet_id, "meta", meta_rows, dry_run=args.dry_run)

        # flagged
        flagged_rows = build_flagged_rows(flagged)
        if not args.dry_run:
            clear_tab(token, sheet_id, "flagged")
        write_tab(token, sheet_id, "flagged", flagged_rows, dry_run=args.dry_run)

    # --- Attempts (append only) ---
    print("\nAppending new attempts...")
    header, new_rows = build_attempts_rows(attempts, cursor)

    if cursor == 0 and new_rows:
        # First sync: write header + rows
        all_rows = [header] + new_rows
        append_tab(token, sheet_id, "attempts", all_rows, dry_run=args.dry_run)
    elif new_rows:
        append_tab(token, sheet_id, "attempts", new_rows, dry_run=args.dry_run)
    else:
        print("  No new attempts to sync.")

    # Update cursor
    new_cursor = len(attempts)
    save_sync_cursor(new_cursor, dry_run=args.dry_run)

    print(f"\nSync complete. Cursor: {cursor} → {new_cursor}")


if __name__ == "__main__":
    main()
