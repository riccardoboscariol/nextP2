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
                time.sleep(2)  # Attendi 2 secondi prima di riprovare
            else:
                st.error("Errore di accesso al Google Sheet: verifica la connessione internet e riprova più tardi.")
                return None

# Inizializza Google Sheet una volta sola e salva in session_state
if "sheet" not in st.session_state:
    st.session_state.sheet = init_google_sheet()

# Funzione per verificare e caricare i dati dal Google Sheet in DataFrame
def load_sheet_data(sheet, max_retries=3):
    for attempt in range(max_retries):
        try:
            records = sheet.get_all_records()
            return pd.DataFrame(records)
        except GSpreadException:
            if attempt < max_retries - 1:
                st.warning(f"Errore nel caricamento dei dati. Riprova ({attempt + 1}/{max_retries})...")
                time.sleep(2)
            else:
                st.error("Errore nel caricamento dei dati. Controlla la connessione internet e riprova più tardi.")
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
    {"frase": "On 20 March 2025, the Apple stock will be higher than on 15 March 2025", "feedback": "We do not know if this statement is true or false."},
    {"frase": "On 20 March 2025, the Apple stock will be higher than on 15 February 2025", "feedback": "We do not know if this statement is true or false."},
]

control_phrases = [
     {"frase": "On 20 March 2025, the Apple stock will be lower than on 15 March 2025", "feedback": "We do not know if this statement is true or false."},
    {"frase": "On 20 March 2025, the Apple stock will be lower than on 15 February 2025", "feedback": "We do not know if this statement is true or false."},
]

# Frasi di test
test_phrases = [
    {"frase": "On 15 July 2023, the NVIDIA stock was higher than on 10 June 2023.", "corretta": True},
    {"frase": "On 10 June 2023, the Alphabet (Google) stock was lower than on 5 May 2023.", "corretta": False},
    {"frase": "On 20 August 2024, the Netflix stock was lower than on 15 July 2024.", "corretta": False},
    {"frase": "On 25 April 2023, the Microsoft stock was lower than on 20 March 2023.", "corretta": False},
    {"frase": "On 20 February 2024, the Tesla stock was lower than on 15 January 2024.", "corretta": False},
    {"frase": "On 15 July 2023, the Apple stock was higher than on 10 June 2023.", "corretta": True},
    {"frase": "On 20 August 2023, the Netflix stock was lower than on 15 August 2023.", "corretta": False},
    {"frase": "On 20 March 2023, the Apple stock was higher than on 15 March 2023.", "corretta": True},
    {"frase": "On 10 December 2023, the Microsoft stock was lower than on 5 November 2023.", "corretta": False},
    {"frase": "On 20 August 2023, the Microsoft stock was lower than on 15 July 2023.", "corretta": False},
    {"frase": "Barcelona won against Atletico Madrid on April 25, 2024.", "corretta": False},
    {"frase": "Borussia Dortmund won against Leipzig on October 30, 2024.", "corretta": False},
    {"frase": "PSG won against Lille on July 8, 2023.", "corretta": True},
    {"frase": "Marseille won against PSG on May 5, 2024.", "corretta": True},
    {"frase": "Inter won against Fiorentina on April 15, 2023.", "corretta": False},
    {"frase": "Milan won against Napoli on February 8, 2024.", "corretta": False},
    {"frase": "Fiorentina won against Bologna on March 15, 2024.", "corretta": True},
    {"frase": "Napoli won against Fiorentina on June 30, 2023.", "corretta": False},
    {"frase": "PSG won against Marseille on May 5, 2024.", "corretta": True},
    {"frase": "Milan won against Napoli on July 8, 2023.", "corretta": False},
    {"frase": "Liverpool won against Manchester United on December 15, 2023.", "corretta": False},
    {"frase": "Bayern Munich won against Leipzig on July 25, 2023.", "corretta": True},
    {"frase": "Napoli won against Lazio on November 10, 2023.", "corretta": True},
    {"frase": "Chelsea won against Manchester United on October 30, 2023.", "corretta": False},
    {"frase": "PSG won against Lille on August 15, 2023.", "corretta": True},
    {"frase": "Bayern Munich won against Leipzig on October 10, 2023.", "corretta": True},
    {"frase": "Arsenal won against Tottenham on January 10, 2024.", "corretta": False},
    {"frase": "Inter won against Roma on May 15, 2023.", "corretta": True},
    {"frase": "Bayern Munich won against Borussia Dortmund on July 30, 2024.", "corretta": True},
    {"frase": "Chelsea won against Tottenham on August 8, 2024.", "corretta": False}
]

# Funzione per salvare i risultati di una singola risposta con riprova
def save_single_response(participant_id, email, frase, risposta, feedback, max_retries=3):
    sheet = st.session_state.sheet
    if sheet is not None:
        for attempt in range(max_retries):
            try:
                sheet.append_row([participant_id, email, frase, risposta, feedback, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
                return  # Se ha successo, esci dalla funzione
            except APIError:
                if attempt < max_retries - 1:
                    st.warning(f"Errore durante il salvataggio. Riprova ({attempt + 1}/{max_retries})...")
                    time.sleep(2)
                else:
                    st.error("Si è verificato un problema durante il salvataggio dei dati. Riprova più tardi.")

# Funzione principale dell'app
def main():
    st.title("Intuitive Evaluation Test of Hidden Statements")

    # Input per l'ID partecipante e l'email
    participant_id = st.text_input("Enter your participant ID (Prolific ID)")
    email = st.text_input("Enter your email (if you wish to receive the results of the study, otherwise write “no”.)")

    if participant_id and email and st.button("Start the Test"):
        st.session_state.participant_id = participant_id
        st.session_state.email = email
        st.session_state.all_phrases = target_phrases + control_phrases + test_phrases
        random.shuffle(st.session_state.all_phrases)  # Mescola le frasi in modo casuale
        st.session_state.current_index = 0
        st.session_state.total_correct = 0
        st.session_state.response_locked = False
        st.experimental_rerun()

    if "all_phrases" in st.session_state:
        if st.session_state.current_index < len(st.session_state.all_phrases):
            current_phrase = st.session_state.all_phrases[st.session_state.current_index]

            st.markdown(
                "<div style='width: 100%; height: 80px; background-color: black; color: black; text-align: center;'>"
                "Hidden Text Behind the Black Panel</div>",
                unsafe_allow_html=True
            )

            st.markdown(
                "Answer the next question based on your intuition.<br>Is the hidden statement behind the black rectangle above true or false?",
                unsafe_allow_html=True
            )

            risposta = st.radio(
                "Select your answer:",
                ("Select", "True", "False"),
                index=0,
                key=f"response_{st.session_state.current_index}",
                disabled=st.session_state.response_locked
            )

            if st.button("Confirm") and not st.session_state.response_locked:
                st.session_state.response_locked = True

                if "corretta" in current_phrase:
                    is_correct = (risposta == "True") == current_phrase["corretta"]
                    feedback = "Correct" if is_correct else "Incorrect"
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
                st.write("Generating a new statement...")
                time.sleep(1)

                st.session_state.current_index += 1
                st.session_state.response_locked = False

                if st.session_state.current_index >= len(st.session_state.all_phrases):
                    st.write("Test completed!")
                    st.write(f"Correct answers (test): {st.session_state.total_correct} out of {len(test_phrases)}")
                    st.stop()
                else:
                    st.experimental_rerun()
        else:
            st.write("Test completed!")
            st.write(f"Correct answers (test): {st.session_state.total_correct} out of {len(test_phrases)}")
            st.stop()

if __name__ == "__main__":
    main()
