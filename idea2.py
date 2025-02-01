import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import random
from gspread.exceptions import APIError, GSpreadException
import time
from datetime import datetime
import pandas as pd

# Funzione per l'inizializzazione e autenticazione di Google Sheets
def init_google_sheet():
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

    try:
        return client.open("Dati Partecipanti").sheet1
    except APIError:
        st.error("Errore di accesso al Google Sheet: verifica che il foglio esista e sia condiviso con l'account di servizio.")
        return None

# Inizializza Google Sheet una volta sola e salva in session_state
if "sheet" not in st.session_state:
    st.session_state.sheet = init_google_sheet()

# Funzione per verificare e caricare i dati dal Google Sheet in DataFrame
def load_sheet_data(sheet):
    try:
        records = sheet.get_all_records()
        return pd.DataFrame(records)
    except GSpreadException:
        st.error("Errore nel caricamento dei dati. Controlla che le intestazioni nel foglio siano uniche.")
        try:
            rows = sheet.get_all_values()
            headers = rows[0]
            data = rows[1:]
            return pd.DataFrame(data, columns=headers)
        except Exception as e:
            st.error("Errore nel caricamento dei dati dal Google Sheet.")
            return None

# Definizione delle frasi

# Frasi target e di controllo
target_phrases = [
    {"frase": "On February 4, 2025, in the Coppa Italia football match Atalanta vs. Bologna, Atalanta will win the match.", "feedback": "Di questa frase non sappiamo se è vera o falsa"}
]

control_phrases = [
    {"frase": "On February 4, 2025, in the Coppa Italia football match Atalanta vs. Bologna, Atalanta will lose the match.", "feedback": "Di questa frase non sappiamo se è vera o falsa"}
]

# Frasi di test
test_phrases = [
    {"frase": f"Test phrase {i+1} (True)", "corretta": True} if i % 2 == 0 else {"frase": f"Test phrase {i+1} (False)", "corretta": False}
    for i in range(30)
]

# Funzione per salvare i risultati di una singola risposta
def save_single_response(participant_id, email, frase, risposta, feedback):
    sheet = st.session_state.sheet
    if sheet is not None:
        try:
            sheet.append_row([participant_id, email, frase, risposta, feedback, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        except APIError:
            st.error("Si è verificato un problema durante il salvataggio dei dati. Riprova più tardi.")

# Funzione principale dell'app
def main():
    st.title("Test di Valutazione a intuito di Frasi Nascoste")

    # Input per l'ID partecipante e l'email
    participant_id = st.text_input("Inserisci il tuo ID partecipante (Prolific ID)")
    email = st.text_input("Inserisci la tua email (se vuoi ricevere i risultati dello studio)")

    if participant_id and email and st.button("Inizia il Test"):
        st.session_state.participant_id = participant_id
        st.session_state.email = email
        st.session_state.all_phrases = target_phrases + control_phrases + test_phrases
        random.shuffle(st.session_state.all_phrases)
        st.session_state.current_index = 0
        st.session_state.total_correct = 0
        st.session_state.response_locked = False
        st.experimental_rerun()

    if "all_phrases" in st.session_state:
        if st.session_state.current_index < len(st.session_state.all_phrases):
            current_phrase = st.session_state.all_phrases[st.session_state.current_index]

            st.markdown(
                "<div style='width: 100%; height: 80px; background-color: black; color: black; text-align: center;'>"
                "Testo Nascosto Dietro il Pannello Nero</div>",
                unsafe_allow_html=True
            )

            st.markdown(
                "Rispondi alla prossima domanda seguendo il tuo intuito.<br>La frase nascosta dietro al rettangolo nero qui sopra è vera o falsa?",
                unsafe_allow_html=True
            )

            risposta = st.radio(
                "Seleziona la tua risposta:",
                ("Seleziona", "Vera", "Falsa"),
                index=0,
                key=f"response_{st.session_state.current_index}",
                disabled=st.session_state.response_locked
            )

            if st.button("Conferma") and not st.session_state.response_locked:
                st.session_state.response_locked = True

                if "corretta" in current_phrase:
                    is_correct = (risposta == "Vera") == current_phrase["corretta"]
                    feedback = "Giusto" if is_correct else "Sbagliato"
                    if is_correct:
                        st.session_state.total_correct += 1
                else:
                    feedback = current_phrase["feedback"]

                save_single_response(
                    st.session_state.participant_id,
                    st.session_state.email,
                    current_phrase["frase"],
                    risposta,
                    feedback
                )

                st.write(feedback)
                time.sleep(1)
                st.write("Generazione di una nuova frase...")
                time.sleep(1)

                st.session_state.current_index += 1
                st.session_state.response_locked = False

                if st.session_state.current_index >= len(st.session_state.all_phrases):
                    st.write("Test completato!")
                    st.write(f"Risposte corrette (test): {st.session_state.total_correct} su {len(test_phrases)}")
                    st.stop()
                else:
                    st.experimental_rerun()
        else:
            st.write("Test completato!")
            st.write(f"Risposte corrette (test): {st.session_state.total_correct} su {len(test_phrases)}")
            st.stop()

if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()

