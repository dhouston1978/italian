#!/usr/bin/env python3
"""
Italian Sentence Production Drill — CLI Program
Helps English speakers practice producing Italian sentences.
No external dependencies — Python 3.8+ standard library only.
"""

from __future__ import annotations

import json
import os
import random
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# ---------------------------------------------------------------------------
# Constants / paths
# ---------------------------------------------------------------------------

DATA_DIR = Path(__file__).resolve().parent / "italian_drill_data"
PROGRESS_FILE = DATA_DIR / "progress.json"
ATTEMPTS_FILE = DATA_DIR / "attempts.jsonl"
FLAGGED_FILE = DATA_DIR / "flagged.jsonl"

SUBJECTS: List[str] = ["io", "tu", "lui", "lei", "noi", "voi", "loro"]

TENSES: List[str] = [
    "presente",
    "imperfetto",
    "futuro",
    "condizionale",
    "passato_prossimo",
]

DISCOURSE_FRAMES: List[Dict[str, str]] = [
    {"it": "Secondo me,", "en": "In my opinion,"},
    {"it": "Secondo lui,", "en": "According to him,"},
    {"it": "Secondo lei,", "en": "According to her,"},
    {"it": "Secondo noi,", "en": "According to us,"},
    {"it": "A mio parere,", "en": "In my view,"},
    {"it": "Per quanto mi riguarda,", "en": "As far as I'm concerned,"},
    {"it": "In realtà,", "en": "Actually,"},
    {"it": "Purtroppo,", "en": "Unfortunately,"},
    {"it": "Fortunatamente,", "en": "Fortunately,"},
    {"it": "Di solito,", "en": "Usually,"},
    {"it": "Ogni giorno,", "en": "Every day,"},
    {"it": "A volte,", "en": "Sometimes,"},
    {"it": "Probabilmente,", "en": "Probably,"},
    {"it": "Forse,", "en": "Maybe,"},
    {"it": "Sinceramente,", "en": "Honestly,"},
]

# No-frame sentinel
NO_FRAME: Dict[str, str] = {"it": "", "en": ""}

# ---------------------------------------------------------------------------
# 100 high-frequency verbs
# ---------------------------------------------------------------------------

ESSERE_VERBS: Set[str] = {
    "andare", "venire", "arrivare", "partire", "tornare",
    "uscire", "entrare", "nascere", "morire", "cadere",
    "restare", "diventare", "rimanere", "salire", "scendere",
    "stare",
}

VERBS: List[Dict[str, Any]] = [
    # --- Irregular essentials ---
    {"infinitive": "essere", "en": "to be", "conjugation": "irregular", "group": "irreg"},
    {"infinitive": "avere", "en": "to have", "conjugation": "irregular", "group": "irreg"},
    {"infinitive": "fare", "en": "to do/make", "conjugation": "irregular", "group": "irreg"},
    {"infinitive": "dire", "en": "to say/tell", "conjugation": "irregular", "group": "irreg"},
    {"infinitive": "andare", "en": "to go", "conjugation": "irregular", "group": "irreg"},
    {"infinitive": "venire", "en": "to come", "conjugation": "irregular", "group": "irreg"},
    {"infinitive": "dare", "en": "to give", "conjugation": "irregular", "group": "irreg"},
    {"infinitive": "stare", "en": "to stay/be", "conjugation": "irregular", "group": "irreg"},
    {"infinitive": "potere", "en": "to be able to/can", "conjugation": "irregular", "group": "irreg"},
    {"infinitive": "volere", "en": "to want", "conjugation": "irregular", "group": "irreg"},
    {"infinitive": "dovere", "en": "to have to/must", "conjugation": "irregular", "group": "irreg"},
    {"infinitive": "sapere", "en": "to know", "conjugation": "irregular", "group": "irreg"},
    {"infinitive": "vedere", "en": "to see", "conjugation": "irregular", "group": "irreg"},
    {"infinitive": "uscire", "en": "to go out", "conjugation": "irregular", "group": "irreg"},
    # --- Regular -are ---
    {"infinitive": "parlare", "en": "to speak/talk", "conjugation": "regular", "group": "are"},
    {"infinitive": "mangiare", "en": "to eat", "conjugation": "regular", "group": "are"},
    {"infinitive": "lavorare", "en": "to work", "conjugation": "regular", "group": "are"},
    {"infinitive": "studiare", "en": "to study", "conjugation": "regular", "group": "are"},
    {"infinitive": "comprare", "en": "to buy", "conjugation": "regular", "group": "are"},
    {"infinitive": "trovare", "en": "to find", "conjugation": "regular", "group": "are"},
    {"infinitive": "pensare", "en": "to think", "conjugation": "regular", "group": "are"},
    {"infinitive": "chiamare", "en": "to call", "conjugation": "regular", "group": "are"},
    {"infinitive": "aspettare", "en": "to wait for", "conjugation": "regular", "group": "are"},
    {"infinitive": "guardare", "en": "to watch/look at", "conjugation": "regular", "group": "are"},
    {"infinitive": "ascoltare", "en": "to listen to", "conjugation": "regular", "group": "are"},
    {"infinitive": "camminare", "en": "to walk", "conjugation": "regular", "group": "are"},
    {"infinitive": "giocare", "en": "to play", "conjugation": "regular", "group": "are"},
    {"infinitive": "cucinare", "en": "to cook", "conjugation": "regular", "group": "are"},
    {"infinitive": "cantare", "en": "to sing", "conjugation": "regular", "group": "are"},
    {"infinitive": "ballare", "en": "to dance", "conjugation": "regular", "group": "are"},
    {"infinitive": "nuotare", "en": "to swim", "conjugation": "regular", "group": "are"},
    {"infinitive": "insegnare", "en": "to teach", "conjugation": "regular", "group": "are"},
    {"infinitive": "imparare", "en": "to learn", "conjugation": "regular", "group": "are"},
    {"infinitive": "pagare", "en": "to pay", "conjugation": "regular", "group": "are"},
    {"infinitive": "cercare", "en": "to look for/search", "conjugation": "regular", "group": "are"},
    {"infinitive": "portare", "en": "to bring/carry", "conjugation": "regular", "group": "are"},
    {"infinitive": "cambiare", "en": "to change", "conjugation": "regular", "group": "are"},
    {"infinitive": "provare", "en": "to try", "conjugation": "regular", "group": "are"},
    {"infinitive": "arrivare", "en": "to arrive", "conjugation": "regular", "group": "are"},
    {"infinitive": "tornare", "en": "to return", "conjugation": "regular", "group": "are"},
    {"infinitive": "entrare", "en": "to enter", "conjugation": "regular", "group": "are"},
    {"infinitive": "restare", "en": "to stay/remain", "conjugation": "regular", "group": "are"},
    {"infinitive": "diventare", "en": "to become", "conjugation": "regular", "group": "are"},
    {"infinitive": "passare", "en": "to pass/spend (time)", "conjugation": "regular", "group": "are"},
    {"infinitive": "usare", "en": "to use", "conjugation": "regular", "group": "are"},
    {"infinitive": "amare", "en": "to love", "conjugation": "regular", "group": "are"},
    {"infinitive": "preparare", "en": "to prepare", "conjugation": "regular", "group": "are"},
    {"infinitive": "ricordare", "en": "to remember", "conjugation": "regular", "group": "are"},
    {"infinitive": "dimenticare", "en": "to forget", "conjugation": "regular", "group": "are"},
    {"infinitive": "aiutare", "en": "to help", "conjugation": "regular", "group": "are"},
    {"infinitive": "spiegare", "en": "to explain", "conjugation": "regular", "group": "are"},
    {"infinitive": "cominciare", "en": "to begin/start", "conjugation": "regular", "group": "are"},
    {"infinitive": "abitare", "en": "to live (reside)", "conjugation": "regular", "group": "are"},
    {"infinitive": "viaggiare", "en": "to travel", "conjugation": "regular", "group": "are"},
    {"infinitive": "suonare", "en": "to play (instrument)", "conjugation": "regular", "group": "are"},
    {"infinitive": "raccontare", "en": "to tell (a story)", "conjugation": "regular", "group": "are"},
    {"infinitive": "desiderare", "en": "to wish/desire", "conjugation": "regular", "group": "are"},
    {"infinitive": "visitare", "en": "to visit", "conjugation": "regular", "group": "are"},
    {"infinitive": "lasciare", "en": "to leave/let", "conjugation": "regular", "group": "are"},
    # --- Regular -ere ---
    {"infinitive": "scrivere", "en": "to write", "conjugation": "regular", "group": "ere"},
    {"infinitive": "leggere", "en": "to read", "conjugation": "regular", "group": "ere"},
    {"infinitive": "prendere", "en": "to take", "conjugation": "regular", "group": "ere"},
    {"infinitive": "vivere", "en": "to live", "conjugation": "regular", "group": "ere"},
    {"infinitive": "credere", "en": "to believe", "conjugation": "regular", "group": "ere"},
    {"infinitive": "correre", "en": "to run", "conjugation": "regular", "group": "ere"},
    {"infinitive": "mettere", "en": "to put", "conjugation": "regular", "group": "ere"},
    {"infinitive": "chiudere", "en": "to close", "conjugation": "regular", "group": "ere"},
    {"infinitive": "perdere", "en": "to lose", "conjugation": "regular", "group": "ere"},
    {"infinitive": "rispondere", "en": "to answer/reply", "conjugation": "regular", "group": "ere"},
    {"infinitive": "chiedere", "en": "to ask", "conjugation": "regular", "group": "ere"},
    {"infinitive": "conoscere", "en": "to know (a person)", "conjugation": "regular", "group": "ere"},
    {"infinitive": "ricevere", "en": "to receive", "conjugation": "regular", "group": "ere"},
    {"infinitive": "vendere", "en": "to sell", "conjugation": "regular", "group": "ere"},
    {"infinitive": "cadere", "en": "to fall", "conjugation": "regular", "group": "ere"},
    {"infinitive": "nascere", "en": "to be born", "conjugation": "regular", "group": "ere"},
    {"infinitive": "rimanere", "en": "to remain", "conjugation": "irregular", "group": "ere"},
    # --- Regular -ire ---
    {"infinitive": "dormire", "en": "to sleep", "conjugation": "regular", "group": "ire"},
    {"infinitive": "partire", "en": "to leave/depart", "conjugation": "regular", "group": "ire"},
    {"infinitive": "sentire", "en": "to hear/feel", "conjugation": "regular", "group": "ire"},
    {"infinitive": "aprire", "en": "to open", "conjugation": "regular", "group": "ire"},
    {"infinitive": "seguire", "en": "to follow", "conjugation": "regular", "group": "ire"},
    {"infinitive": "offrire", "en": "to offer", "conjugation": "regular", "group": "ire"},
    {"infinitive": "servire", "en": "to serve/need", "conjugation": "regular", "group": "ire"},
    {"infinitive": "scoprire", "en": "to discover", "conjugation": "regular", "group": "ire"},
    {"infinitive": "coprire", "en": "to cover", "conjugation": "regular", "group": "ire"},
    # --- -ire (isc) verbs ---
    {"infinitive": "capire", "en": "to understand", "conjugation": "regular", "group": "ire_isc"},
    {"infinitive": "finire", "en": "to finish", "conjugation": "regular", "group": "ire_isc"},
    {"infinitive": "preferire", "en": "to prefer", "conjugation": "regular", "group": "ire_isc"},
    {"infinitive": "spedire", "en": "to send", "conjugation": "regular", "group": "ire_isc"},
    {"infinitive": "costruire", "en": "to build", "conjugation": "regular", "group": "ire_isc"},
    {"infinitive": "pulire", "en": "to clean", "conjugation": "regular", "group": "ire_isc"},
    {"infinitive": "unire", "en": "to unite/join", "conjugation": "regular", "group": "ire_isc"},
    {"infinitive": "guarire", "en": "to heal/recover", "conjugation": "regular", "group": "ire_isc"},
    # --- More irregulars ---
    {"infinitive": "salire", "en": "to go up/climb", "conjugation": "irregular", "group": "ire"},
    {"infinitive": "scendere", "en": "to go down/descend", "conjugation": "regular", "group": "ere"},
    {"infinitive": "morire", "en": "to die", "conjugation": "irregular", "group": "ire"},
    {"infinitive": "bere", "en": "to drink", "conjugation": "irregular", "group": "ere"},
    {"infinitive": "tenere", "en": "to hold/keep", "conjugation": "irregular", "group": "ere"},
    {"infinitive": "scegliere", "en": "to choose", "conjugation": "irregular", "group": "ere"},
    {"infinitive": "correggere", "en": "to correct", "conjugation": "regular", "group": "ere"},
    {"infinitive": "spegnere", "en": "to turn off", "conjugation": "irregular", "group": "ere"},
    {"infinitive": "proporre", "en": "to propose", "conjugation": "irregular", "group": "ere"},
]

# Build a quick lookup
VERB_MAP: Dict[str, Dict[str, Any]] = {v["infinitive"]: v for v in VERBS}

# ---------------------------------------------------------------------------
# Objects and adverbials for sentence variety
# ---------------------------------------------------------------------------

OBJECTS: List[Dict[str, str]] = [
    {"it": "il libro", "en": "the book"},
    {"it": "la pizza", "en": "the pizza"},
    {"it": "il caffè", "en": "the coffee"},
    {"it": "la macchina", "en": "the car"},
    {"it": "il telefono", "en": "the phone"},
    {"it": "la musica", "en": "the music"},
    {"it": "il giornale", "en": "the newspaper"},
    {"it": "la lettera", "en": "the letter"},
    {"it": "il film", "en": "the film"},
    {"it": "la cena", "en": "the dinner"},
    {"it": "il lavoro", "en": "the work"},
    {"it": "la porta", "en": "the door"},
    {"it": "il problema", "en": "the problem"},
    {"it": "la risposta", "en": "the answer"},
    {"it": "il treno", "en": "the train"},
    {"it": "la casa", "en": "the house"},
    {"it": "l'acqua", "en": "the water"},
    {"it": "il pane", "en": "the bread"},
    {"it": "la verità", "en": "the truth"},
    {"it": "il tempo", "en": "the time"},
]

ADVERBIALS: List[Dict[str, str]] = [
    {"it": "domani", "en": "tomorrow"},
    {"it": "ieri", "en": "yesterday"},
    {"it": "oggi", "en": "today"},
    {"it": "sempre", "en": "always"},
    {"it": "spesso", "en": "often"},
    {"it": "bene", "en": "well"},
    {"it": "male", "en": "badly"},
    {"it": "subito", "en": "right away"},
    {"it": "insieme", "en": "together"},
    {"it": "qui", "en": "here"},
    {"it": "lì", "en": "there"},
    {"it": "molto", "en": "a lot"},
    {"it": "poco", "en": "a little"},
    {"it": "tardi", "en": "late"},
    {"it": "presto", "en": "early/soon"},
]

# ---------------------------------------------------------------------------
# Pronouns for template F
# ---------------------------------------------------------------------------

# Direct object pronouns
DIRECT_PRONOUNS: List[Dict[str, str]] = [
    {"it": "lo", "en": "it (m)", "gender": "m", "number": "s"},
    {"it": "la", "en": "it (f)", "gender": "f", "number": "s"},
    {"it": "li", "en": "them (m)", "gender": "m", "number": "p"},
    {"it": "le", "en": "them (f)", "gender": "f", "number": "p"},
]

# Indirect object pronouns
INDIRECT_PRONOUNS: List[Dict[str, str]] = [
    {"it": "mi", "en": "to me"},
    {"it": "ti", "en": "to you"},
    {"it": "gli", "en": "to him"},
    {"it": "le", "en": "to her"},
    {"it": "ci", "en": "to us"},
    {"it": "vi", "en": "to you all"},
    {"it": "gli", "en": "to them"},
]

# Combined pronoun lookup: (indirect, direct) → combined form
COMBINED_PRONOUNS: Dict[Tuple[str, str], str] = {
    # mi + lo/la/li/le → me lo, me la, me li, me le
    ("mi", "lo"): "me lo", ("mi", "la"): "me la",
    ("mi", "li"): "me li", ("mi", "le"): "me le",
    # ti + lo/la/li/le → te lo, te la, te li, te le
    ("ti", "lo"): "te lo", ("ti", "la"): "te la",
    ("ti", "li"): "te li", ("ti", "le"): "te le",
    # gli/le + lo/la/li/le → glielo, gliela, glieli, gliele
    ("gli", "lo"): "glielo", ("gli", "la"): "gliela",
    ("gli", "li"): "glieli", ("gli", "le"): "gliele",
    ("le_ind", "lo"): "glielo", ("le_ind", "la"): "gliela",
    ("le_ind", "li"): "glieli", ("le_ind", "le"): "gliele",
    # ci + lo/la/li/le → ce lo, ce la, ce li, ce le
    ("ci", "lo"): "ce lo", ("ci", "la"): "ce la",
    ("ci", "li"): "ce li", ("ci", "le"): "ce le",
    # vi + lo/la/li/le → ve lo, ve la, ve li, ve le
    ("vi", "lo"): "ve lo", ("vi", "la"): "ve la",
    ("vi", "li"): "ve li", ("vi", "le"): "ve le",
}

# For template F: verbs that work well with pronoun drills
PRONOUN_VERBS: List[str] = [
    "dare", "dire", "portare", "spiegare", "raccontare", "comprare",
    "preparare", "mandare", "scrivere", "leggere", "prendere",
    "mettere", "offrire", "lasciare", "insegnare", "vendere",
]

# ---------------------------------------------------------------------------
# Adjectives for template G (agreement drills)
# ---------------------------------------------------------------------------

# Adjectives with four forms: ms, fs, mp, fp
ADJECTIVES: List[Dict[str, str]] = [
    {"ms": "stanco", "fs": "stanca", "mp": "stanchi", "fp": "stanche", "en": "tired"},
    {"ms": "contento", "fs": "contenta", "mp": "contenti", "fp": "contente", "en": "happy"},
    {"ms": "arrabbiato", "fs": "arrabbiata", "mp": "arrabbiati", "fp": "arrabbiate", "en": "angry"},
    {"ms": "preoccupato", "fs": "preoccupata", "mp": "preoccupati", "fp": "preoccupate", "en": "worried"},
    {"ms": "preparato", "fs": "preparata", "mp": "preparati", "fp": "preparate", "en": "prepared"},
    {"ms": "solo", "fs": "sola", "mp": "soli", "fp": "sole", "en": "alone"},
    {"ms": "pronto", "fs": "pronta", "mp": "pronti", "fp": "pronte", "en": "ready"},
    {"ms": "felice", "fs": "felice", "mp": "felici", "fp": "felici", "en": "glad"},
    {"ms": "triste", "fs": "triste", "mp": "tristi", "fp": "tristi", "en": "sad"},
    {"ms": "nervoso", "fs": "nervosa", "mp": "nervosi", "fp": "nervose", "en": "nervous"},
    {"ms": "malato", "fs": "malata", "mp": "malati", "fp": "malate", "en": "sick"},
    {"ms": "sicuro", "fs": "sicura", "mp": "sicuri", "fp": "sicure", "en": "sure"},
]

# Gendered subjects for template G (noun phrases with explicit gender/number)
GENDERED_SUBJECTS: List[Dict[str, Any]] = [
    {"it": "il ragazzo", "en": "the boy", "gender": "m", "number": "s", "verb_subject": "lui"},
    {"it": "la ragazza", "en": "the girl", "gender": "f", "number": "s", "verb_subject": "lei"},
    {"it": "i ragazzi", "en": "the boys", "gender": "m", "number": "p", "verb_subject": "loro"},
    {"it": "le ragazze", "en": "the girls", "gender": "f", "number": "p", "verb_subject": "loro"},
    {"it": "l'uomo", "en": "the man", "gender": "m", "number": "s", "verb_subject": "lui"},
    {"it": "la donna", "en": "the woman", "gender": "f", "number": "s", "verb_subject": "lei"},
    {"it": "gli uomini", "en": "the men", "gender": "m", "number": "p", "verb_subject": "loro"},
    {"it": "le donne", "en": "the women", "gender": "f", "number": "p", "verb_subject": "loro"},
    {"it": "il bambino", "en": "the child (m)", "gender": "m", "number": "s", "verb_subject": "lui"},
    {"it": "la bambina", "en": "the child (f)", "gender": "f", "number": "s", "verb_subject": "lei"},
    {"it": "i bambini", "en": "the children (m)", "gender": "m", "number": "p", "verb_subject": "loro"},
    {"it": "le bambine", "en": "the children (f)", "gender": "f", "number": "p", "verb_subject": "loro"},
]

# Essere verbs that work well for agreement drills
AGREEMENT_VERBS: List[str] = [
    "arrivare", "partire", "tornare", "uscire", "entrare",
    "restare", "andare", "venire", "cadere", "diventare",
]

# ---------------------------------------------------------------------------
# Focus modes
# ---------------------------------------------------------------------------

FOCUS_MODES: List[str] = ["all", "pronouns", "agreement", "conjugation-endings"]

# ---------------------------------------------------------------------------
# English subject mapping
# ---------------------------------------------------------------------------

SUBJECT_EN: Dict[str, str] = {
    "io": "I",
    "tu": "you",
    "lui": "he",
    "lei": "she",
    "noi": "we",
    "voi": "you all",
    "loro": "they",
}

SUBJECT_INDEX: Dict[str, int] = {
    "io": 0, "tu": 1, "lui": 2, "lei": 3, "noi": 4, "voi": 5, "loro": 6,
}

# ---------------------------------------------------------------------------
# Tense names in English
# ---------------------------------------------------------------------------

TENSE_EN: Dict[str, str] = {
    "presente": "present",
    "imperfetto": "imperfect",
    "futuro": "future",
    "condizionale": "conditional",
    "passato_prossimo": "passato prossimo",
}

# ---------------------------------------------------------------------------
# Conjugation engine
# ---------------------------------------------------------------------------

# Irregular present tense forms: verb → [io, tu, lui/lei, noi, voi, loro]
IRREGULAR_PRESENTE: Dict[str, List[str]] = {
    "essere": ["sono", "sei", "è", "siamo", "siete", "sono"],
    "avere": ["ho", "hai", "ha", "abbiamo", "avete", "hanno"],
    "fare": ["faccio", "fai", "fa", "facciamo", "fate", "fanno"],
    "dire": ["dico", "dici", "dice", "diciamo", "dite", "dicono"],
    "andare": ["vado", "vai", "va", "andiamo", "andate", "vanno"],
    "venire": ["vengo", "vieni", "viene", "veniamo", "venite", "vengono"],
    "dare": ["do", "dai", "dà", "diamo", "date", "danno"],
    "stare": ["sto", "stai", "sta", "stiamo", "state", "stanno"],
    "potere": ["posso", "puoi", "può", "possiamo", "potete", "possono"],
    "volere": ["voglio", "vuoi", "vuole", "vogliamo", "volete", "vogliono"],
    "dovere": ["devo", "devi", "deve", "dobbiamo", "dovete", "devono"],
    "sapere": ["so", "sai", "sa", "sappiamo", "sapete", "sanno"],
    "uscire": ["esco", "esci", "esce", "usciamo", "uscite", "escono"],
    "rimanere": ["rimango", "rimani", "rimane", "rimaniamo", "rimanete", "rimangono"],
    "salire": ["salgo", "sali", "sale", "saliamo", "salite", "salgono"],
    "morire": ["muoio", "muori", "muore", "moriamo", "morite", "muoiono"],
    "bere": ["bevo", "bevi", "beve", "beviamo", "bevete", "bevono"],
    "tenere": ["tengo", "tieni", "tiene", "teniamo", "tenete", "tengono"],
    "scegliere": ["scelgo", "scegli", "sceglie", "scegliamo", "scegliete", "scelgono"],
    "spegnere": ["spengo", "spegni", "spegne", "spegniamo", "spegnete", "spengono"],
    "proporre": ["propongo", "proponi", "propone", "proponiamo", "proponete", "propongono"],
    "vedere": ["vedo", "vedi", "vede", "vediamo", "vedete", "vedono"],
}

IRREGULAR_IMPERFETTO: Dict[str, List[str]] = {
    "essere": ["ero", "eri", "era", "eravamo", "eravate", "erano"],
    "fare": ["facevo", "facevi", "faceva", "facevamo", "facevate", "facevano"],
    "dire": ["dicevo", "dicevi", "diceva", "dicevamo", "dicevate", "dicevano"],
    "bere": ["bevevo", "bevevi", "beveva", "bevevamo", "bevevate", "bevevano"],
    "proporre": ["proponevo", "proponevi", "proponeva", "proponevamo", "proponevate", "proponevano"],
}

# Irregular futuro stems (stem only — endings are -ò, -ai, -à, -emo, -ete, -anno)
IRREGULAR_FUTURO_STEMS: Dict[str, str] = {
    "essere": "sar",
    "avere": "avr",
    "fare": "far",
    "dire": "dir",
    "andare": "andr",
    "venire": "verr",
    "dare": "dar",
    "stare": "star",
    "potere": "potr",
    "volere": "vorr",
    "dovere": "dovr",
    "sapere": "sapr",
    "vedere": "vedr",
    "rimanere": "rimarr",
    "bere": "berr",
    "tenere": "terr",
    "morire": "morr",
    "proporre": "proporr",
}

# Condizionale uses same irregular stems, different endings
IRREGULAR_CONDIZIONALE_STEMS: Dict[str, str] = IRREGULAR_FUTURO_STEMS

# Irregular past participles
IRREGULAR_PAST_PARTICIPLES: Dict[str, str] = {
    "essere": "stato",
    "avere": "avuto",
    "fare": "fatto",
    "dire": "detto",
    "andare": "andato",
    "dare": "dato",
    "stare": "stato",
    "uscire": "uscito",
    "salire": "salito",
    "vedere": "visto",
    "scrivere": "scritto",
    "leggere": "letto",
    "prendere": "preso",
    "mettere": "messo",
    "chiudere": "chiuso",
    "perdere": "perso",
    "rispondere": "risposto",
    "chiedere": "chiesto",
    "correre": "corso",
    "vivere": "vissuto",
    "nascere": "nato",
    "morire": "morto",
    "rimanere": "rimasto",
    "venire": "venuto",
    "bere": "bevuto",
    "scegliere": "scelto",
    "spegnere": "spento",
    "proporre": "proposto",
    "scoprire": "scoperto",
    "aprire": "aperto",
    "offrire": "offerto",
    "coprire": "coperto",
    "correggere": "corretto",
}

FUTURO_ENDINGS: List[str] = ["ò", "ai", "à", "emo", "ete", "anno"]
CONDIZIONALE_ENDINGS: List[str] = ["ei", "esti", "ebbe", "emmo", "este", "ebbero"]


def _get_stem_and_group(verb: str) -> Tuple[str, str]:
    """Return (stem, group) for a verb infinitive."""
    info = VERB_MAP.get(verb)
    if info:
        group = info["group"]
    else:
        if verb.endswith("are"):
            group = "are"
        elif verb.endswith("ere"):
            group = "ere"
        elif verb.endswith("ire"):
            group = "ire"
        else:
            group = "ere"

    if verb.endswith("ire"):
        stem = verb[:-3]
    elif verb.endswith("re"):
        stem = verb[:-2]
    elif verb.endswith("are"):
        stem = verb[:-3]
    else:
        stem = verb[:-3] if len(verb) > 3 else verb

    # Normalize: for -are/-ere/-ire, strip last 3
    if verb.endswith("are") or verb.endswith("ere") or verb.endswith("ire"):
        stem = verb[:-3]
    elif verb.endswith("rre"):  # proporre → propor
        stem = verb[:-2]
    else:
        stem = verb[:-3]

    return stem, group


def conjugate_presente(verb: str, subject: str) -> str:
    """Conjugate verb in presente indicativo."""
    idx = SUBJECT_INDEX[subject]
    # lui/lei share index 2
    conj_idx = idx if idx <= 2 else (2 if idx == 3 else idx - 1)
    # Map: io=0, tu=1, lui=2, lei=2, noi=3(→4→3), voi=4(→5→4), loro=5(→6→5)
    # Actually our irregular tables have 6 entries: io,tu,lui/lei,noi,voi,loro
    six_idx = {0: 0, 1: 1, 2: 2, 3: 2, 4: 3, 5: 4, 6: 5}[idx]

    if verb in IRREGULAR_PRESENTE:
        return IRREGULAR_PRESENTE[verb][six_idx]

    stem, group = _get_stem_and_group(verb)

    if group == "are":
        endings = ["o", "i", "a", "iamo", "ate", "ano"]
        # Handle -care/-gare: add h before i/e
        if verb.endswith("care") or verb.endswith("gare"):
            if six_idx in (1, 3):  # tu (-i), noi (-iamo)
                return stem + "h" + endings[six_idx]
        # Handle -ciare/-giare: drop i before another i
        if verb.endswith("ciare") or verb.endswith("giare"):
            if six_idx in (1, 3):  # endings start with i
                return stem + endings[six_idx]  # stem already has ci/gi, ending adds i
                # Actually: mangiar- + i → mangi (not mangii)
                # stem = mangi, ending = i → mangii is wrong
                # Correct: mangiare → stem mangi, presente: mangio, mangi, mangia...
                # The stem is "mangi" and ending "i" → "mangii"? No — drop the duplicate i
                # mangiare: io mangio, tu mangi, lui mangia, noi mangiamo, voi mangiate, loro mangiano
                # So tu: stem "mangi" + "i" → "mangi" (drop duplicate)
                # noi: stem "mangi" + "iamo" → "mangiamo" (keep — stem i merges with iamo)
                # Actually these are correct as-is with the regular pattern because
                # mangiar- stem is "mangi" and -i → "mangi", -iamo → "mangiamo"
                # The issue was only futuro. For presente, standard works.
        return stem + endings[six_idx]

    elif group == "ere":
        endings = ["o", "i", "e", "iamo", "ete", "ono"]
        return stem + endings[six_idx]

    elif group == "ire":
        endings = ["o", "i", "e", "iamo", "ite", "ono"]
        return stem + endings[six_idx]

    elif group == "ire_isc":
        # isc- inserted in io, tu, lui/lei, loro
        if six_idx in (0, 1, 2, 5):
            endings_isc = ["isco", "isci", "isce", "", "", "iscono"]
            return stem + endings_isc[six_idx]
        else:
            endings_reg = ["", "", "", "iamo", "ite", ""]
            return stem + endings_reg[six_idx]

    return stem + "?"


def conjugate_imperfetto(verb: str, subject: str) -> str:
    """Conjugate verb in imperfetto."""
    idx = SUBJECT_INDEX[subject]
    six_idx = {0: 0, 1: 1, 2: 2, 3: 2, 4: 3, 5: 4, 6: 5}[idx]

    if verb in IRREGULAR_IMPERFETTO:
        return IRREGULAR_IMPERFETTO[verb][six_idx]

    stem, group = _get_stem_and_group(verb)

    if group in ("are",):
        endings = ["avo", "avi", "ava", "avamo", "avate", "avano"]
    elif group in ("ere",):
        endings = ["evo", "evi", "eva", "evamo", "evate", "evano"]
    elif group in ("ire", "ire_isc"):
        endings = ["ivo", "ivi", "iva", "ivamo", "ivate", "ivano"]
    else:
        endings = ["evo", "evi", "eva", "evamo", "evate", "evano"]

    return stem + endings[six_idx]


def _futuro_stem(verb: str) -> str:
    """Get the futuro/condizionale stem."""
    if verb in IRREGULAR_FUTURO_STEMS:
        return IRREGULAR_FUTURO_STEMS[verb]

    stem, group = _get_stem_and_group(verb)

    if group == "are":
        # -are → -er (parlare → parler-)
        base = verb[:-3]
        # -care/-gare → add h: cercare → cercher-, pagare → pagher-
        if verb.endswith("care") or verb.endswith("gare"):
            return base + "her"
        # -ciare/-giare → drop i: cominciare → comencer-, mangiare → manger-
        if verb.endswith("ciare"):
            return base[:-1] + "er"  # strip the i from stem
        if verb.endswith("giare"):
            return base[:-1] + "er"
        return base + "er"
    elif group in ("ere",):
        # -ere → drop e: scrivere → scriver-
        return verb[:-1]  # drop final e → scriver
        # Actually for regular -ere: vivere → viver-
        # We drop the final -e: vivere → viver
    elif group in ("ire", "ire_isc"):
        return verb[:-1]  # dormire → dormir-
    else:
        return verb[:-1]


def conjugate_futuro(verb: str, subject: str) -> str:
    """Conjugate verb in futuro semplice."""
    idx = SUBJECT_INDEX[subject]
    six_idx = {0: 0, 1: 1, 2: 2, 3: 2, 4: 3, 5: 4, 6: 5}[idx]

    stem = _futuro_stem(verb)
    # Endings with accent: ò, ai, à, emo, ete, anno
    endings = ["ò", "ai", "à", "emo", "ete", "anno"]
    return stem + endings[six_idx]


def conjugate_condizionale(verb: str, subject: str) -> str:
    """Conjugate verb in condizionale presente."""
    idx = SUBJECT_INDEX[subject]
    six_idx = {0: 0, 1: 1, 2: 2, 3: 2, 4: 3, 5: 4, 6: 5}[idx]

    stem = _futuro_stem(verb)
    endings = ["ei", "esti", "ebbe", "emmo", "este", "ebbero"]
    return stem + endings[six_idx]


def _past_participle(verb: str) -> str:
    """Get past participle (masculine singular base form)."""
    if verb in IRREGULAR_PAST_PARTICIPLES:
        return IRREGULAR_PAST_PARTICIPLES[verb]

    stem, group = _get_stem_and_group(verb)

    # For "irreg" group, infer from verb ending
    effective_group = group
    if group == "irreg":
        if verb.endswith("are"):
            effective_group = "are"
        elif verb.endswith("ire"):
            effective_group = "ire"
        else:
            effective_group = "ere"

    if effective_group == "are":
        return stem + "ato"
    elif effective_group == "ere":
        return stem + "uto"
    elif effective_group in ("ire", "ire_isc"):
        return stem + "ito"
    return stem + "uto"


def _agree_participle(participle: str, subject: str, gender_io_tu: str) -> str:
    """Agree past participle with subject for essere verbs.

    participle: base masculine singular form (e.g. 'andato')
    gender_io_tu: 'm' or 'f' for io/tu agreement
    """
    # Base form ends in -o (masc sing)
    base = participle[:-1] if participle.endswith("o") else participle[:-1]

    if subject in ("lui",):
        return participle  # masc sing, already correct
    elif subject in ("lei",):
        return base + "a"
    elif subject in ("io", "tu"):
        if gender_io_tu == "f":
            return base + "a"
        return participle  # masc sing
    elif subject in ("noi", "voi", "loro"):
        return base + "i"  # masc plural (default)

    return participle


def _agree_participle_gendered(participle: str, gender: str, number: str) -> str:
    """Agree past participle with explicit gender and number.

    Used for template G where we have noun-phrase subjects with known gender/number.
    """
    base = participle[:-1] if participle.endswith("o") else participle[:-1]

    if gender == "m" and number == "s":
        return participle  # already masc sing
    elif gender == "f" and number == "s":
        return base + "a"
    elif gender == "m" and number == "p":
        return base + "i"
    elif gender == "f" and number == "p":
        return base + "e"
    return participle


def conjugate_passato_prossimo(
    verb: str, subject: str, gender_io_tu: str = "m"
) -> str:
    """Return the full passato prossimo form (auxiliary + participle)."""
    uses_essere = verb in ESSERE_VERBS or verb == "essere"
    auxiliary = "essere" if uses_essere else "avere"
    aux_form = conjugate_presente(auxiliary, subject)
    pp = _past_participle(verb)

    if uses_essere:
        pp = _agree_participle(pp, subject, gender_io_tu)

    return f"{aux_form} {pp}"


def conjugate(
    verb: str, tense: str, subject: str, gender_io_tu: str = "m"
) -> str:
    """Master conjugation function."""
    if tense == "presente":
        return conjugate_presente(verb, subject)
    elif tense == "imperfetto":
        return conjugate_imperfetto(verb, subject)
    elif tense == "futuro":
        return conjugate_futuro(verb, subject)
    elif tense == "condizionale":
        return conjugate_condizionale(verb, subject)
    elif tense == "passato_prossimo":
        return conjugate_passato_prossimo(verb, subject, gender_io_tu)
    else:
        return f"[unknown tense: {tense}]"


# ---------------------------------------------------------------------------
# English conjugation helpers (for prompts)
# ---------------------------------------------------------------------------

def english_conjugation(
    verb_info: Dict[str, Any],
    tense: str,
    subject: str,
    obj_en: str = "",
    adv_en: str = "",
) -> str:
    """Build an approximate English translation for the prompt.

    This doesn't need to be perfect grammar — just clear enough so the user
    knows exactly what Italian sentence to produce.
    """
    en = verb_info["en"]
    # Strip "to " prefix
    bare = en.replace("to ", "") if en.startswith("to ") else en
    # Handle "to do/make" → "do/make"
    subj = SUBJECT_EN[subject]

    # Simple helper for 3rd person singular
    def s_form(v: str) -> str:
        parts = v.split("/")
        results = []
        for p in parts:
            p = p.strip()
            if p.endswith("ch") or p.endswith("sh") or p.endswith("ss") or p.endswith("x") or p.endswith("o"):
                results.append(p + "es")
            elif p.endswith("y") and len(p) > 1 and p[-2] not in "aeiou":
                results.append(p[:-1] + "ies")
            else:
                results.append(p + "s")
        return "/".join(results)

    third = subject in ("lui", "lei")
    obj_part = f" {obj_en}" if obj_en else ""
    adv_part = f" {adv_en}" if adv_en else ""

    if tense == "presente":
        if bare in ("be",):
            forms = {"io": "am", "tu": "are", "lui": "is", "lei": "is",
                     "noi": "are", "voi": "are", "loro": "are"}
            vf = forms[subject]
        elif bare in ("have",):
            vf = "has" if third else "have"
        elif bare in ("can", "be able to/can"):
            vf = "can"
        elif bare in ("have to/must",):
            vf = "must"
        else:
            vf = s_form(bare) if third else bare
        return f"{subj} {vf}{obj_part}{adv_part}"

    elif tense == "imperfetto":
        # "used to X" or "was X-ing"
        if bare in ("be",):
            was = "was" if subject in ("io", "lui", "lei") else "were"
            return f"{subj} {was}{obj_part}{adv_part}"
        return f"{subj} used to {bare}{obj_part}{adv_part}"

    elif tense == "futuro":
        return f"{subj} will {bare}{obj_part}{adv_part}"

    elif tense == "condizionale":
        return f"{subj} would {bare}{obj_part}{adv_part}"

    elif tense == "passato_prossimo":
        # Use simple past in English prompt
        if bare in ("be",):
            was = "was" if subject in ("io", "lui", "lei") else "were"
            return f"{subj} {was}{obj_part}{adv_part}"
        elif bare in ("have",):
            return f"{subj} had{obj_part}{adv_part}"
        elif bare in ("go",):
            return f"{subj} went{obj_part}{adv_part}"
        elif bare in ("come",):
            return f"{subj} came{obj_part}{adv_part}"
        elif bare in ("do/make",):
            return f"{subj} did/made{obj_part}{adv_part}"
        elif bare in ("say/tell",):
            return f"{subj} said/told{obj_part}{adv_part}"
        elif bare in ("see",):
            return f"{subj} saw{obj_part}{adv_part}"
        elif bare in ("write",):
            return f"{subj} wrote{obj_part}{adv_part}"
        elif bare in ("read",):
            return f"{subj} read{obj_part}{adv_part}"
        elif bare in ("take",):
            return f"{subj} took{obj_part}{adv_part}"
        elif bare in ("put",):
            return f"{subj} put{obj_part}{adv_part}"
        elif bare in ("run",):
            return f"{subj} ran{obj_part}{adv_part}"
        elif bare in ("drink",):
            return f"{subj} drank{obj_part}{adv_part}"
        elif bare in ("live",):
            return f"{subj} lived{obj_part}{adv_part}"
        elif bare in ("close",):
            return f"{subj} closed{obj_part}{adv_part}"
        elif bare in ("lose",):
            return f"{subj} lost{obj_part}{adv_part}"
        elif bare in ("answer/reply",):
            return f"{subj} answered/replied{obj_part}{adv_part}"
        elif bare in ("ask",):
            return f"{subj} asked{obj_part}{adv_part}"
        elif bare in ("know (a person)",):
            return f"{subj} knew{obj_part}{adv_part}"
        elif bare in ("fall",):
            return f"{subj} fell{obj_part}{adv_part}"
        elif bare in ("be born",):
            was = "was" if subject in ("io", "lui", "lei", "tu") else "were"
            return f"{subj} {was} born{obj_part}{adv_part}"
        elif bare in ("die",):
            return f"{subj} died{obj_part}{adv_part}"
        elif bare in ("hold/keep",):
            return f"{subj} held/kept{obj_part}{adv_part}"
        elif bare in ("choose",):
            return f"{subj} chose{obj_part}{adv_part}"
        elif bare in ("be able to/can",):
            return f"{subj} was able to{obj_part}{adv_part}" if subject in ("io", "lui", "lei") else f"{subj} were able to{obj_part}{adv_part}"
        elif bare in ("want",):
            return f"{subj} wanted{obj_part}{adv_part}"
        elif bare in ("have to/must",):
            return f"{subj} had to{obj_part}{adv_part}"
        elif bare in ("know",):
            return f"{subj} knew{obj_part}{adv_part}"
        elif bare in ("give",):
            return f"{subj} gave{obj_part}{adv_part}"
        elif bare in ("stay/be",):
            return f"{subj} stayed{obj_part}{adv_part}"
        elif bare in ("remain",):
            return f"{subj} remained{obj_part}{adv_part}"
        elif bare in ("stay/remain",):
            return f"{subj} stayed/remained{obj_part}{adv_part}"
        elif bare in ("go out",):
            return f"{subj} went out{obj_part}{adv_part}"
        elif bare in ("go up/climb",):
            return f"{subj} went up/climbed{obj_part}{adv_part}"
        elif bare in ("go down/descend",):
            return f"{subj} went down/descended{obj_part}{adv_part}"
        elif bare in ("send",):
            return f"{subj} sent{obj_part}{adv_part}"
        elif bare in ("turn off",):
            return f"{subj} turned off{obj_part}{adv_part}"
        elif bare in ("propose",):
            return f"{subj} proposed{obj_part}{adv_part}"
        elif bare in ("sell",):
            return f"{subj} sold{obj_part}{adv_part}"
        elif bare in ("receive",):
            return f"{subj} received{obj_part}{adv_part}"
        # Generic: add -ed (won't always be right, but gives the idea)
        else:
            if bare.endswith("e"):
                past = bare + "d"
            elif bare.endswith("y") and len(bare) > 1 and bare[-2] not in "aeiou":
                past = bare[:-1] + "ied"
            else:
                past = bare + "ed"
            return f"{subj} {past}{obj_part}{adv_part}"

    return f"{subj} {bare}{obj_part}{adv_part}"


# ---------------------------------------------------------------------------
# Sentence generation
# ---------------------------------------------------------------------------

def _pick_frame(difficulty_unlocked: bool) -> Dict[str, str]:
    """Pick a discourse frame (or no frame)."""
    if not difficulty_unlocked:
        # Simple frames only when locked
        simple = [NO_FRAME, NO_FRAME, NO_FRAME,
                  {"it": "Secondo me,", "en": "In my opinion,"},
                  {"it": "Di solito,", "en": "Usually,"},
                  {"it": "In realtà,", "en": "Actually,"}]
        return random.choice(simple)
    # 40% chance no frame
    if random.random() < 0.40:
        return NO_FRAME
    return random.choice(DISCOURSE_FRAMES)


def _pick_tense(difficulty_unlocked: bool, allowed_tenses: List[str]) -> str:
    """Pick a tense with appropriate weighting."""
    if not difficulty_unlocked:
        # Heavily weight present
        weights = []
        for t in allowed_tenses:
            if t == "presente":
                weights.append(70)
            elif t == "passato_prossimo":
                weights.append(15)
            elif t == "imperfetto":
                weights.append(10)
            else:
                weights.append(5)
        return random.choices(allowed_tenses, weights=weights, k=1)[0]
    else:
        # More even distribution
        weights = []
        for t in allowed_tenses:
            if t == "presente":
                weights.append(25)
            elif t == "passato_prossimo":
                weights.append(25)
            elif t == "imperfetto":
                weights.append(20)
            elif t == "futuro":
                weights.append(15)
            elif t == "condizionale":
                weights.append(15)
            else:
                weights.append(10)
        return random.choices(allowed_tenses, weights=weights, k=1)[0]


def _needs_object(verb: str) -> bool:
    """Does this verb typically take an object?"""
    # Intransitive / essere verbs usually don't take objects in our drills
    no_obj = ESSERE_VERBS | {
        "essere", "dormire", "camminare", "nuotare", "ballare",
        "cantare", "lavorare", "studiare", "abitare", "viaggiare",
        "vivere", "correre", "stare",
    }
    return verb not in no_obj


def _is_modal(verb: str) -> bool:
    return verb in ("potere", "volere", "dovere")


def _get_adjective_form(adj: Dict[str, str], gender: str, number: str) -> str:
    """Get the correctly agreed adjective form."""
    key = gender + ("s" if number == "s" else "p")
    return adj.get(key, adj["ms"])


def _get_combined_pronoun(indirect: str, direct: str) -> str:
    """Get combined pronoun form, or fall back to separate pronouns."""
    # Handle le (indirect, meaning 'to her') vs le (direct, meaning 'them f')
    ind_key = "le_ind" if indirect == "le" else indirect
    combo = COMBINED_PRONOUNS.get((ind_key, direct))
    if combo:
        return combo
    # Also try with regular 'gli' for 'to them'
    if indirect == "gli":
        combo = COMBINED_PRONOUNS.get(("gli", direct))
        if combo:
            return combo
    return f"{indirect} {direct}"


class SentenceSpec:
    """Specification of a sentence to drill."""

    def __init__(
        self,
        verb: str,
        tense: str,
        subject: str,
        frame: Dict[str, str],
        template: str,
        obj: Optional[Dict[str, str]] = None,
        adv: Optional[Dict[str, str]] = None,
        modal: Optional[str] = None,
        gender_io_tu: str = "m",
        # Template F extras
        direct_pronoun: Optional[Dict[str, str]] = None,
        indirect_pronoun: Optional[Dict[str, str]] = None,
        pronoun_type: str = "direct",  # "direct", "indirect", "combined"
        f_modal: Optional[str] = None,  # modal for F-modal variant
        # Template G extras
        adjective: Optional[Dict[str, str]] = None,
        gendered_subject: Optional[Dict[str, Any]] = None,
    ):
        self.verb = verb
        self.tense = tense
        self.subject = subject
        self.frame = frame
        self.template = template
        self.obj = obj
        self.adv = adv
        self.modal = modal
        self.gender_io_tu = gender_io_tu
        self.direct_pronoun = direct_pronoun
        self.indirect_pronoun = indirect_pronoun
        self.pronoun_type = pronoun_type
        self.f_modal = f_modal
        self.adjective = adjective
        self.gendered_subject = gendered_subject

    def _get_pronoun_it(self) -> str:
        """Get the Italian pronoun string for template F."""
        if self.pronoun_type == "combined" and self.indirect_pronoun and self.direct_pronoun:
            return _get_combined_pronoun(self.indirect_pronoun["it"], self.direct_pronoun["it"])
        elif self.pronoun_type == "indirect" and self.indirect_pronoun:
            return self.indirect_pronoun["it"]
        elif self.direct_pronoun:
            return self.direct_pronoun["it"]
        return ""

    def _get_pronoun_en(self) -> str:
        """Get the English pronoun description for template F."""
        if self.pronoun_type == "combined" and self.indirect_pronoun and self.direct_pronoun:
            return f"{self.direct_pronoun['en']} {self.indirect_pronoun['en']}"
        elif self.pronoun_type == "indirect" and self.indirect_pronoun:
            return self.indirect_pronoun["en"]
        elif self.direct_pronoun:
            return self.direct_pronoun["en"]
        return ""

    def build_italian(self) -> str:
        """Build the expected Italian sentence."""
        parts: List[str] = []
        if self.frame["it"]:
            parts.append(self.frame["it"])

        if self.template == "A":
            # Frame + subject + verb + object + adverb
            parts.append(self.subject)
            parts.append(conjugate(self.verb, self.tense, self.subject, self.gender_io_tu))
            if self.obj:
                parts.append(self.obj["it"])
            if self.adv:
                parts.append(self.adv["it"])

        elif self.template == "B":
            # Frame + subject + modal(tense) + infinitive + object
            parts.append(self.subject)
            parts.append(conjugate(self.modal or "potere", self.tense, self.subject, self.gender_io_tu))
            parts.append(self.verb)  # infinitive
            if self.obj:
                parts.append(self.obj["it"])

        elif self.template == "C":
            # Frame + subject + "vuole che" + subject2 (implied in prompt)
            # Simplified: subject + volere(tense) + infinitive + object
            parts.append(self.subject)
            parts.append(conjugate("volere", self.tense, self.subject, self.gender_io_tu))
            parts.append(self.verb)  # infinitive
            if self.obj:
                parts.append(self.obj["it"])

        elif self.template == "D":
            # "è possibile che" + subject + verb (presente/indicative)
            parts.append("è possibile che")
            parts.append(self.subject)
            parts.append(conjugate(self.verb, "presente", self.subject, self.gender_io_tu))
            if self.obj:
                parts.append(self.obj["it"])

        elif self.template == "E":
            # Question: Puoi/Potresti + infinitive + object?
            if self.tense == "condizionale":
                parts.append("potresti")
            else:
                parts.append("puoi")
            parts.append(self.verb)  # infinitive
            if self.obj:
                parts.append(self.obj["it"])
            # Append ? to last part
            if parts:
                parts[-1] = parts[-1] + "?"

        elif self.template == "F":
            # Pronoun placement template
            if self.f_modal:
                # Modal + infinitive with pronoun attached: "Vuole darglielo"
                # Or pronoun before modal: "Glielo vuole dare"
                # We'll use the pre-modal form: pronoun + modal + infinitive
                pron = self._get_pronoun_it()
                parts.append(self.subject)
                parts.append(pron)
                parts.append(conjugate(self.f_modal, self.tense, self.subject, self.gender_io_tu))
                parts.append(self.verb)
            else:
                # Simple: pronoun before conjugated verb
                # e.g., "Io glielo do" / "Lei me lo ha dato"
                pron = self._get_pronoun_it()
                parts.append(self.subject)
                parts.append(pron)
                parts.append(conjugate(self.verb, self.tense, self.subject, self.gender_io_tu))

        elif self.template == "G":
            # Agreement template: gendered subject + essere verb + adjective
            gs = self.gendered_subject
            adj = self.adjective
            if gs and adj:
                vs = gs["verb_subject"]  # lui/lei/loro for conjugation
                verb_form = conjugate(self.verb, self.tense, vs, self.gender_io_tu)
                adj_form = _get_adjective_form(adj, gs["gender"], gs["number"])
                parts.append(gs["it"])
                # For passato prossimo, agree participle already handled by conjugate
                if self.tense == "passato_prossimo":
                    # Need special agreement: auxiliary + agreed participle + adjective
                    uses_essere = self.verb in ESSERE_VERBS or self.verb == "essere"
                    aux_form = conjugate_presente("essere" if uses_essere else "avere", vs)
                    pp = _past_participle(self.verb)
                    if uses_essere:
                        # Agree participle with gendered subject
                        pp = _agree_participle_gendered(pp, gs["gender"], gs["number"])
                    parts.append(aux_form)
                    parts.append(pp)
                else:
                    parts.append(verb_form)
                parts.append(adj_form)

        return " ".join(parts)

    def build_english(self) -> str:
        """Build the English prompt."""
        verb_info = VERB_MAP.get(self.verb, {"en": self.verb})
        parts: List[str] = []
        if self.frame["en"]:
            parts.append(self.frame["en"])

        obj_en = self.obj["en"] if self.obj else ""
        adv_en = self.adv["en"] if self.adv else ""

        if self.template == "A":
            parts.append(english_conjugation(verb_info, self.tense, self.subject, obj_en, adv_en))
        elif self.template == "B":
            modal_info = VERB_MAP.get(self.modal or "potere", {"en": "to be able to"})
            modal_en = english_conjugation(modal_info, self.tense, self.subject)
            parts.append(f"{modal_en} {verb_info['en'].replace('to ', '')}")
            if obj_en:
                parts[-1] += f" {obj_en}"
        elif self.template == "C":
            subj = SUBJECT_EN[self.subject]
            want_form = english_conjugation(VERB_MAP["volere"], self.tense, self.subject)
            bare = verb_info["en"].replace("to ", "")
            s = f"{want_form} {bare}"
            if obj_en:
                s += f" {obj_en}"
            parts.append(s)
        elif self.template == "D":
            subj = SUBJECT_EN[self.subject]
            bare = verb_info["en"].replace("to ", "")
            third = self.subject in ("lui", "lei")
            if bare in ("be",):
                vf = "is" if third else "are" if self.subject != "io" else "am"
            elif bare in ("have",):
                vf = "has" if third else "have"
            else:
                vf = bare + "s" if third else bare
            s = f"it's possible that {subj} {vf}"
            if obj_en:
                s += f" {obj_en}"
            parts.append(s)
        elif self.template == "E":
            bare = verb_info["en"].replace("to ", "")
            if self.tense == "condizionale":
                s = f"could you {bare}"
            else:
                s = f"can you {bare}"
            if obj_en:
                s += f" {obj_en}"
            s += "?"
            parts.append(s)

        elif self.template == "F":
            pron_en = self._get_pronoun_en()
            bare = verb_info["en"].replace("to ", "")
            subj = SUBJECT_EN[self.subject]
            if self.f_modal:
                modal_info = VERB_MAP.get(self.f_modal, {"en": "to be able to"})
                modal_en = english_conjugation(modal_info, self.tense, self.subject)
                s = f"{modal_en} {bare} {pron_en}"
                parts.append(s)
            else:
                verb_en = english_conjugation(verb_info, self.tense, self.subject)
                s = f"{verb_en} {pron_en}"
                parts.append(s)
            parts.append("[use Italian pronoun placement]")

        elif self.template == "G":
            gs = self.gendered_subject
            adj = self.adjective
            if gs and adj:
                bare = verb_info["en"].replace("to ", "")
                subj_en = gs["en"]
                adj_en = adj["en"]
                vs = gs["verb_subject"]
                verb_en = english_conjugation(verb_info, self.tense, vs)
                # Replace the subject pronoun with the noun phrase
                for pron in ("he", "she", "they", "I", "you", "we", "you all"):
                    if verb_en.startswith(pron + " "):
                        verb_en = verb_en[len(pron) + 1:]
                        break
                s = f"{subj_en} {verb_en} {adj_en}"
                parts.append(s)

        return " ".join(parts)


def _generate_template_f(
    verb: str,
    tense: str,
    subject: str,
    frame: Dict[str, str],
    gender_io_tu: str,
) -> SentenceSpec:
    """Generate a template F (pronoun placement) sentence."""
    pronoun_type = random.choice(["direct", "indirect", "combined"])
    direct_pron = random.choice(DIRECT_PRONOUNS)
    indirect_pron = random.choice(INDIRECT_PRONOUNS)

    # 30% chance of using a modal (pronoun goes before modal)
    f_modal = random.choice(["volere", "potere", "dovere"]) if random.random() < 0.3 else None

    return SentenceSpec(
        verb=verb, tense=tense, subject=subject, frame=frame, template="F",
        gender_io_tu=gender_io_tu,
        direct_pronoun=direct_pron if pronoun_type in ("direct", "combined") else None,
        indirect_pronoun=indirect_pron if pronoun_type in ("indirect", "combined") else None,
        pronoun_type=pronoun_type,
        f_modal=f_modal,
    )


def _generate_template_g(
    verb: str,
    tense: str,
    frame: Dict[str, str],
    gender_io_tu: str,
) -> SentenceSpec:
    """Generate a template G (agreement) sentence."""
    gs = random.choice(GENDERED_SUBJECTS)
    adj = random.choice(ADJECTIVES)
    # Use essere verb for agreement drill, prefer passato_prossimo 50% of the time
    if random.random() < 0.5 and tense != "passato_prossimo":
        tense = "passato_prossimo"

    return SentenceSpec(
        verb=verb, tense=tense, subject=gs["verb_subject"],
        frame=frame, template="G",
        gender_io_tu=gender_io_tu,
        adjective=adj,
        gendered_subject=gs,
    )


def generate_sentence(
    verb: str,
    allowed_tenses: List[str],
    difficulty_unlocked: bool,
    gender_io_tu: str,
    focus_mode: str = "all",
) -> SentenceSpec:
    """Generate a random sentence specification for a given verb."""
    tense = _pick_tense(difficulty_unlocked, allowed_tenses)
    frame = _pick_frame(difficulty_unlocked)

    # Focus mode: conjugation-endings biases toward voi/loro
    if focus_mode == "conjugation-endings":
        subject = random.choices(
            SUBJECTS,
            weights=[5, 5, 5, 5, 10, 35, 35],  # heavy on voi/loro
            k=1,
        )[0]
    else:
        subject = random.choice(SUBJECTS)

    # Focus mode overrides template selection
    if focus_mode == "pronouns":
        # Heavily weight template F
        if verb in PRONOUN_VERBS or random.random() < 0.7:
            effective_verb = verb if verb in PRONOUN_VERBS else random.choice(PRONOUN_VERBS)
            return _generate_template_f(effective_verb, tense, subject, frame, gender_io_tu)

    if focus_mode == "agreement":
        # Heavily weight template G
        if verb in AGREEMENT_VERBS or random.random() < 0.7:
            effective_verb = verb if verb in AGREEMENT_VERBS else random.choice(AGREEMENT_VERBS)
            return _generate_template_g(effective_verb, tense, frame, gender_io_tu)

    # Choose template
    if _is_modal(verb):
        # Modal verbs always use template A (conjugated directly)
        template = "A"
        obj = random.choice(OBJECTS) if random.random() < 0.5 else None
        adv = random.choice(ADVERBIALS) if random.random() < 0.3 else None
        return SentenceSpec(verb, tense, subject, frame, template, obj, adv, gender_io_tu=gender_io_tu)

    # Weight templates (now including F and G)
    if difficulty_unlocked:
        template = random.choices(
            ["A", "B", "C", "D", "E", "F", "G"],
            weights=[25, 15, 10, 8, 7, 18, 17],
            k=1,
        )[0]
    else:
        template = random.choices(
            ["A", "B", "F", "G"],
            weights=[55, 15, 15, 15],
            k=1,
        )[0]

    obj = None
    adv = None
    modal = None

    if template == "A":
        if _needs_object(verb) and random.random() < 0.6:
            obj = random.choice(OBJECTS)
        if random.random() < 0.3:
            adv = random.choice(ADVERBIALS)

    elif template == "B":
        modal = random.choice(["potere", "volere", "dovere"])
        if _needs_object(verb) and random.random() < 0.5:
            obj = random.choice(OBJECTS)

    elif template == "C":
        if _needs_object(verb) and random.random() < 0.5:
            obj = random.choice(OBJECTS)

    elif template == "D":
        if _needs_object(verb) and random.random() < 0.5:
            obj = random.choice(OBJECTS)

    elif template == "E":
        subject = "tu"  # question directed at tu
        if _needs_object(verb) and random.random() < 0.6:
            obj = random.choice(OBJECTS)

    elif template == "F":
        effective_verb = verb if verb in PRONOUN_VERBS else random.choice(PRONOUN_VERBS)
        return _generate_template_f(effective_verb, tense, subject, frame, gender_io_tu)

    elif template == "G":
        effective_verb = verb if verb in AGREEMENT_VERBS else random.choice(AGREEMENT_VERBS)
        return _generate_template_g(effective_verb, tense, frame, gender_io_tu)

    return SentenceSpec(verb, tense, subject, frame, template, obj, adv, modal, gender_io_tu)


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

def normalize(text: str) -> str:
    """Normalize user input and expected answers for comparison."""
    s = text.strip().lower()
    # Normalize apostrophes
    s = s.replace("\u2019", "'").replace("\u2018", "'").replace("\u0060", "'")
    # Remove final punctuation
    s = s.rstrip(".,;:!?")
    # Collapse multiple spaces
    s = re.sub(r"\s+", " ", s)
    # Allow optional comma after discourse frames: remove commas for comparison
    # Actually we keep commas because they're part of the expected answer
    # But allow missing comma after frame: we strip commas adjacent to spaces
    s = re.sub(r"\s*,\s*", " , ", s)  # normalize comma spacing
    s = re.sub(r"\s+", " ", s).strip()
    return s


def normalize_flexible(text: str) -> str:
    """Even more flexible normalization: strip all commas entirely.

    Used for comparison — if both sides match after stripping commas, accept it.
    """
    return normalize(text).replace(",", "").replace("  ", " ").strip()


def answers_match(user_input: str, expected: str) -> bool:
    """Check if user input matches expected answer."""
    # Try exact normalized match
    if normalize(user_input) == normalize(expected):
        return True
    # Try flexible match (ignore commas)
    if normalize_flexible(user_input) == normalize_flexible(expected):
        return True
    return False


# ---------------------------------------------------------------------------
# Hint generation
# ---------------------------------------------------------------------------

def generate_hint(user_input: str, expected: str, spec: SentenceSpec) -> str:
    """Generate a short hint about what went wrong."""
    u = normalize(user_input).split()
    e = normalize(expected).split()

    verb_form_expected = conjugate(spec.verb, spec.tense, spec.subject, spec.gender_io_tu)

    # Check if frame is missing
    if spec.frame["it"] and spec.frame["it"].lower().rstrip(",") not in normalize(user_input):
        return "missing discourse frame"

    # Check if verb form is wrong
    if verb_form_expected.lower() not in normalize(user_input):
        # Could be wrong tense or wrong person
        # Check if they used the right verb at all
        for t in TENSES:
            for s in SUBJECTS:
                try:
                    form = conjugate(spec.verb, t, s, spec.gender_io_tu)
                    if form.lower() in normalize(user_input):
                        if t != spec.tense and s != spec.subject:
                            return f"wrong tense and wrong person (expected {TENSE_EN[spec.tense]}, {spec.subject})"
                        elif t != spec.tense:
                            return f"wrong tense (expected {TENSE_EN[spec.tense]})"
                        elif s != spec.subject:
                            return f"wrong person (expected {spec.subject})"
                except Exception:
                    pass
        # Check passato prossimo auxiliary
        if spec.tense == "passato_prossimo":
            uses_essere = spec.verb in ESSERE_VERBS or spec.verb == "essere"
            if uses_essere and "ha " in normalize(user_input):
                return "wrong auxiliary (use essere, not avere)"
            if not uses_essere and ("è " in normalize(user_input) or "sono " in normalize(user_input)):
                return "wrong auxiliary (use avere, not essere)"
        return "wrong verb conjugation"

    return "check spelling and word order"


# ---------------------------------------------------------------------------
# Progress / persistence
# ---------------------------------------------------------------------------

def ensure_data_dir() -> None:
    """Create data directory if it doesn't exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_progress() -> Dict[str, Any]:
    """Load progress from file, or return default."""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    # Default structure
    return {
        "lifetime_minutes": 0.0,
        "tense_accuracy": {},
        "person_accuracy": {},
        "tense_person_accuracy": {},
        "verbs": {},
    }


def save_progress(progress: Dict[str, Any]) -> None:
    """Save progress to file."""
    ensure_data_dir()
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, indent=2, ensure_ascii=False)


def get_verb_progress(progress: Dict[str, Any], verb: str) -> Dict[str, Any]:
    """Get or create verb progress entry."""
    if verb not in progress["verbs"]:
        progress["verbs"][verb] = {
            "total_attempts": 0,
            "correct_attempts": 0,
            "hint_uses": 0,
            "mastery_count": 0,
            "mastered": False,
            "last_seen": None,
        }
    return progress["verbs"][verb]


def update_verb_progress(
    progress: Dict[str, Any], verb: str, correct: bool, hint_used: bool
) -> None:
    """Update progress for a verb attempt."""
    vp = get_verb_progress(progress, verb)
    vp["total_attempts"] += 1
    if correct:
        vp["correct_attempts"] += 1
        vp["mastery_count"] += 1
        if vp["mastery_count"] >= 10:
            vp["mastered"] = True
    else:
        # Reset mastery count on incorrect (or reduce)
        vp["mastery_count"] = max(0, vp["mastery_count"] - 1)
    if hint_used:
        vp["hint_uses"] += 1
    vp["last_seen"] = datetime.now(timezone.utc).isoformat()


def update_tense_person_accuracy(
    progress: Dict[str, Any], tense: str, person: str, correct: bool
) -> None:
    """Update tense and person accuracy tracking."""
    # Tense accuracy
    if tense not in progress["tense_accuracy"]:
        progress["tense_accuracy"][tense] = {"attempts": 0, "correct": 0}
    progress["tense_accuracy"][tense]["attempts"] += 1
    if correct:
        progress["tense_accuracy"][tense]["correct"] += 1

    # Person accuracy
    if person not in progress["person_accuracy"]:
        progress["person_accuracy"][person] = {"attempts": 0, "correct": 0}
    progress["person_accuracy"][person]["attempts"] += 1
    if correct:
        progress["person_accuracy"][person]["correct"] += 1

    # Combined
    key = f"{tense}_{person}"
    if key not in progress["tense_person_accuracy"]:
        progress["tense_person_accuracy"][key] = {"attempts": 0, "correct": 0}
    progress["tense_person_accuracy"][key]["attempts"] += 1
    if correct:
        progress["tense_person_accuracy"][key]["correct"] += 1


def append_attempt(record: Dict[str, Any]) -> None:
    """Append an attempt record to the JSONL log."""
    ensure_data_dir()
    with open(ATTEMPTS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def append_flagged(record: Dict[str, Any]) -> None:
    """Append a flagged record to the JSONL log."""
    ensure_data_dir()
    with open(FLAGGED_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Verb selection / adaptation
# ---------------------------------------------------------------------------

def select_verb(
    progress: Dict[str, Any],
    mode: str,
    allowed_tenses: List[str],
) -> str:
    """Select a verb based on mastery and recency."""
    now = datetime.now(timezone.utc)

    candidates: List[Tuple[str, float]] = []
    for v in VERBS:
        verb = v["infinitive"]
        vp = get_verb_progress(progress, verb)

        if mode == "non-mastered" and vp["mastered"]:
            continue
        if mode == "review" and not vp["mastered"]:
            continue

        # Calculate effective mastery for weighting
        effective_mastery = vp["mastery_count"]
        if vp["last_seen"]:
            try:
                last = datetime.fromisoformat(vp["last_seen"])
                if last.tzinfo is None:
                    last = last.replace(tzinfo=timezone.utc)
                days_since = (now - last).days
                if days_since > 14:
                    effective_mastery = effective_mastery / 2
            except (ValueError, TypeError):
                pass

        # Weight: prefer lower mastery
        if vp["mastered"] and effective_mastery >= 5:
            # 15% chance for mastered verbs
            weight = 0.15
        else:
            weight = max(0.1, 10 - effective_mastery)

        candidates.append((verb, weight))

    if not candidates:
        # Fallback: all verbs
        candidates = [(v["infinitive"], 1.0) for v in VERBS]

    verbs, weights = zip(*candidates)
    return random.choices(list(verbs), weights=list(weights), k=1)[0]


def check_difficulty_unlocked(progress: Dict[str, Any]) -> bool:
    """Check if 20% of verbs have mastery_count >= 3."""
    total = len(VERBS)
    count = 0
    for v in VERBS:
        vp = progress["verbs"].get(v["infinitive"], {})
        if vp.get("mastery_count", 0) >= 3:
            count += 1
    return count >= total * 0.20


# ---------------------------------------------------------------------------
# Stats display
# ---------------------------------------------------------------------------

def format_duration(minutes: float) -> str:
    """Format minutes as Xh Ym."""
    h = int(minutes // 60)
    m = int(minutes % 60)
    if h > 0:
        return f"{h}h {m}m"
    return f"{m}m"


def show_stats(progress: Dict[str, Any], session_minutes: float) -> None:
    """Display :stats output."""
    print("\n" + "=" * 60)
    print("STATISTICS")
    print("=" * 60)

    lifetime = progress.get("lifetime_minutes", 0.0) + session_minutes
    print(f"\nLifetime practice: {format_duration(lifetime)}")
    print(f"Current session:   {format_duration(session_minutes)}")

    # Verb stats
    verb_stats: List[Tuple[str, float, int, bool]] = []
    for v in VERBS:
        vp = progress["verbs"].get(v["infinitive"], {})
        total = vp.get("total_attempts", 0)
        correct = vp.get("correct_attempts", 0)
        mastered = vp.get("mastered", False)
        acc = correct / total if total > 0 else 1.0
        verb_stats.append((v["infinitive"], acc, total, mastered))

    # Top 10 weakest (lowest accuracy, at least 1 attempt)
    attempted = [vs for vs in verb_stats if vs[2] > 0]
    weakest = sorted(attempted, key=lambda x: (x[1], -x[2]))[:10]
    if weakest:
        print("\nTop 10 weakest verbs:")
        for verb, acc, total, _ in weakest:
            print(f"  {verb:20s} {acc*100:5.1f}% ({total} attempts)")

    # Top 10 mastered
    mastered_list = sorted(
        [vs for vs in verb_stats if vs[3]],
        key=lambda x: -x[2]
    )[:10]
    if mastered_list:
        print("\nTop 10 mastered verbs:")
        for verb, acc, total, _ in mastered_list:
            print(f"  {verb:20s} {acc*100:5.1f}% ({total} attempts)")

    # Weakest tenses
    ta = progress.get("tense_accuracy", {})
    if ta:
        print("\nTense accuracy:")
        for tense in TENSES:
            if tense in ta:
                a = ta[tense]["attempts"]
                c = ta[tense]["correct"]
                pct = c / a * 100 if a > 0 else 0
                print(f"  {TENSE_EN.get(tense, tense):20s} {pct:5.1f}% ({a} attempts)")

    # Weakest person/tense combos
    tpa = progress.get("tense_person_accuracy", {})
    if tpa:
        combos = []
        for key, data in tpa.items():
            a = data["attempts"]
            c = data["correct"]
            if a > 0:
                combos.append((key, c / a, a))
        combos.sort(key=lambda x: (x[1], -x[2]))
        if combos:
            print("\nWeakest person/tense combos:")
            for key, acc, attempts in combos[:10]:
                print(f"  {key:30s} {acc*100:5.1f}% ({attempts} attempts)")

    print("=" * 60 + "\n")


# ---------------------------------------------------------------------------
# Self-check / test
# ---------------------------------------------------------------------------

def run_self_check() -> None:
    """Run :test — print sample conjugations for verification."""
    print("\n" + "=" * 60)
    print("CONJUGATION SELF-CHECK")
    print("=" * 60)

    test_verbs = ["parlare", "scrivere", "dormire", "capire", "essere",
                  "avere", "fare", "andare", "venire", "potere"]
    test_subjects = ["io", "tu", "lui", "noi", "voi", "loro"]

    for verb in test_verbs:
        print(f"\n--- {verb} ---")
        for tense in TENSES:
            forms = []
            for subj in test_subjects:
                form = conjugate(verb, tense, subj)
                forms.append(f"{subj} {form}")
            print(f"  {TENSE_EN[tense]:20s}: {' | '.join(forms)}")

    print("\n" + "=" * 60 + "\n")


# ---------------------------------------------------------------------------
# Session summary
# ---------------------------------------------------------------------------

def show_session_summary(
    session_correct: int,
    session_total: int,
    session_minutes: float,
    lifetime_minutes: float,
) -> None:
    """Show summary on exit."""
    print("\n" + "=" * 60)
    print("SESSION SUMMARY")
    print("=" * 60)
    acc = session_correct / session_total * 100 if session_total > 0 else 0
    print(f"  Answered:     {session_total}")
    print(f"  Correct:      {session_correct}")
    print(f"  Accuracy:     {acc:.1f}%")
    print(f"  Session time: {format_duration(session_minutes)}")
    print(f"  Lifetime:     {format_duration(lifetime_minutes)}")
    print("=" * 60 + "\n")


# ---------------------------------------------------------------------------
# Sync helper
# ---------------------------------------------------------------------------

def run_sync() -> None:
    """Run sync_to_sheets.py after loading .env."""
    script_dir = Path(__file__).resolve().parent
    env_file = script_dir / ".env"
    sync_script = script_dir / "sync_to_sheets.py"

    if not sync_script.exists():
        print("Warning: sync_to_sheets.py not found, skipping sync.")
        return

    # Load .env
    env = os.environ.copy()
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    env[key.strip()] = value.strip()

    try:
        result = subprocess.run(
            [sys.executable, str(sync_script)],
            env=env,
            cwd=str(script_dir),
            timeout=60,
        )
        if result.returncode != 0:
            print("Warning: sync_to_sheets.py exited with errors.")
    except Exception as e:
        print(f"Warning: sync failed ({e})")


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def startup_prompts() -> Tuple[str, str, List[str], str]:
    """Ask startup questions. Returns (mode, gender_io_tu, allowed_tenses, focus_mode)."""
    print("\n" + "=" * 60)
    print("  ITALIAN SENTENCE PRODUCTION DRILL")
    print("=" * 60)
    print()

    # Mode
    print("Select mode:")
    print("  1. all (default)")
    print("  2. non-mastered only")
    print("  3. review mastered")
    print("  4. custom (pick tenses)")
    choice = input("Choice [1]: ").strip()
    if choice == "2":
        mode = "non-mastered"
    elif choice == "3":
        mode = "review"
    elif choice == "4":
        mode = "custom"
    else:
        mode = "all"

    # Custom tense selection
    allowed_tenses = list(TENSES)
    if mode == "custom":
        print("\nSelect tenses (comma-separated numbers):")
        for i, t in enumerate(TENSES, 1):
            print(f"  {i}. {TENSE_EN[t]}")
        sel = input("Tenses [all]: ").strip()
        if sel:
            indices = [int(x.strip()) - 1 for x in sel.split(",") if x.strip().isdigit()]
            chosen = [TENSES[i] for i in indices if 0 <= i < len(TENSES)]
            if chosen:
                allowed_tenses = chosen

    # Focus mode
    print("\nSelect focus:")
    print("  1. all (default)")
    print("  2. pronouns — weight toward pronoun placement drills")
    print("  3. agreement — weight toward gender/number agreement drills")
    print("  4. conjugation-endings — weight toward voi/loro across all tenses")
    f_choice = input("Choice [1]: ").strip()
    if f_choice == "2":
        focus_mode = "pronouns"
    elif f_choice == "3":
        focus_mode = "agreement"
    elif f_choice == "4":
        focus_mode = "conjugation-endings"
    else:
        focus_mode = "all"

    # Gender for io/tu passato prossimo with essere
    print("\nFor io/tu with essere verbs in passato prossimo:")
    print("  1. masculine (default)")
    print("  2. feminine")
    g_choice = input("Choice [1]: ").strip()
    gender_io_tu = "f" if g_choice == "2" else "m"

    print()
    return mode, gender_io_tu, allowed_tenses, focus_mode


def main() -> None:
    """Main entry point."""
    ensure_data_dir()
    progress = load_progress()

    mode, gender_io_tu, allowed_tenses, focus_mode = startup_prompts()

    session_start = time.time()
    session_total = 0
    session_correct = 0

    print("Type :help for commands. Type :quit to exit.\n")

    try:
        while True:
            # Session stats
            elapsed_min = (time.time() - session_start) / 60
            acc_pct = (session_correct / session_total * 100) if session_total > 0 else 0

            # Select verb
            difficulty_unlocked = check_difficulty_unlocked(progress)
            verb = select_verb(progress, mode, allowed_tenses)
            vp = get_verb_progress(progress, verb)
            verb_acc = (
                f"{vp['correct_attempts']}/{vp['total_attempts']}"
                if vp["total_attempts"] > 0
                else "new"
            )

            # Generate sentence
            spec = generate_sentence(verb, allowed_tenses, difficulty_unlocked, gender_io_tu, focus_mode)
            expected_it = spec.build_italian()
            english_prompt = spec.build_english()

            # Display
            print(
                f"[Session: {session_total} answered | {acc_pct:.0f}% accuracy | "
                f"{format_duration(elapsed_min)}] {verb}: {verb_acc}"
            )
            tense_label = TENSE_EN.get(spec.tense, spec.tense)
            print(f"  Tense: {tense_label} | Subject: {spec.subject}")
            print(f"  EN: {english_prompt}")
            print()

            hint_used = False

            # Get user input
            try:
                user_input = input("  IT: ").strip()
            except EOFError:
                break

            if not user_input:
                continue

            # --- Commands ---
            if user_input.lower() == ":quit":
                break

            if user_input.lower() == ":help":
                print("\nCommands:")
                print("  :quit   — exit, save, show summary, sync")
                print("  :stats  — show detailed statistics")
                print("  :hint   — reveal verb infinitive + required tense")
                print("  :flag   — mark sentence as unnatural, skip")
                print("  :test   — run conjugation self-check")
                print("  :help   — show this help")
                print()
                continue

            if user_input.lower() == ":stats":
                show_stats(progress, elapsed_min)
                continue

            if user_input.lower() == ":test":
                run_self_check()
                continue

            if user_input.lower() == ":hint":
                hint_used = True
                vp["hint_uses"] = vp.get("hint_uses", 0) + 1
                print(f"\n  Hint: {verb} ({VERB_MAP[verb]['en']}) — {tense_label}")
                if spec.tense == "passato_prossimo":
                    aux = "essere" if (verb in ESSERE_VERBS or verb == "essere") else "avere"
                    print(f"  Auxiliary: {aux}")
                print()
                # Re-prompt for answer
                try:
                    user_input = input("  IT: ").strip()
                except EOFError:
                    break
                if user_input.lower() in (":quit", ":flag", ":stats", ":help", ":test"):
                    if user_input.lower() == ":quit":
                        break
                    continue

            if user_input.lower() == ":flag":
                record = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "verb": verb,
                    "tense": spec.tense,
                    "subject": spec.subject,
                    "frame": spec.frame["it"],
                    "english_prompt": english_prompt,
                    "expected": expected_it,
                }
                append_flagged(record)
                print("  Flagged. Skipping.\n")
                continue

            # --- Check answer ---
            correct = answers_match(user_input, expected_it)
            session_total += 1

            # Log attempt
            attempt_record = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "verb": verb,
                "tense": spec.tense,
                "subject": spec.subject,
                "frame": spec.frame["it"],
                "english_prompt": english_prompt,
                "expected": expected_it,
                "user_input": user_input,
                "correct": correct,
                "hint_used": hint_used,
            }
            append_attempt(attempt_record)

            if correct:
                session_correct += 1
                if not hint_used:
                    update_verb_progress(progress, verb, True, False)
                else:
                    # Hint used — don't count as correct for mastery
                    update_verb_progress(progress, verb, False, True)
                update_tense_person_accuracy(progress, spec.tense, spec.subject, True)
                save_progress(progress)
                print("  Correct!\n")
            else:
                update_verb_progress(progress, verb, False, hint_used)
                update_tense_person_accuracy(progress, spec.tense, spec.subject, False)
                save_progress(progress)

                hint_msg = generate_hint(user_input, expected_it, spec)
                print(f"\n  Incorrect.")
                print(f"  Your answer:     {normalize(user_input)}")
                print(f"  Expected answer:  {normalize(expected_it)}")
                print(f"  Hint: {hint_msg}")
                print(f"\n  Type the correct answer 3 times:")

                reps = 0
                while reps < 3:
                    try:
                        retry = input(f"  ({reps+1}/3) IT: ").strip()
                    except EOFError:
                        break
                    if retry.lower() == ":quit":
                        # Save and exit from retry loop
                        session_minutes = (time.time() - session_start) / 60
                        progress["lifetime_minutes"] = progress.get("lifetime_minutes", 0.0) + session_minutes
                        save_progress(progress)
                        show_session_summary(session_correct, session_total, session_minutes, progress["lifetime_minutes"])
                        run_sync()
                        return
                    if answers_match(retry, expected_it):
                        reps += 1
                        if reps < 3:
                            print("  Good. Keep going.")
                    else:
                        print(f"  Not quite. Expected: {normalize(expected_it)}")
                print("  Done. Moving on.\n")

    except KeyboardInterrupt:
        print("\n\nInterrupted.")

    # --- Save & exit ---
    session_minutes = (time.time() - session_start) / 60
    progress["lifetime_minutes"] = progress.get("lifetime_minutes", 0.0) + session_minutes
    save_progress(progress)
    show_session_summary(
        session_correct, session_total, session_minutes, progress["lifetime_minutes"]
    )
    run_sync()


if __name__ == "__main__":
    main()
