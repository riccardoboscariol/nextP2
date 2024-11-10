import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import random
from gspread.exceptions import APIError
import time
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Funzione per l'inizializzazione e autenticazione di Google Sheets
def init_google_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets",
             "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

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
    
# Definizione delle frasi target e di controllo
target_phrases = [
    {"frase": "Apple Inc. (AAPL): Il titolo in data 2025-05-13 sarà più basso rispetto alla data 2025-04-27.", "feedback": "Di questa frase non sappiamo se è vera o falsa"},
    {"frase": "Microsoft Corp. (MSFT): Il titolo in data 2025-05-11 sarà più basso rispetto alla data 2025-05-12.", "feedback": "Di questa frase non sappiamo se è vera o falsa"},
    {"frase": "Amazon.com Inc. (AMZN): Il titolo in data 2025-02-01 sarà più alto rispetto alla data 2025-01-28.", "feedback": "Di questa frase non sappiamo se è vera o falsa"}
]

# LMSR function for probability calculation
def lmsr_probability(yes_count, no_count, b=1):
    yes_score = np.exp(yes_count / b)
    no_score = np.exp(no_count / b)
    total_score = yes_score + no_score
    return yes_score / total_score, no_score / total_score

# Funzione per salvare i risultati di una singola risposta
def save_single_response(participant_id, email, frase, risposta, feedback):
    sheet = st.session_state.sheet  # Usa il foglio dal session_state
    if sheet is not None:  # Verifica che il foglio sia valido
        try:
            sheet.append_row([participant_id, email, frase, risposta, feedback, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        except APIError:
            st.error("Si è verificato un problema durante il salvataggio dei dati. Riprova più tardi.")

# Funzione principale dell'app
def main():
    st.title("Test di Valutazione a intuito di Frasi Nascoste")

    # Input per l'ID partecipante e l'email
    participant_id = st.text_input("Inserisci il tuo ID partecipante")
    email = st.text_input("Inserisci la tua email")

    if participant_id and email and st.button("Inizia il Test"):
        st.session_state.participant_id = participant_id
        st.session_state.email = email
        st.session_state.current_index = 0
        st.session_state.total_correct = 0
        st.session_state.response_locked = False
        st.experimental_rerun()

    # Verifica se il test è iniziato
    if "all_phrases" in st.session_state:
        # Seleziona la frase corrente
        current_phrase = st.session_state.all_phrases[st.session_state.current_index]
        
        # Mostra un pannello nero con la frase nascosta
        st.markdown(
            "<div style='width: 100%; height: 60px; background-color: black; color: black; text-align: center;'>"
            "Testo Nascosto Dietro il Pannello Nero</div>",
            unsafe_allow_html=True
        )
        
        risposta = st.radio(
            "Rispondi alla prossima domanda seguendo il tuo intuito e ascoltando le tue sensazioni interiori.",
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

            save_single_response(st.session_state.participant_id, st.session_state.email, current_phrase["frase"], risposta, feedback)
            
            st.write(feedback)
            time.sleep(2)

            st.session_state.current_index += 1
            st.session_state.response_locked = False

            if st.session_state.current_index >= len(st.session_state.all_phrases):
                st.write("Test completato!")
                st.write(f"Risposte corrette (test): {st.session_state.total_correct} su {len(test_phrases)}")
                
                show_aggregated_prediction_market()  # Call to show prediction market at the end
                st.stop()
            else:
                st.experimental_rerun()

# Funzione per mostrare i grafici di prediction market
def show_aggregated_prediction_market():
    sheet = st.session_state.sheet
    if sheet is not None:
        records = sheet.get_all_records()
        df = pd.DataFrame(records)
        
        for phrase in target_phrases:
            phrase_text = phrase["frase"]
            yes_count = len(df[(df["frase"] == phrase_text) & (df["risposta"] == "Vera")])
            no_count = len(df[(df["frase"] == phrase_text) & (df["risposta"] == "Falsa")])
            
            # Calculate probabilities using LMSR
            yes_prob, no_prob = lmsr_probability(yes_count, no_count)

            # Plotting
            fig, ax = plt.subplots()
            ax.bar(["Vera", "Falsa"], [yes_prob * 100, no_prob * 100])
            ax.set_title(f"Prediction Market - {phrase_text}")
            ax.set_ylabel("Probabilità (%)")
            st.pyplot(fig)

if __name__ == "__main__":
    main()
