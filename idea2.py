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
    if isinstance(creds_dict, str):
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

if "sheet" not in st.session_state:
    st.session_state.sheet = init_google_sheet()

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

# Frasi target e di controllo
target_phrases = [
    {"frase": "On May 31, 2025, in the Champions League football match PSG vs. Inter, PSG will win against Inter", "feedback": "We do not know if this statement is true or false."},
]

control_phrases = [
    {"frase": "On May 31, 2025, in the Champions League football match PSG vs. Inter, Inter will win against PSG", "feedback": "We do not know if this statement is true or false."},

]

# Frasi di test con risposte
raw_test_phrases = [
    ("Barcelona won against Real Madrid on August 15, 2023.", False),
    ("Napoli won against Lazio on January 20, 2024.", True),
    ("Roma won against Juventus on December 15, 2023.", False),
    ("Juventus won against Torino on January 5, 2023.", True),
    ("Manchester City won against Chelsea on October 30, 2023.", False),
    ("Inter won against Torino on January 20, 2024.", True),
    ("Manchester City won against Liverpool on August 8, 2023.", False),
    ("Fiorentina won against Torino on February 8, 2024.", False),
    ("Manchester United won against Chelsea on December 30, 2023.", True),
    ("Real Madrid won against Barcelona on June 10, 2023.", False),
    ("Barcelona won against Atletico Madrid on April 25, 2024.", False),
    ("Borussia Dortmund won against Leipzig on October 30, 2024.", False),
    ("PSG won against Lille on July 8, 2023.", True),
    ("Marseille won against PSG on May 5, 2024.", True),
    ("Inter won against Fiorentina on April 15, 2023.", False),
    ("Milan won against Napoli on February 8, 2024.", False),
    ("Fiorentina won against Bologna on March 15, 2024.", True),
    ("Napoli won against Fiorentina on June 30, 2023.", False),
    ("PSG won against Marseille on May 5, 2024.", True),
    ("Milan won against Napoli on July 8, 2023.", False),
    ("Liverpool won against Manchester United on December 15, 2023.", False),
    ("Bayern Munich won against Leipzig on July 25, 2023.", True),
    ("Napoli won against Lazio on November 10, 2023.", True),
    ("Chelsea won against Manchester United on October 30, 2023.", False),
    ("PSG won against Lille on August 15, 2023.", True),
    ("Bayern Munich won against Leipzig on October 10, 2023.", True),
    ("Arsenal won against Tottenham on January 10, 2024.", False),
    ("Inter won against Roma on May 15, 2023.", True),
    ("Bayern Munich won against Borussia Dortmund on July 30, 2024.", True),
    ("Chelsea won against Tottenham on August 8, 2024.", False),
]

test_phrases = [
    {"frase": frase, "corretta": corretta} for frase, corretta in raw_test_phrases
]

def save_all_responses(participant_id, email, all_responses, completed=True):
    sheet = st.session_state.sheet
    if sheet is not None:
        for attempt in range(3):
            try:
                for response in all_responses:
                    sheet.append_row([
                        participant_id,
                        email,
                        response["frase"],
                        response["risposta"],
                        response["feedback"],
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "COMPLETED" if completed else "INCOMPLETE"
                    ])
                return True
            except APIError:
                if attempt < 2:
                    time.sleep(2)
                else:
                    st.error("Si è verificato un problema durante il salvataggio dei dati. Riprova più tardi.")
                    return False
    return False

def main():
    st.title("Intuitive Evaluation Test of Hidden Statements")

    participant_id = st.text_input("Enter your participant ID (Prolific ID)")
    email = st.text_input("Enter your email (if you wish to receive the results of the study, otherwise write 'no'.)")

    if participant_id and email and st.button("Start the Test"):
        st.session_state.participant_id = participant_id
        st.session_state.email = email
        st.session_state.all_phrases = target_phrases + control_phrases + test_phrases
        random.shuffle(st.session_state.all_phrases)
        st.session_state.current_index = 0
        st.session_state.total_correct = 0
        st.session_state.response_locked = False
        st.session_state.all_responses = []
        st.session_state.start_time = datetime.now()
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

            if risposta != "Select" and st.button("Confirm") and not st.session_state.response_locked:
                st.session_state.response_locked = True

                if "corretta" in current_phrase:
                    is_correct = (risposta == "True") == current_phrase["corretta"]
                    feedback = "Correct" if is_correct else "Incorrect"
                    if is_correct:
                        st.session_state.total_correct += 1
                else:
                    feedback = current_phrase["feedback"]

                st.session_state.all_responses.append({
                    "frase": current_phrase["frase"],
                    "risposta": risposta,
                    "feedback": feedback
                })

                st.write(feedback)
                time.sleep(1)
                st.write("Generating a new statement...")
                time.sleep(1)

                st.session_state.current_index += 1
                st.session_state.response_locked = False
                st.experimental_rerun()

            if st.button("Abandon Test"):
                if save_all_responses(
                    st.session_state.participant_id,
                    st.session_state.email,
                    st.session_state.all_responses,
                    completed=False
                ):
                    st.warning("Your partial responses have been saved. Thank you for your participation.")
                    st.stop()
                else:
                    st.error("Error saving partial responses. Please try again.")

        else:
            if save_all_responses(
                st.session_state.participant_id,
                st.session_state.email,
                st.session_state.all_responses,
                completed=True
            ):
                st.write("Test completed!")
                st.write(f"Correct answers (test): {st.session_state.total_correct} out of {len(test_phrases)}")
                
                # Calcolo tempo impiegato
                time_spent = datetime.now() - st.session_state.start_time
                minutes, seconds = divmod(time_spent.total_seconds(), 60)
                st.write(f"Time spent: {int(minutes)} minutes and {int(seconds)} seconds")
                
                st.stop()
            else:
                st.error("Error saving data. Please try again.")
                st.session_state.current_index -= 1
                st.session_state.response_locked = False
                st.experimental_rerun()

if __name__ == "__main__":
    main()
