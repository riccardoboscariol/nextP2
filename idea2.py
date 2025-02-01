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
    {"frase": "On February 4, 2025, in the Coppa Italia football match Atalanta vs. Bologna, Atalanta will win the match.", "feedback": "Di questa frase non sappiamo se è vera o falsa"}
]

control_phrases = [
    {"frase": "On February 4, 2025, in the Coppa Italia football match Atalanta vs. Bologna, Atalanta will lose the match.", "feedback": "Di questa frase non sappiamo se è vera o falsa"}
]

# Definizione delle frasi di test con 30 frasi (15 vere e 15 false)
test_phrases = [
    # Frasi di Test Vere
    {"frase": "Napoli won against Lazio on January 20, 2024.", "corretta": True},
    {"frase": "Juventus won against Torino on January 5, 2023.", "corretta": True},
    {"frase": "Inter won against Torino on January 20, 2024.", "corretta": True},
    {"frase": "Manchester United won against Chelsea on December 30, 2023.", "corretta": True},
    {"frase": "PSG won against Lille on July 8, 2023.", "corretta": True},
    {"frase": "Marseille won against PSG on May 5, 2024.", "corretta": True},
    {"frase": "Fiorentina won against Bologna on March 15, 2024.", "corretta": True},
    {"frase": "PSG won against Marseille on May 5, 2024.", "corretta": True},
    {"frase": "Bayern Munich won against Leipzig on July 25, 2023.", "corretta": True},
    {"frase": "Napoli won against Lazio on November 10, 2023.", "corretta": True},
    {"frase": "PSG won against Lille on August 15, 2023.", "corretta": True},
    {"frase": "Bayern Munich won against Leipzig on October 10, 2023.", "corretta": True},
    {"frase": "Inter won against Roma on May 15, 2023.", "corretta": True},
    {"frase": "Bayern Munich won against Borussia Dortmund on July 30, 2024.", "corretta": True},
    
    # Frasi di Test False
    {"frase": "Barcelona won against Real Madrid on August 15, 2023.", "corretta": False},
    {"frase": "Roma won against Juventus on December 15, 2023.", "corretta": False},
    {"frase": "Manchester City won against Chelsea on October 30, 2023.", "corretta": False},
    {"frase": "Manchester City won against Liverpool on August 8, 2023.", "corretta": False},
    {"frase": "Fiorentina won against Torino on February 8, 2024.", "corretta": False},
    {"frase": "Real Madrid won against Barcelona on June 10, 2023.", "corretta": False},
    {"frase": "Barcelona won against Atletico Madrid on April 25, 2024.", "corretta": False},
    {"frase": "Borussia Dortmund won against Leipzig on October 30, 2024.", "corretta": False},
    {"frase": "Inter won against Fiorentina on April 15, 2023.", "corretta": False},
    {"frase": "Milan won against Napoli on February 8, 2024.", "corretta": False},
    {"frase": "Napoli won against Fiorentina on June 30, 2023.", "corretta": False},
    {"frase": "Milan won against Napoli on July 8, 2023.", "corretta": False},
    {"frase": "Liverpool won against Manchester United on December 15, 2023.", "corretta": False},
    {"frase": "Chelsea won against Manchester United on October 30, 2023.", "corretta": False},
    {"frase": "Arsenal won against Tottenham on January 10, 2024.", "corretta": False},
    {"frase": "Chelsea won against Tottenham on August 8, 2024.", "corretta": False}
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
        current_phrase = st.session_state.all_phrases[st.session_state.current_index]
        
        st.markdown(
            "<div style='width: 100%; height: 80px; background-color: black; color: black; text-align: center;'>"
            "Testo Nascosto Dietro il Pannello Nero</div>",
            unsafe_allow_html=True
        )
        
        risposta = st.radio(
            "Rispondi alla prossima domanda seguendo il tuo intuito. La frase nascosta dietro al rettangolo nero qui sopra è vera o falsa?", 
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
