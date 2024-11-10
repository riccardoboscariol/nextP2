import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import random
from gspread.exceptions import APIError, GSpreadException
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

# Funzione per verificare e caricare i dati dal Google Sheet in DataFrame
def load_sheet_data(sheet):
    try:
        # Recupera tutti i dati dal foglio
        records = sheet.get_all_records()  # Usa questa chiamata solo se le intestazioni sono corrette e uniche
        return pd.DataFrame(records)
    except GSpreadException:
        st.error("Errore nel caricamento dei dati. Controlla che le intestazioni nel foglio siano uniche.")
        try:
            # Metodo alternativo di recupero dei dati senza utilizzare `get_all_records()`
            rows = sheet.get_all_values()
            headers = rows[0]  # Prima riga come intestazioni
            data = rows[1:]    # Dati veri e propri
            return pd.DataFrame(data, columns=headers)
        except Exception as e:
            st.error("Errore nel caricamento dei dati dal Google Sheet.")
            return None

# Definizione delle frasi target, controllo e di test
target_phrases = [
    {"frase": "Apple Inc. (AAPL): Il titolo in data 2025-05-13 sarà più basso rispetto alla data 2025-04-27.", "feedback": "Di questa frase non sappiamo se è vera o falsa"},
    {"frase": "Microsoft Corp. (MSFT): Il titolo in data 2025-05-11 sarà più basso rispetto alla data 2025-05-12.", "feedback": "Di questa frase non sappiamo se è vera o falsa"},
    {"frase": "Amazon.com Inc. (AMZN): Il titolo in data 2025-02-01 sarà più alto rispetto alla data 2025-01-28.", "feedback": "Di questa frase non sappiamo se è vera o falsa"}
]

control_phrases = [
    {"frase": "Apple Inc. (AAPL): Il titolo in data 2025-04-27 sarà più basso rispetto alla data 2025-05-13.", "feedback": "Di questa frase non sappiamo se è vera o falsa"},
    {"frase": "Microsoft Corp. (MSFT): Il titolo in data 2025-05-11 sarà più alto rispetto alla data 2025-05-15.", "feedback": "Di questa frase non sappiamo se è vera o falsa"},
    {"frase": "Amazon.com Inc. (AMZN): Il titolo in data 2025-01-28 sarà più alto rispetto alla data 2025-02-01.", "feedback": "Di questa frase non sappiamo se è vera o falsa"}
]

# Definizione delle frasi di test con 15 frasi vere e 15 frasi false
test_phrases = [
    # Frasi di Test Vere
    {"frase": "Apple Inc. (AAPL): Il titolo in data 2023-03-15 era più alto rispetto alla data 2023-03-10.", "corretta": True},
    {"frase": "Microsoft Corp. (MSFT): Il titolo in data 2023-06-20 era più basso rispetto alla data 2023-06-21.", "corretta": True},
    {"frase": "Amazon.com Inc. (AMZN): Il titolo in data 2022-12-01 era più basso rispetto alla data 2022-12-05.", "corretta": True},
    {"frase": "Tesla Inc. (TSLA): Il titolo in data 2022-09-14 era più alto rispetto alla data 2022-09-12.", "corretta": True},
    {"frase": "Alphabet Inc. (GOOGL): Il titolo in data 2023-02-20 era più alto rispetto alla data 2023-02-18.", "corretta": True},
    {"frase": "Meta Platforms Inc. (META): Il titolo in data 2023-01-15 era più basso rispetto alla data 2023-01-18.", "corretta": True},
    {"frase": "Apple Inc. (AAPL): Il titolo in data 2022-11-22 era più basso rispetto alla data 2022-11-25.", "corretta": True},
    {"frase": "Microsoft Corp. (MSFT): Il titolo in data 2022-07-10 era più alto rispetto alla data 2022-07-08.", "corretta": True},
    {"frase": "Amazon.com Inc. (AMZN): Il titolo in data 2023-04-12 era più basso rispetto alla data 2023-04-15.", "corretta": True},
    {"frase": "Tesla Inc. (TSLA): Il titolo in data 2022-10-01 era più alto rispetto alla data 2022-09-28.", "corretta": True},
    {"frase": "Alphabet Inc. (GOOGL): Il titolo in data 2022-08-30 era più basso rispetto alla data 2022-08-31.", "corretta": True},
    {"frase": "Meta Platforms Inc. (META): Il titolo in data 2023-05-01 era più alto rispetto alla data 2023-04-28.", "corretta": True},
    {"frase": "Apple Inc. (AAPL): Il titolo in data 2022-06-18 era più basso rispetto alla data 2022-06-20.", "corretta": True},
    {"frase": "Microsoft Corp. (MSFT): Il titolo in data 2023-03-05 era più alto rispetto alla data 2023-03-03.", "corretta": True},
    {"frase": "Amazon.com Inc. (AMZN): Il titolo in data 2022-11-30 era più basso rispetto alla data 2022-12-01.", "corretta": True},
    
    # Frasi di Test False
    {"frase": "Apple Inc. (AAPL): Il titolo in data 2023-03-10 era più alto rispetto alla data 2023-03-15.", "corretta": False},
    {"frase": "Microsoft Corp. (MSFT): Il titolo in data 2023-06-21 era più basso rispetto alla data 2023-06-20.", "corretta": False},
    {"frase": "Amazon.com Inc. (AMZN): Il titolo in data 2022-12-05 era più basso rispetto alla data 2022-12-01.", "corretta": False},
    {"frase": "Tesla Inc. (TSLA): Il titolo in data 2022-09-12 era più alto rispetto alla data 2022-09-14.", "corretta": False},
    {"frase": "Alphabet Inc. (GOOGL): Il titolo in data 2023-02-18 era più alto rispetto alla data 2023-02-20.", "corretta": False},
    {"frase": "Meta Platforms Inc. (META): Il titolo in data 2023-01-18 era più basso rispetto alla data 2023-01-15.", "corretta": False},
    {"frase": "Apple Inc. (AAPL): Il titolo in data 2022-11-25 era più basso rispetto alla data 2022-11-22.", "corretta": False},
    {"frase": "Microsoft Corp. (MSFT): Il titolo in data 2022-07-08 era più alto rispetto alla data 2022-07-10.", "corretta": False},
    {"frase": "Amazon.com Inc. (AMZN): Il titolo in data 2023-04-15 era più basso rispetto alla data 2023-04-12.", "corretta": False},
    {"frase": "Tesla Inc. (TSLA): Il titolo in data 2022-09-28 era più alto rispetto alla data 2022-10-01.", "corretta": False},
    {"frase": "Alphabet Inc. (GOOGL): Il titolo in data 2022-08-31 era più basso rispetto alla data 2022-08-30.", "corretta": False},
    {"frase": "Meta Platforms Inc. (META): Il titolo in data 2023-04-28 era più alto rispetto alla data 2023-05-01.", "corretta": False},
    {"frase": "Apple Inc. (AAPL): Il titolo in data 2022-06-20 era più basso rispetto alla data 2022-06-18.", "corretta": False},
    {"frase": "Microsoft Corp. (MSFT): Il titolo in data 2023-03-03 era più alto rispetto alla data 2023-03-05.", "corretta": False},
    {"frase": "Amazon.com Inc. (AMZN): Il titolo in data 2022-12-01 era più basso rispetto alla data 2022-11-30.", "corretta": False}
]


# Funzione per salvare i risultati di una singola risposta
def save_single_response(participant_id, email, frase, risposta, feedback):
    sheet = st.session_state.sheet
    if sheet is not None:
        try:
            sheet.append_row([participant_id, email, frase, risposta, feedback, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        except APIError:
            st.error("Si è verificato un problema durante il salvataggio dei dati. Riprova più tardi.")

# Funzione LMSR per il calcolo delle probabilità
def lmsr_probability(yes_count, no_count, b=1):
    yes_score = np.exp(yes_count / b)
    no_score = np.exp(no_count / b)
    total_score = yes_score + no_score
    return yes_score / total_score, no_score / total_score

# Funzione principale dell'app
def main():
    st.title("Test di Valutazione a intuito di Frasi Nascoste")

    # Input per l'ID partecipante e l'email
    participant_id = st.text_input("Inserisci il tuo ID partecipante")
    email = st.text_input("Inserisci la tua email")

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
        current_phrase = st.session_state.all_phrases[st.session_state.current_index]
        
        st.markdown(
            "<div style='width: 100%; height: 60px; background-color: black; color: black; text-align: center;'>"
            "Testo Nascosto Dietro il Pannello Nero</div>",
            unsafe_allow_html=True
        )
        
        risposta = st.radio(
            "Rispondi alla prossima domanda seguendo il tuo intuito.", 
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
                
                show_aggregated_prediction_market()
                st.stop()
            else:
                st.experimental_rerun()

# Funzione per mostrare i grafici di prediction market
def show_aggregated_prediction_market():
    sheet = st.session_state.sheet
    if sheet is not None:
        df = load_sheet_data(sheet)
        if df is not None and not df.empty:
            for phrase in target_phrases:
                phrase_text = phrase["frase"]
                yes_count = len(df[(df["frase"] == phrase_text) & (df["risposta"] == "Vera")])
                no_count = len(df[(df["frase"] == phrase_text) & (df["risposta"] == "Falsa")])
                
                # Calcola le probabilità LMSR
                yes_prob, no_prob = lmsr_probability(yes_count, no_count)

                # Creazione del grafico
                fig, ax = plt.subplots()
                ax.bar(["Vera", "Falsa"], [yes_prob * 100, no_prob * 100])
                ax.set_title(f"Prediction Market - {phrase_text}")
                ax.set_ylabel("Probabilità (%)")
                st.pyplot(fig)
        else:
            st.warning("Non sono disponibili dati sufficienti per generare i grafici di prediction market.")

if __name__ == "__main__":
    main()


