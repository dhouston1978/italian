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

DATA_DIR = Path(os.environ["ITALIAN_DRILL_DATA_DIR"]) if "ITALIAN_DRILL_DATA_DIR" in os.environ else Path(__file__).resolve().parent / "italian_drill_data"
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

# ---------------------------------------------------------------------------
# Per-verb-category object nouns (semantically plausible pairings)
# ---------------------------------------------------------------------------

# Fallback / general-purpose objects for verbs without a specific category
OBJECTS_DEFAULT: List[Dict[str, str]] = [
    {"it": "il libro", "en": "the book"},
    {"it": "il telefono", "en": "the phone"},
    {"it": "la macchina", "en": "the car"},
    {"it": "il giornale", "en": "the newspaper"},
    {"it": "la porta", "en": "the door"},
    {"it": "il treno", "en": "the train"},
    {"it": "la casa", "en": "the house"},
]

# Category → list of plausible objects
OBJECTS_BY_CATEGORY: Dict[str, List[Dict[str, str]]] = {
    # Eating/drinking/cooking
    "food": [
        {"it": "la pizza", "en": "the pizza"},
        {"it": "la cena", "en": "the dinner"},
        {"it": "il caffè", "en": "the coffee"},
        {"it": "il pane", "en": "the bread"},
        {"it": "l'acqua", "en": "the water"},
        {"it": "la pasta", "en": "the pasta"},
        {"it": "il pranzo", "en": "the lunch"},
    ],
    # Reading/writing/studying
    "text": [
        {"it": "il libro", "en": "the book"},
        {"it": "la lettera", "en": "the letter"},
        {"it": "il giornale", "en": "the newspaper"},
        {"it": "il messaggio", "en": "the message"},
        {"it": "l'email", "en": "the email"},
        {"it": "la poesia", "en": "the poem"},
    ],
    # Communication / telling / explaining
    "communication": [
        {"it": "la verità", "en": "the truth"},
        {"it": "la risposta", "en": "the answer"},
        {"it": "la storia", "en": "the story"},
        {"it": "il problema", "en": "the problem"},
        {"it": "la notizia", "en": "the news"},
        {"it": "la situazione", "en": "the situation"},
    ],
    # Watching/listening
    "media": [
        {"it": "il film", "en": "the film"},
        {"it": "la musica", "en": "the music"},
        {"it": "la partita", "en": "the match"},
        {"it": "il programma", "en": "the program"},
        {"it": "la canzone", "en": "the song"},
    ],
    # Helping / teaching / people as objects
    "people": [
        {"it": "un amico", "en": "a friend"},
        {"it": "i figli", "en": "the children"},
        {"it": "sua sorella", "en": "his/her sister"},
        {"it": "mia madre", "en": "my mother"},
        {"it": "gli studenti", "en": "the students"},
        {"it": "il collega", "en": "the colleague"},
        {"it": "mio fratello", "en": "my brother"},
        {"it": "la nonna", "en": "the grandmother"},
        {"it": "il vicino", "en": "the neighbor"},
        {"it": "i genitori", "en": "the parents"},
    ],
    # Buying/selling/paying/bringing/carrying
    "commerce": [
        {"it": "il regalo", "en": "the gift"},
        {"it": "i biglietti", "en": "the tickets"},
        {"it": "la macchina", "en": "the car"},
        {"it": "il vestito", "en": "the dress"},
        {"it": "il telefono", "en": "the phone"},
        {"it": "il conto", "en": "the bill"},
    ],
    # Finding / looking for / choosing
    "seeking": [
        {"it": "il lavoro", "en": "the work"},
        {"it": "la casa", "en": "the house"},
        {"it": "la soluzione", "en": "the solution"},
        {"it": "il ristorante", "en": "the restaurant"},
        {"it": "le chiavi", "en": "the keys"},
        {"it": "la strada", "en": "the road"},
    ],
    # Playing (instrument)
    "instrument": [
        {"it": "la chitarra", "en": "the guitar"},
        {"it": "il pianoforte", "en": "the piano"},
        {"it": "il violino", "en": "the violin"},
    ],
    # Opening/closing/turning off
    "physical": [
        {"it": "la porta", "en": "the door"},
        {"it": "la finestra", "en": "the window"},
        {"it": "la luce", "en": "the light"},
        {"it": "il computer", "en": "the computer"},
        {"it": "il rubinetto", "en": "the faucet"},
    ],
    # Calling (people only)
    "calling": [
        {"it": "un amico", "en": "a friend"},
        {"it": "il medico", "en": "the doctor"},
        {"it": "mia madre", "en": "my mother"},
        {"it": "mio padre", "en": "my father"},
        {"it": "mia sorella", "en": "my sister"},
        {"it": "il vicino", "en": "the neighbor"},
        {"it": "un taxi", "en": "a taxi"},
    ],
    # Remembering / forgetting
    "memory": [
        {"it": "il nome", "en": "the name"},
        {"it": "la password", "en": "the password"},
        {"it": "l'appuntamento", "en": "the appointment"},
        {"it": "l'indirizzo", "en": "the address"},
        {"it": "il numero", "en": "the number"},
    ],
    # Preparing
    "preparing": [
        {"it": "la valigia", "en": "the suitcase"},
        {"it": "la cena", "en": "the dinner"},
        {"it": "la lezione", "en": "the lesson"},
        {"it": "il pranzo", "en": "the lunch"},
        {"it": "la festa", "en": "the party"},
    ],
    # Changing / trying
    "change": [
        {"it": "il programma", "en": "the plan"},
        {"it": "la strategia", "en": "the strategy"},
        {"it": "il vestito", "en": "the outfit"},
        {"it": "le abitudini", "en": "the habits"},
    ],
    # Using
    "using": [
        {"it": "il computer", "en": "the computer"},
        {"it": "il telefono", "en": "the phone"},
        {"it": "la macchina", "en": "the car"},
        {"it": "internet", "en": "the internet"},
    ],
    # Visiting
    "places": [
        {"it": "il museo", "en": "the museum"},
        {"it": "la città", "en": "the city"},
        {"it": "i nonni", "en": "the grandparents"},
        {"it": "Roma", "en": "Rome"},
    ],
    # Waiting for
    "waiting": [
        {"it": "l'autobus", "en": "the bus"},
        {"it": "un amico", "en": "a friend"},
        {"it": "il treno", "en": "the train"},
        {"it": "il risultato", "en": "the result"},
    ],
    # Leaving / letting
    "leaving": [
        {"it": "il lavoro", "en": "the job"},
        {"it": "la città", "en": "the city"},
        {"it": "la casa", "en": "the house"},
        {"it": "un messaggio", "en": "a message"},
    ],
    # Proposing
    "proposing": [
        {"it": "un'idea", "en": "an idea"},
        {"it": "una soluzione", "en": "a solution"},
        {"it": "un cambiamento", "en": "a change"},
    ],
    # Wishing / desiring / wanting
    "desire": [
        {"it": "la pace", "en": "peace"},
        {"it": "un caffè", "en": "a coffee"},
        {"it": "una vacanza", "en": "a vacation"},
        {"it": "il successo", "en": "success"},
    ],
    # Keeping / holding
    "keeping": [
        {"it": "il segreto", "en": "the secret"},
        {"it": "la promessa", "en": "the promise"},
        {"it": "le chiavi", "en": "the keys"},
        {"it": "il libro", "en": "the book"},
    ],
}

# Verb → category mapping
VERB_OBJECT_CATEGORY: Dict[str, str] = {
    # Food verbs
    "mangiare": "food", "cucinare": "food", "bere": "food",
    "preparare": "preparing",
    # Text verbs
    "scrivere": "text", "leggere": "text", "studiare": "text",
    # Communication
    "dire": "communication", "raccontare": "communication",
    "spiegare": "communication", "rispondere": "communication",
    # Media
    "guardare": "media", "ascoltare": "media",
    # People
    "aiutare": "people", "insegnare": "people", "seguire": "people",
    # Commerce
    "comprare": "commerce", "vendere": "commerce", "pagare": "commerce",
    "portare": "commerce",
    # Seeking
    "trovare": "seeking", "cercare": "seeking", "scegliere": "seeking",
    # Instrument
    "suonare": "instrument",
    # Physical
    "aprire": "physical", "chiudere": "physical", "spegnere": "physical",
    "mettere": "physical", "coprire": "physical",
    # Calling
    "chiamare": "calling",
    # Memory
    "ricordare": "memory", "dimenticare": "memory",
    # Change
    "cambiare": "change", "provare": "change", "correggere": "change",
    # Using
    "usare": "using",
    # Places
    "visitare": "places",
    # Waiting
    "aspettare": "waiting",
    # Leaving
    "lasciare": "leaving",
    # Proposing
    "proporre": "proposing",
    # Desire
    "desiderare": "desire", "amare": "desire",
    # Keeping
    "tenere": "keeping",
    # Communication (receiving/sending)
    "ricevere": "text", "spedire": "text",
    # Other transitive
    "prendere": "food", "servire": "food",
    "scoprire": "communication", "offrire": "food",
    "dare": "commerce", "perdere": "seeking",
    "chiedere": "communication", "conoscere": "people",
    "costruire": "physical", "pulire": "physical",
    "unire": "people",
    # passare can be time-related
    "passare": "leaving",
    # Thinking / believing
    "pensare": "communication", "credere": "communication",
    # Sending
    "cominciare": "text",
}


# ---------------------------------------------------------------------------
# Verb semantic categories
# ---------------------------------------------------------------------------

VERB_SEMANTIC_CATEGORY: Dict[str, str] = {
    # movement
    "andare": "movement", "venire": "movement", "arrivare": "movement",
    "partire": "movement", "entrare": "movement", "uscire": "movement",
    "tornare": "movement", "salire": "movement", "scendere": "movement",
    "camminare": "movement", "correre": "movement", "viaggiare": "movement",
    "nuotare": "movement",
    # state
    "essere": "state", "stare": "state", "restare": "state",
    "rimanere": "state", "diventare": "state",
    # mental
    "pensare": "mental", "credere": "mental", "sapere": "mental",
    "capire": "mental", "ricordare": "mental", "dimenticare": "mental",
    "volere": "mental", "preferire": "mental", "desiderare": "mental",
    "potere": "mental", "dovere": "mental", "conoscere": "mental",
    "imparare": "mental",
    # communication
    "dire": "communication", "parlare": "communication",
    "raccontare": "communication", "spiegare": "communication",
    "chiedere": "communication", "rispondere": "communication",
    "chiamare": "communication",
    # action
    "fare": "action", "dare": "action", "prendere": "action",
    "mettere": "action", "portare": "action", "comprare": "action",
    "vendere": "action", "pagare": "action", "usare": "action",
    "preparare": "action", "costruire": "action", "pulire": "action",
    "aprire": "action", "chiudere": "action", "spegnere": "action",
    "coprire": "action", "cambiare": "action", "provare": "action",
    "correggere": "action", "lasciare": "action", "tenere": "action",
    "cercare": "action", "trovare": "action", "passare": "action",
    "servire": "action", "offrire": "action", "proporre": "action",
    "spedire": "action", "unire": "action",
    # food (sub-category of action for object selection)
    "mangiare": "food", "bere": "food", "cucinare": "food",
    # perception
    "vedere": "perception", "guardare": "perception",
    "ascoltare": "perception", "sentire": "perception",
    # creative
    "scrivere": "creative", "leggere": "creative", "cantare": "creative",
    "suonare": "creative", "ballare": "creative", "studiare": "creative",
    # social
    "aiutare": "social", "insegnare": "social", "seguire": "social",
    "visitare": "social", "incontrare": "social",
    # other
    "avere": "action", "abitare": "state", "vivere": "state",
    "lavorare": "action", "giocare": "action",
    "dormire": "state", "nascere": "state", "morire": "state",
    "cadere": "movement", "cominciare": "action", "finire": "action",
    "amare": "mental", "scoprire": "mental", "aspettare": "action",
    "ricevere": "action", "perdere": "action", "scegliere": "mental",
    "guarire": "state",
}

# Categories that allow predicate adjectives (Template G)
ADJECTIVE_VERB_CATEGORIES: Set[str] = {"state"}

# Verbs that specifically allow predicate adjectives beyond pure state verbs
# (essere verbs in passato prossimo can carry a resultative adjective)
ADJECTIVE_PASSATO_VERBS: Set[str] = {
    "arrivare", "tornare", "restare", "rimanere",
}


# ---------------------------------------------------------------------------
# Location objects for movement verbs
# ---------------------------------------------------------------------------

OBJECTS_LOCATION: List[Dict[str, str]] = [
    {"it": "a casa", "en": "home"},
    {"it": "al lavoro", "en": "to work"},
    {"it": "in Italia", "en": "to/in Italy"},
    {"it": "a Roma", "en": "to/in Rome"},
    {"it": "al supermercato", "en": "to the supermarket"},
    {"it": "in ufficio", "en": "to the office"},
    {"it": "in centro", "en": "downtown"},
    {"it": "all'università", "en": "to the university"},
    {"it": "al ristorante", "en": "to the restaurant"},
    {"it": "in chiesa", "en": "to church"},
    {"it": "al cinema", "en": "to the cinema"},
    {"it": "in biblioteca", "en": "to the library"},
    {"it": "al parco", "en": "to the park"},
    {"it": "in ospedale", "en": "to the hospital"},
]

# Abstract objects for mental verbs
# Each entry has bare forms (for direct-object verbs like capire) and
# prepositional forms for verbs that require a/di prepositions.
# Contractions: a+il=al, a+la=alla, a+l'=all', a+i=ai, a+le=alle
#               di+il=del, di+la=della, di+l'=dell', di+i=dei, di+le=delle
OBJECTS_MENTAL: List[Dict[str, str]] = [
    {"it": "la verità", "en": "the truth",
     "a": "alla verità", "di": "della verità"},
    {"it": "il problema", "en": "the problem",
     "a": "al problema", "di": "del problema"},
    {"it": "una soluzione", "en": "a solution",
     "a": "a una soluzione", "di": "di una soluzione"},
    {"it": "la situazione", "en": "the situation",
     "a": "alla situazione", "di": "della situazione"},
    {"it": "la risposta", "en": "the answer",
     "a": "alla risposta", "di": "della risposta"},
    {"it": "il motivo", "en": "the reason",
     "a": "al motivo", "di": "del motivo"},
    {"it": "la differenza", "en": "the difference",
     "a": "alla differenza", "di": "della differenza"},
    {"it": "il futuro", "en": "the future",
     "a": "al futuro", "di": "del futuro"},
    {"it": "il risultato", "en": "the result",
     "a": "al risultato", "di": "del risultato"},
    {"it": "l'esame", "en": "the exam",
     "a": "all'esame", "di": "dell'esame"},
]

# Mental verbs that require a preposition before a noun object.
# Verbs NOT listed here take direct objects (capire il problema, etc.)
# "prep": IT preposition key used to look up contracted form in OBJECTS_MENTAL
# "en_prep": English preposition for the prompt ("about", "in", etc.)
MENTAL_VERB_PREPOSITION: Dict[str, Dict[str, str]] = {
    "pensare": {"prep": "a", "en_prep": "about"},     # pensare a qualcosa
    "credere": {"prep": "a", "en_prep": "in"},         # credere a qualcosa
}

# Mental verbs that take direct objects normally — no preposition needed
# (capire, conoscere, sapere, ricordare, dimenticare, scoprire,
#  scegliere, preferire, desiderare, amare, imparare)


def get_object_for_verb(verb: str) -> Dict[str, str]:
    """Return a semantically plausible object for the given verb.

    Mental verbs that require a preposition (pensare a, credere a)
    return the prepositional form baked into the object string.
    """
    sem = VERB_SEMANTIC_CATEGORY.get(verb)
    # Movement verbs get location objects
    if sem == "movement":
        return random.choice(OBJECTS_LOCATION)
    # Mental verbs get abstract objects, with preposition if needed
    if sem == "mental":
        obj = random.choice(OBJECTS_MENTAL)
        prep_info = MENTAL_VERB_PREPOSITION.get(verb)
        if prep_info:
            prep_key = prep_info["prep"]       # "a" or "di"
            en_prep = prep_info["en_prep"]     # "about" or "in"
            if prep_key in obj:
                return {"it": obj[prep_key], "en": f"{en_prep} {obj['en']}"}
        # Direct object form
        return {"it": obj["it"], "en": obj["en"]}
    # Food verbs
    if sem == "food":
        return random.choice(OBJECTS_BY_CATEGORY["food"])
    # Use existing per-verb category mapping
    category = VERB_OBJECT_CATEGORY.get(verb)
    if category and category in OBJECTS_BY_CATEGORY:
        return random.choice(OBJECTS_BY_CATEGORY[category])
    return random.choice(OBJECTS_DEFAULT)


# Legacy alias for any code that references OBJECTS directly
OBJECTS: List[Dict[str, str]] = OBJECTS_DEFAULT

# ---------------------------------------------------------------------------
# Tense-compatible adverbs
# ---------------------------------------------------------------------------

# Adverbs that work with any tense
ADVERBS_ANY: List[Dict[str, str]] = [
    {"it": "sempre", "en": "always"},
    {"it": "spesso", "en": "often"},
    {"it": "di solito", "en": "usually"},
    {"it": "ogni giorno", "en": "every day"},
    {"it": "a volte", "en": "sometimes"},
    {"it": "bene", "en": "well"},
    {"it": "male", "en": "badly"},
    {"it": "insieme", "en": "together"},
    {"it": "molto", "en": "a lot"},
    {"it": "poco", "en": "a little"},
    {"it": "qui", "en": "here"},
    {"it": "lì", "en": "there"},
    {"it": "subito", "en": "right away"},
]

# Present-tense only
ADVERBS_PRESENT: List[Dict[str, str]] = [
    {"it": "oggi", "en": "today"},
    {"it": "adesso", "en": "now"},
    {"it": "ora", "en": "now"},
]

# Future-compatible (future and present with future meaning)
ADVERBS_FUTURE: List[Dict[str, str]] = [
    {"it": "domani", "en": "tomorrow"},
    {"it": "presto", "en": "soon"},
    {"it": "la settimana prossima", "en": "next week"},
]

# Past-tense only
ADVERBS_PAST: List[Dict[str, str]] = [
    {"it": "ieri", "en": "yesterday"},
    {"it": "stamattina", "en": "this morning"},
    {"it": "la settimana scorsa", "en": "last week"},
]

# Keep legacy flat list for any old code that references it
ADVERBIALS: List[Dict[str, str]] = ADVERBS_ANY + ADVERBS_PRESENT + ADVERBS_FUTURE + ADVERBS_PAST + [
    {"it": "tardi", "en": "late"},
]


def get_adverb_for_tense(tense: str) -> Dict[str, str]:
    """Return a semantically compatible adverb for the given tense."""
    return random.choice(_get_adverb_pool(tense))


# ---------------------------------------------------------------------------
# Location adverbs (simple single-word) — for movement and state verbs
# ---------------------------------------------------------------------------

LOCATION_ADVERBS: List[Dict[str, str]] = [
    {"it": "qui", "en": "here"},
    {"it": "qua", "en": "here"},
    {"it": "lì", "en": "there"},
    {"it": "là", "en": "there"},
    {"it": "lassù", "en": "up there"},
    {"it": "laggiù", "en": "down there"},
    {"it": "vicino", "en": "nearby"},
    {"it": "lontano", "en": "far away"},
    {"it": "fuori", "en": "outside"},
    {"it": "dentro", "en": "inside"},
    {"it": "sopra", "en": "above/upstairs"},
    {"it": "sotto", "en": "below/downstairs"},
    {"it": "davanti", "en": "in front"},
    {"it": "dietro", "en": "behind"},
]

# ---------------------------------------------------------------------------
# Prepositional location phrases — richer location details
# ---------------------------------------------------------------------------

# Prepositional phrases that imply traversal — movement verbs only
PREP_LOCATIONS_MOVEMENT: List[Dict[str, str]] = [
    # attraverso (across/through)
    {"it": "attraverso il parco", "en": "through the park"},
    {"it": "attraverso la città", "en": "through the city"},
    {"it": "attraverso il ponte", "en": "across the bridge"},
    # lungo (along)
    {"it": "lungo il fiume", "en": "along the river"},
    {"it": "lungo la strada", "en": "along the road"},
    {"it": "lungo la costa", "en": "along the coast"},
    # fino a (as far as)
    {"it": "fino alla stazione", "en": "as far as the station"},
    {"it": "fino al mare", "en": "all the way to the sea"},
    {"it": "fino in centro", "en": "all the way to the center"},
]

# Prepositional phrases for static position — movement and state verbs
PREP_LOCATIONS_ANY: List[Dict[str, str]] = [
    # sul/sulla (on)
    {"it": "sul ponte", "en": "over the bridge"},
    {"it": "sulla collina", "en": "on the hill"},
    {"it": "sul marciapiede", "en": "on the sidewalk"},
    {"it": "sul treno", "en": "on the train"},
    {"it": "sull'autobus", "en": "on the bus"},
    # nel/nella (in/into)
    {"it": "nel parco", "en": "in the park"},
    {"it": "nella piazza", "en": "in the square"},
    {"it": "nella foresta", "en": "in the forest"},
    {"it": "nell'ufficio", "en": "in the office"},
    # vicino a (near)
    {"it": "vicino al fiume", "en": "near the river"},
    {"it": "vicino alla stazione", "en": "near the station"},
    {"it": "vicino al mare", "en": "near the sea"},
    {"it": "vicino alla scuola", "en": "near the school"},
    # davanti a (in front of)
    {"it": "davanti alla chiesa", "en": "in front of the church"},
    {"it": "davanti al cinema", "en": "in front of the cinema"},
    {"it": "davanti alla scuola", "en": "in front of the school"},
    # dietro (behind)
    {"it": "dietro la casa", "en": "behind the house"},
    {"it": "dietro l'angolo", "en": "around the corner"},
    {"it": "dietro al negozio", "en": "behind the shop"},
    # in cima a (at the top of)
    {"it": "in cima alla collina", "en": "at the top of the hill"},
    {"it": "in cima alle scale", "en": "at the top of the stairs"},
    # in fondo a (at the bottom/end of)
    {"it": "in fondo alla strada", "en": "at the end of the street"},
    {"it": "in fondo al corridoio", "en": "at the end of the corridor"},
]

# Combined flat list for backward compat
PREPOSITIONAL_LOCATIONS: List[Dict[str, str]] = PREP_LOCATIONS_MOVEMENT + PREP_LOCATIONS_ANY

# Verb categories eligible for location elements
LOCATION_ELIGIBLE_CATEGORIES: Set[str] = {"movement", "state"}


def _pick_location_element(verb: str) -> Optional[Dict[str, str]]:
    """Optionally pick a location adverb or prepositional phrase.

    Returns None most of the time.  For eligible verbs:
    - ~20% chance of a simple location adverb
    - ~30% chance of a prepositional location phrase
    - ~50% nothing (use time adverb / no location)

    Movement verbs get the full pool (traversal + static phrases).
    State verbs only get static position phrases.
    """
    sem = VERB_SEMANTIC_CATEGORY.get(verb, "")
    if sem not in LOCATION_ELIGIBLE_CATEGORIES:
        return None
    r = random.random()
    if r < 0.20:
        return random.choice(LOCATION_ADVERBS)
    elif r < 0.50:
        if sem == "movement":
            return random.choice(PREPOSITIONAL_LOCATIONS)
        else:
            return random.choice(PREP_LOCATIONS_ANY)
    return None

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
# ---------------------------------------------------------------------------
# Gendered noun-phrase subjects (family, social, possessive)
# ---------------------------------------------------------------------------

# Family nouns (with articles)
SUBJECTS_FAMILY: List[Dict[str, Any]] = [
    {"it": "il marito", "en": "the husband", "gender": "m", "number": "s", "verb_subject": "lui"},
    {"it": "la moglie", "en": "the wife", "gender": "f", "number": "s", "verb_subject": "lei"},
    {"it": "il padre", "en": "the father", "gender": "m", "number": "s", "verb_subject": "lui"},
    {"it": "la madre", "en": "the mother", "gender": "f", "number": "s", "verb_subject": "lei"},
    {"it": "il figlio", "en": "the son", "gender": "m", "number": "s", "verb_subject": "lui"},
    {"it": "la figlia", "en": "the daughter", "gender": "f", "number": "s", "verb_subject": "lei"},
    {"it": "il fratello", "en": "the brother", "gender": "m", "number": "s", "verb_subject": "lui"},
    {"it": "la sorella", "en": "the sister", "gender": "f", "number": "s", "verb_subject": "lei"},
    {"it": "il nonno", "en": "the grandfather", "gender": "m", "number": "s", "verb_subject": "lui"},
    {"it": "la nonna", "en": "the grandmother", "gender": "f", "number": "s", "verb_subject": "lei"},
    {"it": "il nipote", "en": "the nephew", "gender": "m", "number": "s", "verb_subject": "lui"},
    {"it": "la nipote", "en": "the niece", "gender": "f", "number": "s", "verb_subject": "lei"},
    {"it": "il cugino", "en": "the cousin (m)", "gender": "m", "number": "s", "verb_subject": "lui"},
    {"it": "la cugina", "en": "the cousin (f)", "gender": "f", "number": "s", "verb_subject": "lei"},
    {"it": "lo zio", "en": "the uncle", "gender": "m", "number": "s", "verb_subject": "lui"},
    {"it": "la zia", "en": "the aunt", "gender": "f", "number": "s", "verb_subject": "lei"},
    {"it": "il cognato", "en": "the brother-in-law", "gender": "m", "number": "s", "verb_subject": "lui"},
    {"it": "la cognata", "en": "the sister-in-law", "gender": "f", "number": "s", "verb_subject": "lei"},
    {"it": "il suocero", "en": "the father-in-law", "gender": "m", "number": "s", "verb_subject": "lui"},
    {"it": "la suocera", "en": "the mother-in-law", "gender": "f", "number": "s", "verb_subject": "lei"},
    {"it": "il genero", "en": "the son-in-law", "gender": "m", "number": "s", "verb_subject": "lui"},
    {"it": "la nuora", "en": "the daughter-in-law", "gender": "f", "number": "s", "verb_subject": "lei"},
    # Plural family
    {"it": "i genitori", "en": "the parents", "gender": "m", "number": "p", "verb_subject": "loro"},
    {"it": "i figli", "en": "the children", "gender": "m", "number": "p", "verb_subject": "loro"},
    {"it": "i fratelli", "en": "the brothers", "gender": "m", "number": "p", "verb_subject": "loro"},
    {"it": "le sorelle", "en": "the sisters", "gender": "f", "number": "p", "verb_subject": "loro"},
    {"it": "i nonni", "en": "the grandparents", "gender": "m", "number": "p", "verb_subject": "loro"},
    {"it": "i cugini", "en": "the cousins", "gender": "m", "number": "p", "verb_subject": "loro"},
]

# Social/professional nouns (with articles)
SUBJECTS_SOCIAL: List[Dict[str, Any]] = [
    {"it": "il capo", "en": "the boss", "gender": "m", "number": "s", "verb_subject": "lui"},
    {"it": "il collega", "en": "the colleague (m)", "gender": "m", "number": "s", "verb_subject": "lui"},
    {"it": "la collega", "en": "the colleague (f)", "gender": "f", "number": "s", "verb_subject": "lei"},
    {"it": "il vicino", "en": "the neighbor (m)", "gender": "m", "number": "s", "verb_subject": "lui"},
    {"it": "la vicina", "en": "the neighbor (f)", "gender": "f", "number": "s", "verb_subject": "lei"},
    {"it": "l'amico", "en": "the friend (m)", "gender": "m", "number": "s", "verb_subject": "lui"},
    {"it": "l'amica", "en": "the friend (f)", "gender": "f", "number": "s", "verb_subject": "lei"},
    {"it": "il compagno", "en": "the partner (m)", "gender": "m", "number": "s", "verb_subject": "lui"},
    {"it": "la compagna", "en": "the partner (f)", "gender": "f", "number": "s", "verb_subject": "lei"},
    {"it": "il ragazzo", "en": "the boyfriend", "gender": "m", "number": "s", "verb_subject": "lui"},
    {"it": "la ragazza", "en": "the girlfriend", "gender": "f", "number": "s", "verb_subject": "lei"},
    {"it": "il medico", "en": "the doctor", "gender": "m", "number": "s", "verb_subject": "lui"},
    {"it": "l'insegnante", "en": "the teacher", "gender": "m", "number": "s", "verb_subject": "lui"},
    {"it": "lo studente", "en": "the student (m)", "gender": "m", "number": "s", "verb_subject": "lui"},
    {"it": "la studentessa", "en": "the student (f)", "gender": "f", "number": "s", "verb_subject": "lei"},
    {"it": "il professore", "en": "the professor (m)", "gender": "m", "number": "s", "verb_subject": "lui"},
    {"it": "la professoressa", "en": "the professor (f)", "gender": "f", "number": "s", "verb_subject": "lei"},
    # Plural social
    {"it": "gli amici", "en": "the friends", "gender": "m", "number": "p", "verb_subject": "loro"},
    {"it": "i colleghi", "en": "the colleagues", "gender": "m", "number": "p", "verb_subject": "loro"},
    {"it": "i vicini", "en": "the neighbors", "gender": "m", "number": "p", "verb_subject": "loro"},
    {"it": "i ragazzi", "en": "the guys", "gender": "m", "number": "p", "verb_subject": "loro"},
    {"it": "le ragazze", "en": "the girls", "gender": "f", "number": "p", "verb_subject": "loro"},
]

# Possessive variants
# Italian drops the article with singular unmodified family nouns:
#   mio padre (NOT il mio padre), mia sorella (NOT la mia sorella)
# Plural always keeps the article: i miei genitori
# Non-family always keeps the article: il mio capo, il mio amico
SUBJECTS_POSSESSIVE: List[Dict[str, Any]] = [
    # Singular family — no article
    {"it": "mio marito", "en": "my husband", "gender": "m", "number": "s", "verb_subject": "lui"},
    {"it": "mia moglie", "en": "my wife", "gender": "f", "number": "s", "verb_subject": "lei"},
    {"it": "mio padre", "en": "my father", "gender": "m", "number": "s", "verb_subject": "lui"},
    {"it": "mia madre", "en": "my mother", "gender": "f", "number": "s", "verb_subject": "lei"},
    {"it": "mio figlio", "en": "my son", "gender": "m", "number": "s", "verb_subject": "lui"},
    {"it": "mia figlia", "en": "my daughter", "gender": "f", "number": "s", "verb_subject": "lei"},
    {"it": "mio fratello", "en": "my brother", "gender": "m", "number": "s", "verb_subject": "lui"},
    {"it": "mia sorella", "en": "my sister", "gender": "f", "number": "s", "verb_subject": "lei"},
    {"it": "mio nonno", "en": "my grandfather", "gender": "m", "number": "s", "verb_subject": "lui"},
    {"it": "mia nonna", "en": "my grandmother", "gender": "f", "number": "s", "verb_subject": "lei"},
    {"it": "mio cugino", "en": "my cousin (m)", "gender": "m", "number": "s", "verb_subject": "lui"},
    {"it": "mia cugina", "en": "my cousin (f)", "gender": "f", "number": "s", "verb_subject": "lei"},
    {"it": "mio zio", "en": "my uncle", "gender": "m", "number": "s", "verb_subject": "lui"},
    {"it": "mia zia", "en": "my aunt", "gender": "f", "number": "s", "verb_subject": "lei"},
    # Plural family — keeps article
    {"it": "i miei genitori", "en": "my parents", "gender": "m", "number": "p", "verb_subject": "loro"},
    {"it": "i miei figli", "en": "my children", "gender": "m", "number": "p", "verb_subject": "loro"},
    {"it": "i miei fratelli", "en": "my siblings", "gender": "m", "number": "p", "verb_subject": "loro"},
    # Non-family — keeps article
    {"it": "il mio capo", "en": "my boss", "gender": "m", "number": "s", "verb_subject": "lui"},
    {"it": "il mio amico", "en": "my friend (m)", "gender": "m", "number": "s", "verb_subject": "lui"},
    {"it": "la mia amica", "en": "my friend (f)", "gender": "f", "number": "s", "verb_subject": "lei"},
    {"it": "il mio collega", "en": "my colleague (m)", "gender": "m", "number": "s", "verb_subject": "lui"},
    {"it": "il mio vicino", "en": "my neighbor (m)", "gender": "m", "number": "s", "verb_subject": "lui"},
    {"it": "la mia vicina", "en": "my neighbor (f)", "gender": "f", "number": "s", "verb_subject": "lei"},
]


def _pick_gendered_subject() -> Dict[str, Any]:
    """Pick a gendered noun-phrase subject with weighted distribution.

    60% family, 20% social/professional, 20% possessive.
    """
    r = random.random()
    if r < 0.60:
        return random.choice(SUBJECTS_FAMILY)
    elif r < 0.80:
        return random.choice(SUBJECTS_SOCIAL)
    else:
        return random.choice(SUBJECTS_POSSESSIVE)


# Flat list for backward compat
GENDERED_SUBJECTS: List[Dict[str, Any]] = SUBJECTS_FAMILY + SUBJECTS_SOCIAL + SUBJECTS_POSSESSIVE

# Verbs that work for agreement drills (Template G with predicate adjective)
# ONLY state verbs and a few essere-verbs that take resultative adjectives in passato prossimo
AGREEMENT_VERBS_STATE: List[str] = [
    "essere", "stare", "restare", "rimanere", "diventare",
]
AGREEMENT_VERBS_RESULTATIVE: List[str] = [
    "arrivare", "tornare",
]
# Combined list for backward compat and template selection
AGREEMENT_VERBS: List[str] = AGREEMENT_VERBS_STATE + AGREEMENT_VERBS_RESULTATIVE

# ---------------------------------------------------------------------------
# Focus modes
# ---------------------------------------------------------------------------

FOCUS_MODES: List[str] = ["all", "pronouns", "agreement", "conjugation-endings"]

# ---------------------------------------------------------------------------
# Reflexive verbs (Template I)
# ---------------------------------------------------------------------------

REFLEXIVE_PRONOUNS: Dict[str, str] = {
    "io": "mi", "tu": "ti", "lui": "si", "lei": "si",
    "noi": "ci", "voi": "vi", "loro": "si",
}

REFLEXIVE_VERBS: List[Dict[str, Any]] = [
    {"infinitive": "alzarsi", "stem_verb": "alzare", "en": "to get up", "group": "are"},
    {"infinitive": "addormentarsi", "stem_verb": "addormentare", "en": "to fall asleep", "group": "are"},
    {"infinitive": "svegliarsi", "stem_verb": "svegliare", "en": "to wake up", "group": "are"},
    {"infinitive": "lavarsi", "stem_verb": "lavare", "en": "to wash oneself", "group": "are"},
    {"infinitive": "vestirsi", "stem_verb": "vestire", "en": "to get dressed", "group": "ire"},
    {"infinitive": "spogliarsi", "stem_verb": "spogliare", "en": "to get undressed", "group": "are"},
    {"infinitive": "pettinarsi", "stem_verb": "pettinare", "en": "to comb one's hair", "group": "are"},
    {"infinitive": "truccarsi", "stem_verb": "truccare", "en": "to put on makeup", "group": "are"},
    {"infinitive": "radersi", "stem_verb": "radere", "en": "to shave", "group": "ere",
     "pp_irreg": "raso"},
    {"infinitive": "prepararsi", "stem_verb": "preparare", "en": "to get ready", "group": "are"},
    {"infinitive": "sedersi", "stem_verb": "sedere", "en": "to sit down", "group": "ere",
     "pres_irreg": ["siedo", "siedi", "siede", "sediamo", "sedete", "siedono"]},
    {"infinitive": "fermarsi", "stem_verb": "fermare", "en": "to stop", "group": "are"},
    {"infinitive": "avvicinarsi", "stem_verb": "avvicinare", "en": "to approach", "group": "are"},
    {"infinitive": "allontanarsi", "stem_verb": "allontanare", "en": "to move away", "group": "are"},
    {"infinitive": "incontrarsi", "stem_verb": "incontrare", "en": "to meet each other", "group": "are"},
    {"infinitive": "vedersi", "stem_verb": "vedere", "en": "to see each other", "group": "ere"},
    {"infinitive": "parlarsi", "stem_verb": "parlare", "en": "to talk to each other", "group": "are"},
    {"infinitive": "sentirsi", "stem_verb": "sentire", "en": "to feel", "group": "ire"},
    {"infinitive": "chiamarsi", "stem_verb": "chiamare", "en": "to be called", "group": "are"},
    {"infinitive": "annoiarsi", "stem_verb": "annoiare", "en": "to get bored", "group": "are"},
    {"infinitive": "divertirsi", "stem_verb": "divertire", "en": "to enjoy oneself", "group": "ire"},
    {"infinitive": "arrabbiarsi", "stem_verb": "arrabbiare", "en": "to get angry", "group": "are"},
    {"infinitive": "preoccuparsi", "stem_verb": "preoccupare", "en": "to worry", "group": "are"},
    {"infinitive": "rilassarsi", "stem_verb": "rilassare", "en": "to relax", "group": "are"},
    {"infinitive": "riposarsi", "stem_verb": "riposare", "en": "to rest", "group": "are"},
    {"infinitive": "sbagliarsi", "stem_verb": "sbagliare", "en": "to be mistaken", "group": "are"},
    {"infinitive": "ricordarsi", "stem_verb": "ricordare", "en": "to remember", "group": "are"},
    {"infinitive": "dimenticarsi", "stem_verb": "dimenticare", "en": "to forget", "group": "are"},
]

REFLEXIVE_VERB_MAP: Dict[str, Dict[str, Any]] = {v["infinitive"]: v for v in REFLEXIVE_VERBS}

# Reflexive verbs that are reciprocal (use plural subjects only)
RECIPROCAL_REFLEXIVES: Set[str] = {
    "incontrarsi", "vedersi", "parlarsi",
}


def conjugate_reflexive(
    reflex_verb: Dict[str, Any], tense: str, subject: str, gender_io_tu: str = "m"
) -> str:
    """Conjugate a reflexive verb: pronoun + verb form.

    Reflexive verbs always use essere in passato prossimo with agreement.
    """
    pron = REFLEXIVE_PRONOUNS[subject]
    stem_verb = reflex_verb["stem_verb"]

    if tense == "passato_prossimo":
        # Always essere + agreed participle
        aux = conjugate_presente("essere", subject)
        if "pp_irreg" in reflex_verb:
            pp = reflex_verb["pp_irreg"]
        elif stem_verb in IRREGULAR_PAST_PARTICIPLES:
            pp = IRREGULAR_PAST_PARTICIPLES[stem_verb]
        else:
            pp = _past_participle(stem_verb)
        pp = _agree_participle(pp, subject, gender_io_tu)
        return f"{pron} {aux} {pp}"

    if tense == "presente":
        if "pres_irreg" in reflex_verb:
            idx = SUBJECT_INDEX[subject]
            six_idx = {0: 0, 1: 1, 2: 2, 3: 2, 4: 3, 5: 4, 6: 5}[idx]
            form = reflex_verb["pres_irreg"][six_idx]
        else:
            form = conjugate_presente(stem_verb, subject)
        return f"{pron} {form}"

    if tense == "imperfetto":
        form = conjugate_imperfetto(stem_verb, subject)
        return f"{pron} {form}"

    if tense == "futuro":
        form = conjugate_futuro(stem_verb, subject)
        return f"{pron} {form}"

    if tense == "condizionale":
        form = conjugate_condizionale(stem_verb, subject)
        return f"{pron} {form}"

    return f"{pron} {stem_verb}"


# Optional complements for reflexive verbs
REFLEXIVE_COMPLEMENTS: Dict[str, List[Dict[str, str]]] = {
    "alzarsi": [
        {"it": "presto", "en": "early"}, {"it": "tardi", "en": "late"},
        {"it": "alle sei", "en": "at six"},
    ],
    "addormentarsi": [
        {"it": "sul divano", "en": "on the couch"}, {"it": "tardi", "en": "late"},
        {"it": "subito", "en": "right away"},
    ],
    "svegliarsi": [
        {"it": "presto", "en": "early"}, {"it": "tardi", "en": "late"},
        {"it": "alle sette", "en": "at seven"},
    ],
    "prepararsi": [
        {"it": "in fretta", "en": "in a hurry"}, {"it": "lentamente", "en": "slowly"},
    ],
    "fermarsi": [
        {"it": "al bar", "en": "at the bar"}, {"it": "un momento", "en": "for a moment"},
    ],
    "rilassarsi": [
        {"it": "a casa", "en": "at home"}, {"it": "al parco", "en": "at the park"},
    ],
    "riposarsi": [
        {"it": "dopo pranzo", "en": "after lunch"}, {"it": "un po'", "en": "a bit"},
    ],
    "incontrarsi": [
        {"it": "al bar", "en": "at the bar"}, {"it": "in centro", "en": "downtown"},
    ],
    "avvicinarsi": [
        {"it": "lentamente", "en": "slowly"}, {"it": "in silenzio", "en": "quietly"},
    ],
}

# ---------------------------------------------------------------------------
# Question words (Template H)
# ---------------------------------------------------------------------------

QUESTION_WORDS: List[Dict[str, Any]] = [
    # High-frequency (higher weight)
    {"it": "dove", "en": "where", "weight": 15, "needs_subj": True, "verb_filter": None},
    {"it": "quando", "en": "when", "weight": 12, "needs_subj": True, "verb_filter": None},
    {"it": "chi", "en": "who", "weight": 15, "needs_subj": False, "verb_filter": None},
    {"it": "cosa", "en": "what", "weight": 15, "needs_subj": True, "verb_filter": None},
    {"it": "come", "en": "how", "weight": 8, "needs_subj": True, "verb_filter": None},
    {"it": "perché", "en": "why", "weight": 8, "needs_subj": True, "verb_filter": None},
    # Lower frequency
    {"it": "quale", "en": "which", "weight": 5, "needs_subj": True,
     "verb_filter": ["leggere", "comprare", "guardare", "ascoltare", "scegliere",
                      "prendere", "preferire", "cucinare", "preparare", "studiare"],
     "needs_noun": True},
    {"it": "a chi", "en": "to whom", "weight": 5, "needs_subj": True,
     "verb_filter": ["dare", "dire", "spiegare", "raccontare", "portare", "mandare",
                      "scrivere", "insegnare", "chiedere"]},
    {"it": "con chi", "en": "with whom", "weight": 5, "needs_subj": True,
     "verb_filter": ["parlare", "lavorare", "giocare", "viaggiare", "studiare",
                      "uscire", "camminare", "vivere"]},
    {"it": "da dove", "en": "from where", "weight": 4, "needs_subj": True,
     "verb_filter": ["venire", "arrivare", "tornare", "partire"]},
    {"it": "quante ore", "en": "how many hours", "weight": 3, "needs_subj": True,
     "verb_filter": ["lavorare", "studiare", "dormire", "giocare"]},
    {"it": "per quanto tempo", "en": "for how long", "weight": 3, "needs_subj": True,
     "verb_filter": ["restare", "rimanere", "aspettare", "studiare", "lavorare",
                      "dormire", "vivere"]},
]

# Nouns for "quale" questions
QUALE_NOUNS: List[Dict[str, str]] = [
    {"it": "libro", "en": "book"}, {"it": "film", "en": "film"},
    {"it": "canzone", "en": "song"}, {"it": "ristorante", "en": "restaurant"},
    {"it": "strada", "en": "road"}, {"it": "treno", "en": "train"},
]

# ---------------------------------------------------------------------------
# Object-transfer verbs and transferable objects (expanded F / Template J)
# ---------------------------------------------------------------------------

TRANSFER_VERBS: List[Dict[str, Any]] = [
    {"infinitive": "dare", "en": "to give", "en_past": "gave"},
    {"infinitive": "mandare", "en": "to send", "en_past": "sent"},
    {"infinitive": "portare", "en": "to bring", "en_past": "brought"},
    {"infinitive": "mostrare", "en": "to show", "en_past": "showed"},
    {"infinitive": "spiegare", "en": "to explain", "en_past": "explained"},
    {"infinitive": "regalare", "en": "to give as a gift", "en_past": "gave as a gift"},
    {"infinitive": "prestare", "en": "to lend", "en_past": "lent"},
    {"infinitive": "restituire", "en": "to return", "en_past": "returned"},
    {"infinitive": "dire", "en": "to tell", "en_past": "told"},
    {"infinitive": "chiedere", "en": "to ask for", "en_past": "asked for"},
    {"infinitive": "comprare", "en": "to buy", "en_past": "bought"},
    {"infinitive": "cucinare", "en": "to cook", "en_past": "cooked"},
    {"infinitive": "leggere", "en": "to read", "en_past": "read"},
    {"infinitive": "scrivere", "en": "to write", "en_past": "wrote"},
]

TRANSFER_VERB_MAP: Dict[str, Dict[str, Any]] = {v["infinitive"]: v for v in TRANSFER_VERBS}

# Objects that can be transferred (with gender/number for pronoun selection)
TRANSFER_OBJECTS: List[Dict[str, str]] = [
    {"it": "il libro", "en": "the book", "gender": "m", "number": "s", "pron": "lo"},
    {"it": "la chiave", "en": "the key", "gender": "f", "number": "s", "pron": "la"},
    {"it": "i soldi", "en": "the money", "gender": "m", "number": "p", "pron": "li"},
    {"it": "le foto", "en": "the photos", "gender": "f", "number": "p", "pron": "le"},
    {"it": "il regalo", "en": "the gift", "gender": "m", "number": "s", "pron": "lo"},
    {"it": "la lettera", "en": "the letter", "gender": "f", "number": "s", "pron": "la"},
    {"it": "il messaggio", "en": "the message", "gender": "m", "number": "s", "pron": "lo"},
    {"it": "la ricetta", "en": "the recipe", "gender": "f", "number": "s", "pron": "la"},
    {"it": "i documenti", "en": "the documents", "gender": "m", "number": "p", "pron": "li"},
    {"it": "la torta", "en": "the cake", "gender": "f", "number": "s", "pron": "la"},
]

# Recipients for indirect pronoun context in English
TRANSFER_RECIPIENTS: List[Dict[str, str]] = [
    {"indirect_it": "mi", "en": "to me", "en_short": "me"},
    {"indirect_it": "ti", "en": "to you", "en_short": "you"},
    {"indirect_it": "gli", "en": "to him", "en_short": "him"},
    {"indirect_it": "le_ind", "en": "to her", "en_short": "her"},
    {"indirect_it": "ci", "en": "to us", "en_short": "us"},
    {"indirect_it": "vi", "en": "to you all", "en_short": "you all"},
    {"indirect_it": "gli", "en": "to them", "en_short": "them"},
]

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
        # Handle -ciare/-giare: drop stem's trailing i before endings that start with i
        # mangiare: stem "mangi" + "i" → "mangi" (not "mangii")
        # mangiare: stem "mangi" + "iamo" → "mangiamo" (not "mangiiamo")
        if verb.endswith("ciare") or verb.endswith("giare"):
            ending = endings[six_idx]
            if ending.startswith("i"):
                return stem[:-1] + ending  # drop the i from stem
            return stem + ending
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

# ---------------------------------------------------------------------------
# Temporal coherence: classify frames and adverbs as habitual vs specific
# ---------------------------------------------------------------------------

# Habitual discourse frames (imply repeated/general action)
HABITUAL_FRAMES: Set[str] = {
    "Di solito,", "A volte,", "Ogni giorno,",
}

# Specific discourse frames (imply a particular occasion)
SPECIFIC_FRAMES: Set[str] = {
    "Purtroppo,", "Fortunatamente,", "In realtà,",
    "Secondo me,", "Secondo lui,", "Secondo lei,", "Secondo noi,",
    "A mio parere,", "Per quanto mi riguarda,",
    "Probabilmente,", "Forse,", "Sinceramente,",
}

# Habitual adverbs (imply repeated/general action)
HABITUAL_ADVERBS: Set[str] = {
    "sempre", "spesso", "a volte", "ogni giorno", "di solito",
}

# Specific-time adverbs (imply a particular moment)
SPECIFIC_ADVERBS: Set[str] = {
    "domani", "ieri", "oggi", "stamattina", "adesso", "ora",
    "la settimana scorsa", "la settimana prossima", "presto", "tardi",
}

# Manner adverbs that are neutral (compatible with anything)
NEUTRAL_ADVERBS: Set[str] = {
    "bene", "male", "insieme", "molto", "poco", "qui", "lì", "subito",
}


def _classify_frame(frame: Dict[str, str]) -> str:
    """Classify a frame as 'habitual', 'specific', or 'neutral'."""
    it = frame.get("it", "")
    if it in HABITUAL_FRAMES:
        return "habitual"
    if it in SPECIFIC_FRAMES:
        return "specific"
    return "neutral"


def _classify_adverb(adv: Dict[str, str]) -> str:
    """Classify an adverb as 'habitual', 'specific', or 'neutral'."""
    it = adv.get("it", "")
    if it in HABITUAL_ADVERBS:
        return "habitual"
    if it in SPECIFIC_ADVERBS:
        return "specific"
    return "neutral"


def _get_adverb_pool(tense: str) -> List[Dict[str, str]]:
    """Get the full pool of tense-compatible adverbs."""
    pool = list(ADVERBS_ANY)
    if tense == "presente":
        pool += ADVERBS_PRESENT
    elif tense == "futuro":
        pool += ADVERBS_FUTURE
    elif tense == "condizionale":
        pool += ADVERBS_FUTURE
    elif tense in ("passato_prossimo", "imperfetto"):
        pool += ADVERBS_PAST
    return pool


def _get_compatible_adverb(tense: str, frame_class: str) -> Optional[Dict[str, str]]:
    """Pick an adverb compatible with both tense and frame temporal class.

    Returns None when the frame is habitual (Di solito, A volte, Ogni giorno)
    because the frame itself already provides the frequency context — adding
    an adverb would create redundant sentences like "Di solito ... di solito".
    """
    if frame_class == "habitual":
        return None
    pool = _get_adverb_pool(tense)
    compatible = []
    for adv in pool:
        ac = _classify_adverb(adv)
        if frame_class == "specific" and ac == "habitual":
            continue  # No habitual adverb with specific frame
        compatible.append(adv)
    if not compatible:
        compatible = [a for a in ADVERBS_ANY if a["it"] in NEUTRAL_ADVERBS]
    return random.choice(compatible) if compatible else {"it": "bene", "en": "well"}


def _pick_frame(difficulty_unlocked: bool) -> Dict[str, str]:
    """Pick a discourse frame. Always returns a frame (never empty)."""
    if not difficulty_unlocked:
        simple = [
            {"it": "Secondo me,", "en": "In my opinion,"},
            {"it": "Di solito,", "en": "Usually,"},
            {"it": "In realtà,", "en": "Actually,"},
            {"it": "Ogni giorno,", "en": "Every day,"},
            {"it": "A volte,", "en": "Sometimes,"},
        ]
        return random.choice(simple)
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
    """Does this verb typically take a direct/indirect object (not location)?

    Movement verbs DO get objects (locations), but that's handled separately.
    Modal verbs (potere/dovere/volere) take infinitives, not noun objects.
    """
    sem = VERB_SEMANTIC_CATEGORY.get(verb, "")
    # Movement verbs get location objects — handled via get_object_for_verb
    if sem == "movement":
        return True
    # Modal verbs take infinitives, not noun objects
    if verb in ("potere", "dovere", "volere"):
        return False
    # State verbs and intransitive verbs don't take objects
    no_obj = {
        "essere", "stare", "restare", "rimanere", "diventare",
        "dormire", "nuotare", "ballare", "cantare", "lavorare",
        "abitare", "vivere", "nascere", "morire", "guarire",
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
        # Location element (simple adverb or prepositional phrase)
        location: Optional[Dict[str, str]] = None,
        # Template H extras (questions)
        question_word: Optional[Dict[str, Any]] = None,
        quale_noun: Optional[Dict[str, str]] = None,
        # Template I extras (reflexive)
        reflexive_verb: Optional[Dict[str, Any]] = None,
        reflexive_complement: Optional[Dict[str, str]] = None,
        reflexive_modal: Optional[str] = None,
        # Template J extras (object transfer with combined pronouns)
        transfer_object: Optional[Dict[str, str]] = None,
        transfer_recipient: Optional[Dict[str, str]] = None,
        # Alternate accepted answers
        alt_italian: Optional[str] = None,
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
        self.location = location
        self.question_word = question_word
        self.quale_noun = quale_noun
        self.reflexive_verb = reflexive_verb
        self.reflexive_complement = reflexive_complement
        self.reflexive_modal = reflexive_modal
        self.transfer_object = transfer_object
        self.transfer_recipient = transfer_recipient
        self.alt_italian = alt_italian

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
        """Build the expected Italian sentence.

        Italian is pro-drop: subject pronouns (io, tu, lui, lei, noi, voi, loro)
        are omitted in the model answer for templates A/B/C/E/F. They are kept
        for template D (after "che") and G (noun-phrase subjects).
        """
        parts: List[str] = []
        if self.frame["it"]:
            parts.append(self.frame["it"])

        if self.template == "A":
            # Frame + verb + object + location/adverb  (subject pronoun dropped)
            parts.append(conjugate(self.verb, self.tense, self.subject, self.gender_io_tu))
            if self.obj:
                parts.append(self.obj["it"])
            if self.location:
                parts.append(self.location["it"])
            elif self.adv:
                parts.append(self.adv["it"])

        elif self.template == "B":
            # Frame + modal(tense) + infinitive + object/location  (subject pronoun dropped)
            parts.append(conjugate(self.modal or "potere", self.tense, self.subject, self.gender_io_tu))
            parts.append(self.verb)  # infinitive
            if self.obj:
                parts.append(self.obj["it"])
            if self.location:
                parts.append(self.location["it"])

        elif self.template == "C":
            # Frame + volere(tense) + infinitive + object/location  (subject pronoun dropped)
            parts.append(conjugate("volere", self.tense, self.subject, self.gender_io_tu))
            parts.append(self.verb)  # infinitive
            if self.obj:
                parts.append(self.obj["it"])
            if self.location:
                parts.append(self.location["it"])

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
            # Pronoun placement template (subject pronoun dropped)
            pron = self._get_pronoun_it()
            if self.f_modal:
                # Pre-modal form: pronoun + modal + infinitive
                parts.append(pron)
                parts.append(conjugate(self.f_modal, self.tense, self.subject, self.gender_io_tu))
                parts.append(self.verb)
            else:
                # Simple: pronoun before conjugated verb
                parts.append(pron)
                parts.append(conjugate(self.verb, self.tense, self.subject, self.gender_io_tu))
            if self.adv:
                parts.append(self.adv["it"])

        elif self.template == "G":
            # Agreement template: gendered subject + essere verb + adjective + adverb
            gs = self.gendered_subject
            adj = self.adjective
            if gs and adj:
                vs = gs["verb_subject"]  # lui/lei/loro for conjugation
                verb_form = conjugate(self.verb, self.tense, vs, self.gender_io_tu)
                adj_form = _get_adjective_form(adj, gs["gender"], gs["number"])
                parts.append(gs["it"])
                if self.tense == "passato_prossimo":
                    uses_essere = self.verb in ESSERE_VERBS or self.verb == "essere"
                    aux_form = conjugate_presente("essere" if uses_essere else "avere", vs)
                    pp = _past_participle(self.verb)
                    if uses_essere:
                        pp = _agree_participle_gendered(pp, gs["gender"], gs["number"])
                    parts.append(aux_form)
                    parts.append(pp)
                else:
                    parts.append(verb_form)
                parts.append(adj_form)
                if self.location:
                    parts.append(self.location["it"])
                elif self.adv:
                    parts.append(self.adv["it"])

        elif self.template == "H":
            # Question: question_word + verb + subject + object/complement?
            qw = self.question_word
            if qw:
                qw_it = qw["it"].capitalize()
                if self.quale_noun:
                    qw_it = f"{qw_it} {self.quale_noun['it']}"
                parts.append(qw_it)
                # Conjugated verb
                parts.append(conjugate(self.verb, self.tense, self.subject, self.gender_io_tu))
                # Subject noun phrase (only for 3rd person with gendered_subject)
                if self.gendered_subject:
                    parts.append(self.gendered_subject["it"])
                if self.obj:
                    parts.append(self.obj["it"])
                if self.adv:
                    parts.append(self.adv["it"])
                # Add question mark to last part
                if parts:
                    parts[-1] = parts[-1] + "?"

        elif self.template == "I":
            # Reflexive: frame + reflexive_conjugation + complement
            rv = self.reflexive_verb
            if rv:
                if self.reflexive_modal:
                    # Pre-modal form: pronoun + modal + infinitive(si)
                    pron = REFLEXIVE_PRONOUNS[self.subject]
                    modal_form = conjugate(self.reflexive_modal, self.tense,
                                           self.subject, self.gender_io_tu)
                    parts.append(pron)
                    parts.append(modal_form)
                    parts.append(rv["stem_verb"] + "si" if not rv["infinitive"].endswith("si") else rv["infinitive"])
                elif self.gendered_subject:
                    # Noun-phrase subject
                    gs = self.gendered_subject
                    parts.append(gs["it"])
                    form = conjugate_reflexive(rv, self.tense, gs["verb_subject"],
                                               self.gender_io_tu)
                    parts.append(form)
                else:
                    form = conjugate_reflexive(rv, self.tense, self.subject,
                                               self.gender_io_tu)
                    parts.append(form)
                if self.reflexive_complement:
                    parts.append(self.reflexive_complement["it"])
                if self.adv:
                    parts.append(self.adv["it"])

        elif self.template == "J":
            # Object transfer with combined pronouns
            # Frame + combined_pronoun + verb + adv
            if self.transfer_recipient and self.transfer_object:
                ind_key = self.transfer_recipient["indirect_it"]
                dir_pron = self.transfer_object["pron"]
                # Use real indirect key (le_ind → gli for lookup)
                actual_ind = "le" if ind_key == "le_ind" else ind_key
                combined = _get_combined_pronoun(ind_key, dir_pron)
                parts.append(combined)
                parts.append(conjugate(self.verb, self.tense, self.subject,
                                       self.gender_io_tu))
                if self.adv:
                    parts.append(self.adv["it"])
                # No question mark for J

        return " ".join(parts)

    def build_english(self) -> str:
        """Build the English prompt."""
        verb_info = VERB_MAP.get(self.verb, {"en": self.verb})
        parts: List[str] = []
        if self.frame["en"]:
            parts.append(self.frame["en"])

        obj_en = self.obj["en"] if self.obj else ""
        # Location element takes the adverb slot in English prompt
        if self.location:
            adv_en = self.location["en"]
        elif self.adv:
            adv_en = self.adv["en"]
        else:
            adv_en = ""

        if self.template == "A":
            parts.append(english_conjugation(verb_info, self.tense, self.subject, obj_en, adv_en))
        elif self.template == "B":
            modal_info = VERB_MAP.get(self.modal or "potere", {"en": "to be able to"})
            modal_en = english_conjugation(modal_info, self.tense, self.subject)
            s = f"{modal_en} {verb_info['en'].replace('to ', '')}"
            if obj_en:
                s += f" {obj_en}"
            if self.location:
                s += f" {self.location['en']}"
            parts.append(s)
        elif self.template == "C":
            subj = SUBJECT_EN[self.subject]
            want_form = english_conjugation(VERB_MAP["volere"], self.tense, self.subject)
            bare = verb_info["en"].replace("to ", "")
            s = f"{want_form} {bare}"
            if obj_en:
                s += f" {obj_en}"
            if self.location:
                s += f" {self.location['en']}"
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
            adv_en_f = self.adv["en"] if self.adv else ""
            if self.f_modal:
                modal_info = VERB_MAP.get(self.f_modal, {"en": "to be able to"})
                modal_en = english_conjugation(modal_info, self.tense, self.subject)
                s = f"{modal_en} {bare} {pron_en}"
                if adv_en_f:
                    s += f" {adv_en_f}"
                parts.append(s)
            else:
                verb_en = english_conjugation(verb_info, self.tense, self.subject)
                s = f"{verb_en} {pron_en}"
                if adv_en_f:
                    s += f" {adv_en_f}"
                parts.append(s)
            parts.append("[use Italian pronoun placement]")

        elif self.template == "G":
            gs = self.gendered_subject
            adj = self.adjective
            if gs and adj:
                bare = verb_info["en"].replace("to ", "")
                subj_en = gs["en"]
                adj_en = adj["en"]
                adv_en_g = self.location["en"] if self.location else (self.adv["en"] if self.adv else "")
                vs = gs["verb_subject"]
                verb_en = english_conjugation(verb_info, self.tense, vs)
                # Replace the subject pronoun with the noun phrase
                for pron in ("he", "she", "they", "I", "you", "we", "you all"):
                    if verb_en.startswith(pron + " "):
                        verb_en = verb_en[len(pron) + 1:]
                        break
                s = f"{subj_en} {verb_en} {adj_en}"
                if adv_en_g:
                    s += f" {adv_en_g}"
                parts.append(s)

        elif self.template == "H":
            # Question form English prompt
            qw = self.question_word
            if qw:
                qw_en = qw["en"].capitalize()
                if self.quale_noun:
                    qw_en = f"{qw_en} {self.quale_noun['en']}"
                bare = verb_info["en"].replace("to ", "")
                if self.gendered_subject:
                    subj_en = self.gendered_subject["en"]
                else:
                    subj_en = SUBJECT_EN[self.subject]
                # Build the auxiliary / tense portion
                if qw["it"] == "chi":
                    # "chi" is the subject — use 3rd person statement form
                    verb_en_h = english_conjugation(verb_info, self.tense, "lui", obj_en, adv_en)
                    # Strip "he " prefix
                    if verb_en_h.startswith("he "):
                        verb_en_h = verb_en_h[3:]
                    s = f"{qw_en} {verb_en_h}?"
                else:
                    # "does/did/will + subject + bare verb" question form
                    extras = ""
                    if obj_en:
                        extras += f" {obj_en}"
                    if adv_en:
                        extras += f" {adv_en}"
                    if self.tense == "presente":
                        aux = "does" if self.subject in ("lui", "lei") else "do"
                        s = f"{qw_en} {aux} {subj_en} {bare}{extras}?"
                    elif self.tense in ("passato_prossimo", "imperfetto"):
                        s = f"{qw_en} did {subj_en} {bare}{extras}?"
                    elif self.tense == "futuro":
                        s = f"{qw_en} will {subj_en} {bare}{extras}?"
                    elif self.tense == "condizionale":
                        s = f"{qw_en} would {subj_en} {bare}{extras}?"
                    else:
                        s = f"{qw_en} does {subj_en} {bare}{extras}?"
                parts.append(s)

        elif self.template == "I":
            # Reflexive English prompt
            rv = self.reflexive_verb
            if rv:
                bare = rv["en"].replace("to ", "")
                subj_en = SUBJECT_EN[self.subject]
                if self.gendered_subject:
                    subj_en = self.gendered_subject["en"]
                comp_en = self.reflexive_complement["en"] if self.reflexive_complement else ""
                adv_en_i = self.adv["en"] if self.adv else ""
                if self.reflexive_modal:
                    modal_info = VERB_MAP.get(self.reflexive_modal, {"en": "to be able to"})
                    modal_en = english_conjugation(modal_info, self.tense, self.subject)
                    s = f"{modal_en} {bare}"
                else:
                    # Simple tense-based English
                    third = self.subject in ("lui", "lei")
                    if self.tense == "presente":
                        if third:
                            # Simple s_form for first word
                            words = bare.split()
                            w = words[0]
                            if w.endswith("ch") or w.endswith("sh") or w.endswith("ss") or w.endswith("x") or w.endswith("o"):
                                vf = w + "es"
                            elif w.endswith("e"):
                                vf = w + "s"
                            elif w.endswith("y") and len(w) > 1 and w[-2] not in "aeiou":
                                vf = w[:-1] + "ies"
                            else:
                                vf = w + "s"
                            words[0] = vf
                            s = f"{subj_en} {' '.join(words)}"
                        else:
                            s = f"{subj_en} {bare}"
                    elif self.tense == "passato_prossimo":
                        # Use simple past approximation
                        if bare in ("get up", "wake up"):
                            s = f"{subj_en} got up" if bare == "get up" else f"{subj_en} woke up"
                        elif bare in ("get dressed",):
                            s = f"{subj_en} got dressed"
                        elif bare in ("get undressed",):
                            s = f"{subj_en} got undressed"
                        elif bare in ("get bored",):
                            s = f"{subj_en} got bored"
                        elif bare in ("get angry",):
                            s = f"{subj_en} got angry"
                        elif bare in ("get ready",):
                            s = f"{subj_en} got ready"
                        elif bare in ("sit down",):
                            s = f"{subj_en} sat down"
                        elif bare in ("fall asleep",):
                            s = f"{subj_en} fell asleep"
                        elif bare in ("be called",):
                            was = "was" if self.subject in ("io", "lui", "lei") else "were"
                            s = f"{subj_en} {was} called"
                        elif bare in ("be mistaken",):
                            was = "was" if self.subject in ("io", "lui", "lei") else "were"
                            s = f"{subj_en} {was} mistaken"
                        elif bare in ("see each other",):
                            s = f"{subj_en} saw each other"
                        elif bare in ("meet each other",):
                            s = f"{subj_en} met each other"
                        elif bare in ("feel",):
                            s = f"{subj_en} felt"
                        else:
                            if bare.endswith("e"):
                                past = bare + "d"
                            else:
                                past = bare + "ed"
                            s = f"{subj_en} {past}"
                    elif self.tense == "futuro":
                        s = f"{subj_en} will {bare}"
                    elif self.tense == "condizionale":
                        s = f"{subj_en} would {bare}"
                    elif self.tense == "imperfetto":
                        s = f"{subj_en} used to {bare}"
                    else:
                        s = f"{subj_en} {bare}"
                if comp_en:
                    s += f" {comp_en}"
                if adv_en_i:
                    s += f" {adv_en_i}"
                parts.append(s)

        elif self.template == "J":
            # Object transfer English prompt
            if self.transfer_recipient and self.transfer_object:
                obj_ref = self.transfer_object
                recip = self.transfer_recipient
                # Gender marker for the object pronoun
                gender_marker = "(m)" if obj_ref["gender"] == "m" else "(f)"
                num_marker = "pl" if obj_ref["number"] == "p" else ""
                pron_desc = f"it {gender_marker}" if obj_ref["number"] == "s" else f"them {gender_marker}"

                subj_en = SUBJECT_EN[self.subject]
                tv = TRANSFER_VERB_MAP.get(self.verb, {})
                bare = tv.get("en", verb_info["en"]).replace("to ", "")

                if self.tense == "presente":
                    third = self.subject in ("lui", "lei")
                    if third:
                        words = bare.split()
                        w = words[0]
                        if w.endswith("e"):
                            vf = w + "s"
                        elif w.endswith("y") and len(w) > 1 and w[-2] not in "aeiou":
                            vf = w[:-1] + "ies"
                        else:
                            vf = w + "s"
                        words[0] = vf
                        s = f"{subj_en} {' '.join(words)} {pron_desc} {recip['en']}"
                    else:
                        s = f"{subj_en} {bare} {pron_desc} {recip['en']}"
                elif self.tense == "passato_prossimo":
                    en_past = tv.get("en_past", bare + "ed")
                    s = f"{subj_en} {en_past} {pron_desc} {recip['en']}"
                elif self.tense == "futuro":
                    s = f"{subj_en} will {bare} {pron_desc} {recip['en']}"
                elif self.tense == "condizionale":
                    s = f"{subj_en} would {bare} {pron_desc} {recip['en']}"
                elif self.tense == "imperfetto":
                    s = f"{subj_en} used to {bare} {pron_desc} {recip['en']}"
                else:
                    s = f"{subj_en} {bare} {pron_desc} {recip['en']}"

                if self.adv:
                    s += f" {self.adv['en']}"
                parts.append(s)
                parts.append("[use combined pronouns]")

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

    # Temporally coherent adverb
    frame_class = _classify_frame(frame)
    adv = _get_compatible_adverb(tense, frame_class)

    return SentenceSpec(
        verb=verb, tense=tense, subject=subject, frame=frame, template="F",
        gender_io_tu=gender_io_tu,
        adv=adv,
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
    """Generate a template G (agreement) sentence.

    Adjective rules:
    - State verbs (essere, stare, restare, rimanere, diventare) can take
      predicate adjectives in any tense.
    - Resultative verbs (arrivare, tornare) can only take adjectives in
      passato_prossimo ("è arrivata stanca").
    """
    gs = _pick_gendered_subject()
    adj = random.choice(ADJECTIVES)

    # Enforce tense compatibility with adjective usage
    if verb in AGREEMENT_VERBS_RESULTATIVE:
        # Resultative adjective only works in passato prossimo
        tense = "passato_prossimo"
    elif verb in AGREEMENT_VERBS_STATE:
        # State verbs: prefer passato_prossimo 50% for agreement practice
        if random.random() < 0.5 and tense != "passato_prossimo":
            tense = "passato_prossimo"
    else:
        # Verb not suitable for adjective — fall back to a state verb
        verb = random.choice(AGREEMENT_VERBS_STATE)

    frame_class = _classify_frame(frame)

    # Try a location element; if picked, skip the time adverb
    location = _pick_location_element(verb)
    if location:
        adv = None
    else:
        adv = _get_compatible_adverb(tense, frame_class)

    return SentenceSpec(
        verb=verb, tense=tense, subject=gs["verb_subject"],
        frame=frame, template="G",
        gender_io_tu=gender_io_tu,
        adv=adv,
        adjective=adj,
        gendered_subject=gs,
        location=location,
    )


def _generate_template_h(
    verb: str,
    tense: str,
    frame: Dict[str, str],
    gender_io_tu: str,
) -> SentenceSpec:
    """Generate a template H (question) sentence.

    Questions never use discourse frames.
    """
    # Pick a question word (weighted)
    weights = [qw["weight"] for qw in QUESTION_WORDS]
    qw = random.choices(QUESTION_WORDS, weights=weights, k=1)[0]

    # If question word has a verb filter, choose a compatible verb
    if qw.get("verb_filter"):
        compatible = [v for v in qw["verb_filter"] if v in VERB_MAP]
        if compatible:
            verb = random.choice(compatible)

    # Pick a subject — chi questions don't need one (chi IS the subject)
    if qw["it"] == "chi":
        # "chi" acts as 3rd person singular subject
        subject = "lui"
        gendered_subject = None
    elif qw.get("needs_subj", True):
        # Use a gendered subject ~60% of the time for variety
        if random.random() < 0.6:
            gs = _pick_gendered_subject()
            subject = gs["verb_subject"]
            gendered_subject = gs
        else:
            subject = random.choice(["lui", "lei", "loro", "tu", "noi", "voi"])
            gendered_subject = None
    else:
        subject = random.choice(SUBJECTS)
        gendered_subject = None

    # "quale" needs a noun
    quale_noun = None
    if qw.get("needs_noun"):
        quale_noun = random.choice(QUALE_NOUNS)

    # Object for transitive verbs (not for dove/quando/come/perché/da dove)
    obj = None
    if qw["it"] in ("chi", "cosa", "quale", "a chi", "quante ore", "per quanto tempo"):
        pass  # These don't need an object in the question
    elif qw["it"] not in ("dove", "da dove", "come", "perché", "quando", "con chi"):
        if _needs_object(verb):
            obj = get_object_for_verb(verb)

    # Adverb — only occasionally and no habitual adverbs in questions
    adv = None
    if random.random() < 0.3:
        pool = _get_adverb_pool(tense)
        non_habitual = [a for a in pool if a["it"] not in HABITUAL_ADVERBS]
        if non_habitual:
            adv = random.choice(non_habitual)

    return SentenceSpec(
        verb=verb, tense=tense, subject=subject,
        frame=NO_FRAME, template="H",
        gender_io_tu=gender_io_tu,
        obj=obj, adv=adv,
        question_word=qw,
        quale_noun=quale_noun,
        gendered_subject=gendered_subject,
    )


def _generate_template_i(
    tense: str,
    frame: Dict[str, str],
    gender_io_tu: str,
    difficulty_unlocked: bool,
) -> SentenceSpec:
    """Generate a template I (reflexive verb) sentence."""
    rv = random.choice(REFLEXIVE_VERBS)

    # Reciprocal verbs need plural subjects
    if rv["infinitive"] in RECIPROCAL_REFLEXIVES:
        subject = random.choice(["noi", "voi", "loro"])
    else:
        subject = random.choice(SUBJECTS)

    frame_class = _classify_frame(frame)

    # 20% chance of modal (devo svegliarmi / mi devo svegliare)
    # Only in simple tenses — passato prossimo + modal + reflexive is too complex
    reflexive_modal = None
    if random.random() < 0.2 and difficulty_unlocked and tense != "passato_prossimo":
        reflexive_modal = random.choice(["volere", "potere", "dovere"])

    # Optional complement
    complement = None
    complements = REFLEXIVE_COMPLEMENTS.get(rv["infinitive"])
    if complements and random.random() < 0.5:
        complement = random.choice(complements)

    # Use a gendered subject ~40% of the time
    gendered_subject = None
    if random.random() < 0.4 and reflexive_modal is None:
        gs = _pick_gendered_subject()
        # Respect reciprocal constraint
        if rv["infinitive"] in RECIPROCAL_REFLEXIVES:
            if gs["number"] != "p":
                gs = None
        if gs:
            gendered_subject = gs
            subject = gs["verb_subject"]

    # Adverb
    adv = None
    if complement is None and random.random() < 0.4:
        adv = _get_compatible_adverb(tense, frame_class)

    return SentenceSpec(
        verb=rv["stem_verb"], tense=tense, subject=subject,
        frame=frame, template="I",
        gender_io_tu=gender_io_tu,
        adv=adv,
        reflexive_verb=rv,
        reflexive_complement=complement,
        reflexive_modal=reflexive_modal,
        gendered_subject=gendered_subject,
    )


def _generate_template_j(
    tense: str,
    subject: str,
    frame: Dict[str, str],
    gender_io_tu: str,
) -> SentenceSpec:
    """Generate a template J (object transfer with combined pronouns) sentence."""
    tv = random.choice(TRANSFER_VERBS)
    obj = random.choice(TRANSFER_OBJECTS)
    recip = random.choice(TRANSFER_RECIPIENTS)

    # Avoid giving something "to yourself" — skip if indirect pronoun matches subject
    subj_to_pron = {"io": "mi", "tu": "ti", "lui": "gli", "lei": "le_ind",
                     "noi": "ci", "voi": "vi", "loro": "gli"}
    if subj_to_pron.get(subject) == recip["indirect_it"]:
        # Re-pick recipient
        others = [r for r in TRANSFER_RECIPIENTS if r["indirect_it"] != subj_to_pron.get(subject)]
        if others:
            recip = random.choice(others)

    frame_class = _classify_frame(frame)
    adv = None
    if random.random() < 0.3:
        adv = _get_compatible_adverb(tense, frame_class)

    return SentenceSpec(
        verb=tv["infinitive"], tense=tense, subject=subject,
        frame=frame, template="J",
        gender_io_tu=gender_io_tu,
        adv=adv,
        transfer_object=obj,
        transfer_recipient=recip,
    )


def _validate_sentence(spec: SentenceSpec) -> bool:
    """Validate that a generated sentence is semantically coherent.

    Checks:
    1. Verb category + adjective usage
    2. Verb category + object category
    3. Tense + adverb compatibility
    4. Frame + adverb temporal coherence
    5. Location element compatibility
    """
    sem = VERB_SEMANTIC_CATEGORY.get(spec.verb, "action")

    # 1. Adjective should only appear with state verbs (or resultative in pp)
    if spec.adjective:
        if sem == "state":
            pass  # always OK
        elif spec.verb in ADJECTIVE_PASSATO_VERBS and spec.tense == "passato_prossimo":
            pass  # resultative OK in passato prossimo
        else:
            return False

    # 2. Movement verbs must have location objects (not random nouns)
    if sem == "movement" and spec.obj:
        location_its = {loc["it"] for loc in OBJECTS_LOCATION}
        if spec.obj["it"] not in location_its:
            return False

    # 3. Tense + adverb compatibility
    if spec.adv:
        adv_it = spec.adv["it"]
        if adv_it in {"domani", "la settimana prossima"}:
            if spec.tense in ("passato_prossimo", "imperfetto"):
                return False
        elif adv_it in {"ieri", "stamattina", "la settimana scorsa"}:
            if spec.tense in ("futuro", "presente"):
                return False
        elif adv_it in {"oggi", "adesso", "ora"}:
            if spec.tense in ("futuro", "imperfetto"):
                return False

    # 4. Habitual frames should have no adverb (frame provides the context)
    frame_class = _classify_frame(spec.frame)
    if frame_class == "habitual" and spec.adv is not None:
        return False

    # 5. Specific frames should not pair with habitual adverbs
    if spec.adv:
        adv_class = _classify_adverb(spec.adv)
        if frame_class == "specific" and adv_class == "habitual":
            return False

    # 6. Questions should have no discourse frame
    if spec.template == "H" and spec.frame.get("it", ""):
        return False

    # 7. Location element checks
    if spec.location:
        # Location only for movement and state verbs
        if sem not in LOCATION_ELIGIBLE_CATEGORIES:
            return False
        # Never combine location with a location object
        if spec.obj:
            return False
        # Never combine location with a time adverb
        if spec.adv:
            return False

    return True


def generate_sentence(
    verb: str,
    allowed_tenses: List[str],
    difficulty_unlocked: bool,
    gender_io_tu: str,
    focus_mode: str = "all",
) -> SentenceSpec:
    """Generate a random sentence specification for a given verb.

    Includes semantic validation with retry (up to 5 attempts) and
    fallback to a simple template A sentence.
    """
    for _attempt in range(5):
        spec = _generate_sentence_inner(
            verb, allowed_tenses, difficulty_unlocked, gender_io_tu, focus_mode
        )
        if _validate_sentence(spec):
            return spec

    # Fallback: simple template A with safe defaults
    tense = _pick_tense(difficulty_unlocked, allowed_tenses)
    frame = _pick_frame(difficulty_unlocked)
    frame_class = _classify_frame(frame)
    subject = random.choice(SUBJECTS)
    obj = get_object_for_verb(verb) if _needs_object(verb) else None
    adv = _get_compatible_adverb(tense, frame_class)
    return SentenceSpec(verb, tense, subject, frame, "A", obj, adv, gender_io_tu=gender_io_tu)


def _generate_sentence_inner(
    verb: str,
    allowed_tenses: List[str],
    difficulty_unlocked: bool,
    gender_io_tu: str,
    focus_mode: str = "all",
) -> SentenceSpec:
    """Inner sentence generation (may produce invalid combos, validated by caller)."""
    tense = _pick_tense(difficulty_unlocked, allowed_tenses)
    frame = _pick_frame(difficulty_unlocked)
    frame_class = _classify_frame(frame)

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
        if verb in PRONOUN_VERBS or random.random() < 0.7:
            effective_verb = verb if verb in PRONOUN_VERBS else random.choice(PRONOUN_VERBS)
            return _generate_template_f(effective_verb, tense, subject, frame, gender_io_tu)

    if focus_mode == "agreement":
        if verb in AGREEMENT_VERBS or random.random() < 0.7:
            effective_verb = verb if verb in AGREEMENT_VERBS else random.choice(AGREEMENT_VERBS)
            return _generate_template_g(effective_verb, tense, frame, gender_io_tu)

    # Choose template
    if _is_modal(verb):
        template = "A"
        obj = get_object_for_verb(verb)
        adv = _get_compatible_adverb(tense, frame_class)
        return SentenceSpec(verb, tense, subject, frame, template, obj, adv, gender_io_tu=gender_io_tu)

    if difficulty_unlocked:
        # A:20% B:10% C:5% D:5% E:5% F:15% G:10% H:15% I:10% J:5%
        template = random.choices(
            ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"],
            weights=[20, 10, 5, 5, 5, 15, 10, 15, 10, 5],
            k=1,
        )[0]
    else:
        template = random.choices(
            ["A", "B", "F", "G", "H", "I"],
            weights=[40, 10, 15, 10, 15, 10],
            k=1,
        )[0]

    obj = None
    adv = _get_compatible_adverb(tense, frame_class)
    modal = None
    location = None

    # For templates A/B/C: try a location element for eligible verbs
    # Location replaces both the location-object and the time adverb
    loc_candidate = _pick_location_element(verb) if template in ("A", "B", "C") else None

    if template == "A":
        if loc_candidate:
            # Location element replaces obj and adverb
            location = loc_candidate
            obj = None
            adv = None
        elif _needs_object(verb):
            obj = get_object_for_verb(verb)

    elif template == "B":
        modal = random.choice(["potere", "volere", "dovere"])
        if loc_candidate:
            location = loc_candidate
            obj = None
            adv = None
        elif _needs_object(verb):
            obj = get_object_for_verb(verb)

    elif template == "C":
        if loc_candidate:
            location = loc_candidate
            obj = None
            adv = None
        elif _needs_object(verb):
            obj = get_object_for_verb(verb)

    elif template == "D":
        if _needs_object(verb):
            obj = get_object_for_verb(verb)

    elif template == "E":
        subject = "tu"
        if _needs_object(verb):
            obj = get_object_for_verb(verb)

    elif template == "F":
        effective_verb = verb if verb in PRONOUN_VERBS else random.choice(PRONOUN_VERBS)
        return _generate_template_f(effective_verb, tense, subject, frame, gender_io_tu)

    elif template == "G":
        effective_verb = verb if verb in AGREEMENT_VERBS else random.choice(AGREEMENT_VERBS)
        return _generate_template_g(effective_verb, tense, frame, gender_io_tu)

    elif template == "H":
        return _generate_template_h(verb, tense, frame, gender_io_tu)

    elif template == "I":
        return _generate_template_i(tense, frame, gender_io_tu, difficulty_unlocked)

    elif template == "J":
        return _generate_template_j(tense, subject, frame, gender_io_tu)

    return SentenceSpec(verb, tense, subject, frame, template, obj, adv, modal, gender_io_tu, location=location)


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
    # Normalize comma spacing: comma attached to preceding word, space after
    s = re.sub(r"\s*,\s*", ", ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def normalize_flexible(text: str) -> str:
    """Even more flexible normalization: strip all commas entirely.

    Used for comparison — if both sides match after stripping commas, accept it.
    """
    return normalize(text).replace(",", "").replace("  ", " ").strip()


def _strip_leading_pronoun(text: str) -> str:
    """Strip a leading subject pronoun from normalized text.

    The model answer omits subject pronouns (pro-drop), but if the user
    includes one we should still accept it.  This helper removes the pronoun
    so both sides can be compared without it.
    """
    pronouns = {"io", "tu", "lui", "lei", "noi", "voi", "loro"}
    words = text.split()
    # Try stripping pronoun at position 0 (no frame)
    if words and words[0] in pronouns:
        return " ".join(words[1:])
    # Try stripping pronoun right after a comma (frame present)
    # After normalize, commas attach to the preceding word: "me, io" → ["me,", "io"]
    for i, w in enumerate(words):
        if w.endswith(",") and i + 1 < len(words) and words[i + 1] in pronouns:
            return " ".join(words[: i + 1] + words[i + 2:])
    return text


def answers_match(user_input: str, expected: str, spec: Optional[SentenceSpec] = None) -> bool:
    """Check if user input matches expected answer.

    Accepts the answer with or without the subject pronoun, since
    Italian is pro-drop and the model answer omits it.
    Also checks spec.alt_italian for alternate accepted forms.
    """
    u_norm = normalize(user_input)
    e_norm = normalize(expected)

    # Exact normalized match
    if u_norm == e_norm:
        return True
    # Flexible match (ignore commas)
    if normalize_flexible(user_input) == normalize_flexible(expected):
        return True
    # User included subject pronoun that the model answer omits — strip it
    u_stripped = _strip_leading_pronoun(u_norm)
    if u_stripped == e_norm:
        return True
    if normalize_flexible(u_stripped) == normalize_flexible(expected):
        return True
    # Check alternate answer
    if spec and spec.alt_italian:
        alt_norm = normalize(spec.alt_italian)
        if u_norm == alt_norm or normalize_flexible(user_input) == normalize_flexible(spec.alt_italian):
            return True
        if u_stripped == alt_norm or normalize_flexible(u_stripped) == normalize_flexible(spec.alt_italian):
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

def _find_sync_script() -> Optional[Path]:
    """Locate sync_to_sheets.py, checking Colab paths first.

    Search order:
      1. /content/sync_to_sheets.py          (Colab working dir)
      2. /content/drive/MyDrive/sync_to_sheets.py  (Google Drive)
         — if found here but not in /content/, copy it there first
      3. Same directory as italian_drill.py   (local / fallback)
    """
    import shutil

    colab_content = Path("/content/sync_to_sheets.py")
    colab_drive = Path("/content/drive/MyDrive/sync_to_sheets.py")
    local = Path(__file__).resolve().parent / "sync_to_sheets.py"

    if colab_content.exists():
        return colab_content

    if colab_drive.exists():
        try:
            shutil.copy2(str(colab_drive), str(colab_content))
            print(f"  Copied sync_to_sheets.py from Drive to {colab_content}")
            return colab_content
        except OSError:
            return colab_drive

    if local.exists():
        return local

    return None


def run_sync() -> None:
    """Run sync_to_sheets.py after loading .env."""
    script_dir = Path(__file__).resolve().parent

    sync_script = _find_sync_script()
    if sync_script is None:
        print("Warning: sync_to_sheets.py not found, skipping sync.")
        return

    # Load .env — check Colab paths, then local
    env = os.environ.copy()
    env_candidates = [
        Path("/content/.env"),
        Path("/content/drive/MyDrive/.env"),
        script_dir / ".env",
    ]
    for env_file in env_candidates:
        if env_file.exists():
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, _, value = line.partition("=")
                        env[key.strip()] = value.strip()
            break

    try:
        result = subprocess.run(
            [sys.executable, str(sync_script)],
            env=env,
            cwd=str(sync_script.parent),
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

            # --- Command dispatch (checked BEFORE any answer evaluation) ---
            cmd = user_input.lower()

            if cmd == ":quit":
                break

            if cmd == ":help":
                print("\nCommands:")
                print("  :quit   — exit, save, show summary, sync")
                print("  :stats  — show detailed statistics")
                print("  :hint   — reveal verb infinitive + required tense")
                print("  :flag   — mark sentence as unnatural, skip")
                print("  :test   — run conjugation self-check")
                print("  :help   — show this help")
                print()
                continue

            if cmd == ":stats":
                show_stats(progress, elapsed_min)
                continue

            if cmd == ":test":
                run_self_check()
                continue

            if cmd == ":flag":
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

            if cmd == ":hint":
                hint_used = True
                vp["hint_uses"] = vp.get("hint_uses", 0) + 1
                if spec.reflexive_verb:
                    rv = spec.reflexive_verb
                    print(f"\n  Hint: {rv['infinitive']} ({rv['en']}) — {tense_label}")
                    print(f"  Reflexive: always essere in passato prossimo")
                elif spec.template == "J":
                    print(f"\n  Hint: {verb} ({VERB_MAP.get(verb, {}).get('en', verb)}) — {tense_label}")
                    print(f"  Combined pronouns: indirect + direct → combined form")
                elif spec.template == "H":
                    print(f"\n  Hint: {verb} ({VERB_MAP.get(verb, {}).get('en', verb)}) — {tense_label}")
                    print(f"  Question word: {spec.question_word['it'] if spec.question_word else '?'}")
                else:
                    print(f"\n  Hint: {verb} ({VERB_MAP.get(verb, {}).get('en', verb)}) — {tense_label}")
                if spec.tense == "passato_prossimo" and not spec.reflexive_verb:
                    aux = "essere" if (verb in ESSERE_VERBS or verb == "essere") else "avere"
                    print(f"  Auxiliary: {aux}")
                print()
                # Re-prompt for answer after hint
                try:
                    user_input = input("  IT: ").strip()
                except EOFError:
                    break
                if not user_input:
                    continue
                # Re-check commands on the post-hint input
                cmd2 = user_input.lower()
                if cmd2 == ":quit":
                    break
                if cmd2 == ":flag":
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
                if cmd2 in (":stats", ":help", ":test", ":hint"):
                    # Non-answer commands after hint — skip this round
                    continue

            # --- Check answer ---
            correct = answers_match(user_input, expected_it, spec)
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
                    if answers_match(retry, expected_it, spec):
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


if __name__ in ("__main__", "<run_path>"):
    main()
