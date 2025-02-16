import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import random
from gspread.exceptions import APIError, GSpreadException
import time
from datetime import datetime
import pandas as pd

# Funzione per l'inizializzazione e autenticazione di Google Sheets con riprova
def init_google_sheet(max_retries=3):
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive"
    ]

    creds_dict = st.secrets["google_sheets"]["credentials_json"]
    if isinstance(creds_dict, str):  # Se è una stringa, convertila in dizionario
        creds_dict = json.loads(creds_dict)

    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)

    for attempt in range(max_retries):
        try:
            return client.open("Dati Partecipanti").sheet1
        except APIError as e:
            if attempt < max_retries - 1:
                st.warning(f"Errore di connessione. Riprova ({attempt + 1}/{max_retries})...")
                time.sleep(2)
            else:
                st.error("Errore di accesso al Google Sheet: verifica la connessione internet e riprova più tardi.")
                return None

# Inizializza Google Sheet una volta sola e salva in session_state
if "sheet" not in st.session_state:
    st.session_state.sheet = init_google_sheet()

# Frasi target e di controllo
target_phrases = [
    {"frase": "On February 18, 2025, in the Champions League football match Atalanta vs. Club Brugge, Atalanta will win the match.", "feedback": "We do not know if this statement is true or false."},
    {"frase": "On February 18, 2025, in the Champions League football match Benfica vs. Monaco, Benfica will win the match.", "feedback": "We do not know if this statement is true or false."},
    {"frase": "On February 19, 2025, in the Champions League football match Real Madrid vs. Manchester City, Real Madrid will win the match.", "feedback": "We do not know if this statement is true or false."}
]

control_phrases = [
    {"frase": "On February 18, 2025, in the Champions League football match Atalanta vs. Club Brugge, Atalanta will lose the match.", "feedback": "We do not know if this statement is true or false."},
    {"frase": "On February 18, 2025, in the Champions League football match Benfica vs. Monaco, Benfica will lose the match.", "feedback": "We do not know if this statement is true or false."},
    {"frase": "On February 19, 2025, in the Champions League football match Real Madrid vs. Manchester City, Real Madrid will lose the match.", "feedback": "We do not know if this statement is true or false."}
]

# Frasi di test
test_phrases = [
    {"frase": "Barcelona won against Real Madrid on August 15, 2023.", "corretta": False},
    {"frase": "Napoli won against Lazio on January 20, 2024.", "corretta": True},
    {"frase": "Roma won against Juventus on December 15, 2023.", "corretta": False},
    {"frase": "Juventus won against Torino on January 5, 2023.", "corretta": True},
    {"frase": "Manchester City won against Chelsea on October 30, 2023.", "corretta": False},
    {"frase": "Inter won against Torino on January 20, 2024.", "corretta": True},
    {"frase": "Manchester City won against Liverpool on August 8, 2023.", "corretta": False},
    {"frase": "Fiorentina won against Torino on February 8, 2024.", "corretta": False},
    {"frase": "Manchester United won against Chelsea on December 30, 2023.", "corretta": True},
    {"frase": "Real Madrid won against Barcelona on June 10, 2023.", "corretta": False}
]

# Frasi di controllo (opposte alle frasi di test)
control_test_phrases = [
    {"frase": phrase["frase"].replace("won", "lost"), "corretta": not phrase["corretta"]}
    for phrase in test_phrases
]

test_phrases += control_test_phrases

# Unione delle frasi
total_phrases = target_phrases + control_phrases + test_phrases
random.shuffle(total_phrases)

# Output delle frasi per il test
for phrase in total_phrases:
    print(phrase)

