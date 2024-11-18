import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import random
from gspread.exceptions import APIError, GSpreadException
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

test_phrases = [
    # Frasi di Test Vere
    {"frase": "Apple Inc. (AAPL): Il titolo in data 2023-03-15 era più alto rispetto alla data 2023-03-10.", "corretta": True},
    {"frase": "Microsoft Corp. (MSFT): Il titolo in data 2023-06-20 era più basso rispetto alla data 2023-06-21.", "corretta": True},
    {"frase": "Amazon.com Inc. (AMZN): Il titolo in data 2022-12-01 era più basso rispetto alla data 2022-12-05.", "corretta": True},
    {"frase": "Tesla Inc. (TSLA): Il titolo in data 2022-09-14 era più alto rispetto alla data 2022-09-12.", "corretta": True},
    {"frase": "Alphabet Inc. (GOOGL): Il titolo in data 2023-02-20 era più alto rispetto alla data 2023-02-18.", "corretta": True},
    {"frase": "Meta Platforms Inc. (META): Il titolo in data 2023-01-15 era più basso rispetto alla data 2023-01-18.", "corretta": True},
    # Frasi di Test False
    {"frase": "Apple Inc. (AAPL): Il titolo in data 2023-03-10 era più alto rispetto alla data 2023-03-15.", "corretta": False},
    {"frase": "Microsoft Corp. (MSFT): Il titolo in data 2023-06-21 era più basso rispetto alla data 2023-06-20.", "corretta": False},
    {"frase": "Amazon.com Inc. (AMZN): Il titolo in data 2022-12-05 era più basso rispetto alla data 2022-12-01.", "corretta": False},
    {"frase": "Tesla Inc. (TSLA): Il titolo in data 2022-09-12 era più alto rispetto alla data 2022-09-14.", "corretta": False},
    {"frase": "Alphabet Inc. (GOOGL): Il titolo in data 2023-02-18 era più alto rispetto alla data 2023-02-20.", "corretta": False},
    {"frase": "Meta Platforms Inc. (META): Il titolo in data 2023-01-18 era più basso rispetto alla data 2023-01-15.", "corretta": False}
]

# Funzione LMSR per il calcolo delle probabilità
def lmsr_probability(yes_count, no_count, b=1):
    yes_score = np.exp(yes_count / b)
    no_score = np.exp(no_count / b)
    total_score = yes_score + no_score
    return yes_score / total_score, no_score / total_score

# Funzione per mostrare grafici collettivi per ciascun mercato (frasi target)
def show_market_graphs(df):
    if df is not None and not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        
        for phrase in target_phrases:
            phrase_text = phrase["frase"]
            market_df = df[df["frase"] == phrase_text].copy()
            market_df.sort_values(by="timestamp", inplace=True)
            
            if market_df.empty:
                st.warning(f"Nessun dato disponibile per la frase: {phrase_text}")
                continue
            
            # Calcolo delle probabilità LMSR nel tempo per il mercato
            probabilities = []
            for i in range(1, len(market_df) + 1):
                subset = market_df.iloc[:i]
                yes_count = len(subset[subset["risposta"] == "Vera"])
                no_count = len(subset[subset["risposta"] == "Falsa"])
                yes_prob, no_prob = lmsr_probability(yes_count, no_count)
                probabilities.append(yes_prob)
            
            # Grafico delle probabilità LMSR per il mercato
            market_df["probabilità_Vera"] = probabilities
            
            fig, ax = plt.subplots()
            ax.plot(market_df["timestamp"], market_df["probabilità_Vera"] * 100, label="Probabilità Vera (%)")
            ax.set_title(f"Andamento del Mercato: {phrase_text}")
            ax.set_xlabel("Data")
            ax.set_ylabel("Probabilità (%)")
            ax.legend()
            st.pyplot(fig)

# Funzione principale dell'app
def main():
    st.title("Test di Valutazione a intuito di Frasi Nascoste")
    sheet = st.session_state.sheet
    if sheet is not None:
        df = load_sheet_data(sheet)
        if df is not None:
            st.header("Andamento Storico dei Mercati")
            show_market_graphs(df)  # Mostra i grafici per ciascun mercato

if __name__ == "__main__":
    main()



