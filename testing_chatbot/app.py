#!/usr/bin/env python3
"""
Streamlit Dashboard zur Bewertung der Chatbot-Antworten.
Ermöglicht manuelle Bewertung mit Likert-Skala (1-5) und Notizen.

WICHTIG: Verwendet den Agent direkt aus agent_langgraph_app.py
- Antworten werden live vom Agent abgerufen
- Keine vorherigen Evaluation-Dateien nötig
- Testdaten werden aus JSON-Dateien geladen

Verwendung:
    streamlit run testing_chatbot/app.py
"""

import streamlit as st
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from openai import OpenAI
import time
import os
import sys
import asyncio
from dotenv import load_dotenv

# Projekt-Root zum Path hinzufügen
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "fh-swifty-chatbot"))

# Agent-Imports (wie in agent_langgraph_app.py)
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage

try:
    from helpers.tools import find_info_on_fhswf_website
    from helpers.prompts import prompt_langgraph
except ImportError as e:
    st.error(f"Import-Fehler: {e}")
    st.stop()

# .env Datei laden
load_dotenv()

# Seitenkonfiguration
st.set_page_config(
    page_title="Chatbot Evaluation Dashboard",
    page_icon="🤖",
    layout="wide"
)

# Pfade
RESULTS_DIR = Path("testing_chatbot/test_results")
RATINGS_FILE = Path("testing_chatbot/test_results/manual_ratings.json")
TEST_DATA_DIR = Path("testing_chatbot/test_data")


@st.cache_resource
def initialize_agent():
    """
    Initialisiert den Chatbot-Agent (exakt wie in agent_langgraph_app.py)
    """
    try:
        # Exakt wie in agent_langgraph_app.py Zeile 22-24
        model = ChatOpenAI(model="gpt-4o", streaming=True)  # streaming=True wie im Original
        tools = [find_info_on_fhswf_website]
        agent = create_react_agent(model=model, tools=tools, prompt=prompt_langgraph)
        return agent
    except Exception as e:
        st.error(f"Fehler beim Initialisieren des Agents: {e}")
        return None


async def ask_agent_async(agent, question: str):
    """
    Sendet eine Frage an den Agent und gibt die Antwort zurück
    (exakt wie in agent_langgraph_app.py, aber ohne Chainlit-Callbacks)
    """
    if not agent:
        return {"answer": "", "response_time": 0, "error": "Agent nicht initialisiert"}
    
    start_time = time.time()
    try:
        response_parts = []
        # Exakt wie in agent_langgraph_app.py Zeile 41-46, aber ohne Chainlit-Callbacks
        async for msg, metadata in agent.astream(
            {"messages": [HumanMessage(question)]},
            stream_mode="messages",
            # Keine Callbacks in Streamlit-Umgebung (cl.LangchainCallbackHandler() benötigt Chainlit)
        ):
            # Exakt wie in agent_langgraph_app.py Zeile 47-49
            node = (metadata or {}).get("langgraph_node")
            content = (msg.content or "")
            
            # Exakt wie in agent_langgraph_app.py Zeile 59: Nur nicht-Tool-Inhalte
            if content and node != "tools":
                response_parts.append(content)
        
        answer = "".join(response_parts).strip()
        end_time = time.time()
        response_time = end_time - start_time
        
        if not answer:
            return {
                "answer": "",
                "response_time": round(response_time, 2),
                "error": "Keine Antwort vom Agent erhalten"
            }
        
        return {
            "answer": answer,
            "response_time": round(response_time, 2),
            "error": None
        }
    except Exception as e:
        error_msg = str(e)
        # Detailliertere Fehlermeldung für Chainlit-Fehler
        if "chainlit" in error_msg.lower() or "Chainlit" in error_msg.lower() or "context not found" in error_msg.lower():
            error_msg = f"Chainlit-Kontext-Fehler: {error_msg}. Das Tool wurde bereits angepasst, um ohne Chainlit zu funktionieren. Bitte prüfe, ob helpers/tools.py korrekt ist."
        return {
            "answer": "",
            "response_time": 0,
            "error": error_msg
        }


def ask_agent(agent, question: str):
    """
    Wrapper für ask_agent_async (für Streamlit)
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(ask_agent_async(agent, question))


def load_test_data(test_data_file: str = None):
    """Lädt Testdaten aus JSON-Datei"""
    if test_data_file is None:
        # Suche nach Testdaten-Dateien
        test_files = list(TEST_DATA_DIR.glob("*.json"))
        if not test_files:
            return None
        # Verwende die erste gefundene Datei (oder die simple-Version falls vorhanden)
        simple_file = TEST_DATA_DIR / "chatbot_tests_simple.json"
        test_data_file = simple_file if simple_file.exists() else test_files[0]
    
    test_data_path = Path(test_data_file)
    if not test_data_path.exists():
        return None
    
    try:
        with open(test_data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data, test_data_path.name
    except Exception as e:
        st.error(f"Fehler beim Laden der Testdaten: {e}")
        return None


def load_ratings():
    """Lädt gespeicherte Bewertungen"""
    if RATINGS_FILE.exists():
        with open(RATINGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_ratings(ratings):
    """Speichert Bewertungen"""
    RATINGS_FILE.parent.mkdir(exist_ok=True)
    with open(RATINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(ratings, f, ensure_ascii=False, indent=2)


def get_likert_label(value):
    """Gibt das passende Label für die Likert-Skala zurück"""
    labels = {
        1: "Stimme überhaupt nicht zu",
        2: "Stimme eher nicht zu",
        3: "Teils/teils",
        4: "Stimme eher zu",
        5: "Stimme voll und ganz zu"
    }
    return labels.get(value, "Keine Bewertung")


def get_comparison_label(value):
    """Gibt das passende Label für die ChatGPT-Vergleichsbewertung zurück"""
    labels = {
        1: "sehr schlecht",
        2: "schlechter",
        3: "ähnlich",
        4: "besser",
        5: "sehr gut"
    }
    return labels.get(value, "Keine Bewertung")


def get_chatgpt_answer(api_key: str, question: str, model: str = "gpt-4o-mini") -> dict:
    """Ruft eine Antwort von ChatGPT ab"""
    try:
        # Validierung der Modell-ID
        valid_models = ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo", "gpt-4-turbo"]
        if model not in valid_models:
            return {
                'answer': None,
                'response_time': 0,
                'error': f"Ungültiges Modell: {model}. Verfügbare Modelle: {', '.join(valid_models)}"
            }
        
        if not api_key:
            return {
                'answer': None,
                'response_time': 0,
                'error': "API-Key fehlt"
            }
        
        client = OpenAI(api_key=api_key)
        
        start_time = time.time()
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Du bist ein hilfreicher Assistent für Fragen zur FH Südwestfalen."},
                {"role": "user", "content": question}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        end_time = time.time()
        
        answer = response.choices[0].message.content
        response_time = end_time - start_time
        
        return {
            'answer': answer,
            'response_time': round(response_time, 2),
            'error': None
        }
    except Exception as e:
        error_msg = str(e)
        # Detailliertere Fehlermeldung extrahieren, falls verfügbar
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                if 'error' in error_data:
                    error_msg = f"Error code: {e.status_code} - {error_data['error']}"
            except:
                pass
        
        return {
            'answer': None,
            'response_time': 0,
            'error': error_msg
        }


def main():
    st.title("🤖 Chatbot Evaluation Dashboard")
    st.markdown("**Verwendet Agent direkt aus `agent_langgraph_app.py`**")
    st.markdown("---")
    
    # Agent initialisieren
    agent = initialize_agent()
    if agent is None:
        st.error("Agent konnte nicht initialisiert werden!")
        return
    
    # Testdaten laden
    result = load_test_data()
    
    if result is None:
        st.error("Keine Testdaten gefunden!")
        st.info("Bitte Testdaten-Datei in `testing_chatbot/test_data/` ablegen.")
        return
    
    data, filename = result
    ratings = load_ratings()
    
    # Testdaten in das erwartete Format konvertieren
    if "tests" in data:
        results = data.get("tests", [])
    elif "results" in data:
        results = data.get("results", [])
    else:
        st.error("Ungültiges Testdaten-Format!")
        return
    
    # Sidebar für Filterung
    st.sidebar.header("Filter")
    
    # Metadata anzeigen
    metadata = data.get("metadata", {})
    st.sidebar.markdown(f"""
    **Testdaten:** {filename}  
    **Institution:** {metadata.get('institution', 'N/A')}  
    **Tests:** {len(results)}  
    **Agent:** agent_langgraph_app.py
    """)
    kategorien = sorted(set(r.get('kategorie', 'Unbekannt') for r in results))
    
    selected_kategorie = st.sidebar.selectbox(
        "Kategorie wählen:",
        ["Alle"] + kategorien
    )
    
    # Test-Typ Filter
    test_typen = sorted(set(r.get('test_typ', 'Unbekannt') for r in results))
    selected_typ = st.sidebar.multiselect(
        "Test-Typ:",
        test_typen,
        default=test_typen
    )
    
    # Nur unbewertete Tests?
    nur_unbewertete = st.sidebar.checkbox("Nur unbewertete Tests zeigen")
    
    # ChatGPT API Key aus .env laden
    chatgpt_api_key = os.getenv("OPENAI_API_KEY")
    if not chatgpt_api_key:
        st.sidebar.error("⚠️ OPENAI_API_KEY nicht in .env gefunden!")
    
    # ChatGPT Modell-Auswahl
    st.sidebar.markdown("---")
    st.sidebar.header("ChatGPT Vergleich")
    chatgpt_model = st.sidebar.selectbox(
        "ChatGPT Modell:",
        ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
        index=0
    )
    
    # Ergebnisse filtern
    filtered_results = results
    if selected_kategorie != "Alle":
        filtered_results = [r for r in filtered_results if r.get('kategorie') == selected_kategorie]
    
    if selected_typ:
        filtered_results = [r for r in filtered_results if r.get('test_typ') in selected_typ]
    
    if nur_unbewertete:
        filtered_results = [r for r in filtered_results if r.get('test_id') not in ratings]
    
    # Tabs für verschiedene Ansichten
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Bewertung", "📊 Übersicht", "📈 Statistiken", "🤖 ChatGPT Vergleich"])
    
    # Tab 1: Bewertung
    with tab1:
        st.header("Manuelle Bewertung")
        
        if not filtered_results:
            st.warning("Keine Tests gefunden, die den Filterkriterien entsprechen.")
            return
        
        # Test-Auswahl
        test_options = {
            f"{r.get('test_id')} - {r.get('testfrage', '')[:50]}...": i 
            for i, r in enumerate(filtered_results)
        }
        
        selected_test = st.selectbox(
            f"Test wählen ({len(filtered_results)} Tests):",
            list(test_options.keys()),
            key="test_select_rating"
        )
        
        if selected_test:
            idx = test_options[selected_test]
            test = filtered_results[idx]
            # Test-ID kann 'test_id' oder 'id' sein
            test_id = test.get('test_id') or test.get('id')
            
            # Test-Details anzeigen
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.subheader("Test-Information")
                st.markdown(f"""
                **Test-ID:** {test_id}  
                **Kategorie:** {test.get('kategorie', 'N/A')}  
                **Test-Typ:** {test.get('test_typ', 'N/A')}  
                **Subkategorie:** {test.get('subkategorie', 'N/A')}
                """)
                
                st.markdown("**Testfrage:**")
                st.info(test.get('testfrage', 'N/A'))
                
                st.markdown("**Erwartete Antwort:**")
                st.success(test.get('erwartete_antwort', 'N/A'))
            
            with col2:
                st.subheader("Chatbot-Antwort")
                
                # Antwort live vom Agent abrufen
                testfrage = test.get('testfrage', '')
                saved_rating = ratings.get(test_id, {})
                bot_answer = saved_rating.get('bot_answer', '')
                bot_response_time = saved_rating.get('bot_response_time', None)
                
                # Button zum Abrufen der Antwort
                if not bot_answer:
                    if st.button("🔄 Antwort vom Agent abrufen", key=f"fetch_{test_id}"):
                        with st.spinner("Agent wird befragt..."):
                            response = ask_agent(agent, testfrage)
                            if response['error']:
                                st.error(f"❌ Fehler: {response['error']}")
                            else:
                                # Antwort speichern
                                if test_id not in ratings:
                                    ratings[test_id] = {
                                        'rating': None,
                                        'notes': '',
                                        'timestamp': datetime.now().isoformat(),
                                        'testfrage': testfrage,
                                        'kategorie': test.get('kategorie', ''),
                                    }
                                ratings[test_id]['bot_answer'] = response['answer']
                                ratings[test_id]['bot_response_time'] = response['response_time']
                                save_ratings(ratings)
                                st.rerun()
                    st.info("Klicke auf 'Antwort vom Agent abrufen', um die Antwort live zu erhalten.")
                else:
                    # Ratings neu laden, um sicherzustellen, dass wir die neueste Version haben
                    ratings = load_ratings()
                    saved_rating = ratings.get(test_id, {})
                    bot_answer = saved_rating.get('bot_answer', '')
                    bot_response_time = saved_rating.get('bot_response_time', None)
                    
                    # Antwort anzeigen
                    st.markdown(f"**Antwortzeit:** {bot_response_time}s")
                    st.markdown("**Tatsächliche Antwort:**")
                    
                    # Lange Antworten scrollbar machen
                    if len(bot_answer) > 500:
                        st.text_area(
                            "Antwort", 
                            bot_answer, 
                            height=300, 
                            disabled=True,
                            key=f"answer_{test_id}"
                        )
                    else:
                        st.warning(bot_answer)
                    
                    # Button zum erneuten Abrufen
                    if st.button("🔄 Antwort erneut abrufen", key=f"refetch_{test_id}", type="secondary"):
                        with st.spinner("Agent wird befragt..."):
                            response = ask_agent(agent, testfrage)
                            if response['error']:
                                st.error(f"❌ Fehler: {response['error']}")
                            else:
                                # Antwort aktualisieren
                                if test_id not in ratings:
                                    ratings[test_id] = {
                                        'rating': None,
                                        'notes': '',
                                        'timestamp': datetime.now().isoformat(),
                                        'testfrage': testfrage,
                                        'kategorie': test.get('kategorie', ''),
                                    }
                                ratings[test_id]['bot_answer'] = response['answer']
                                ratings[test_id]['bot_response_time'] = response['response_time']
                                save_ratings(ratings)
                                # Erfolgsmeldung und sofortige Anzeige der neuen Antwort
                                st.success(f"✅ Antwort aktualisiert! ({response['response_time']}s)")
                                # Neue Antwort sofort anzeigen
                                st.markdown("**Neue Antwort:**")
                                if len(response['answer']) > 500:
                                    st.text_area(
                                        "Aktualisierte Antwort",
                                        response['answer'],
                                        height=300,
                                        disabled=True,
                                        key=f"new_answer_{test_id}"
                                    )
                                else:
                                    st.info(response['answer'])
                                # Seite neu laden, um aktualisierte Antwort dauerhaft anzuzeigen
                                st.rerun()
            
            st.markdown("---")
            
            # Bewertungsbereich
            st.subheader("Bewertung")
            
            # Vorherige Bewertung laden, falls vorhanden
            previous_rating = ratings.get(test_id, {})
            
            col_rating, col_notes = st.columns([1, 2])
            
            with col_rating:
                st.markdown("**Likert-Skala Bewertung**")
                st.caption("1 = Stimme überhaupt nicht zu, 5 = Stimme voll und ganz zu")
                
                rating = st.radio(
                    "Wie gut entspricht die Antwort der Erwartung?",
                    options=[1, 2, 3, 4, 5],
                    index=previous_rating.get('rating', 3) - 1 if previous_rating else 2,
                    format_func=lambda x: f"{x} - {get_likert_label(x)}",
                    key=f"rating_{test_id}"
                )
                
                # Visuelle Darstellung
                st.progress(rating / 5)
            
            with col_notes:
                st.markdown("**Notizen & Begründung**")
                notes = st.text_area(
                    "Begründung für die Bewertung:",
                    value=previous_rating.get('notes', ''),
                    height=150,
                    placeholder="Warum diese Bewertung? Was fehlt? Was ist gut?",
                    key=f"notes_{test_id}"
                )
            
            # Speichern-Button
            col_save, col_info = st.columns([1, 3])
            
            with col_save:
                if st.button("💾 Bewertung speichern", type="primary"):
                    # Bot-Antwort aus gespeicherten Ratings holen, falls vorhanden
                    existing_bot_answer = ratings.get(test_id, {}).get('bot_answer', '')
                    existing_bot_time = ratings.get(test_id, {}).get('bot_response_time', None)
                    
                    ratings[test_id] = {
                        'rating': rating,
                        'notes': notes,
                        'timestamp': datetime.now().isoformat(),
                        'testfrage': test.get('testfrage', ''),
                        'kategorie': test.get('kategorie', ''),
                        'bot_answer': existing_bot_answer,
                        'bot_response_time': existing_bot_time
                    }
                    save_ratings(ratings)
                    st.success("✅ Bewertung gespeichert!")
            
            with col_info:
                if test_id in ratings:
                    prev = ratings[test_id]
                    st.info(f"🕒 Letzte Bewertung: {prev.get('timestamp', 'N/A')[:19]}")
    
    # Tab 2: Übersicht
    with tab2:
        st.header("Bewertungs-Übersicht")
        
        if not ratings:
            st.info("Noch keine Bewertungen vorhanden. Starte mit der Bewertung im ersten Tab!")
        else:
            # Option zum Ein-/Ausblenden von Spalten
            st.markdown("**Spalten-Filter:**")
            col_filter1, col_filter2, col_filter3 = st.columns(3)
            
            with col_filter1:
                show_basic = st.checkbox("Basis-Informationen", value=True)
            with col_filter2:
                show_answers = st.checkbox("Antworten & Zeiten", value=True)
            with col_filter3:
                show_comparison = st.checkbox("ChatGPT-Vergleich", value=True)
            
            st.markdown("---")
            # Übersicht als Tabelle mit erweiterten Informationen
            table_data = []
            for test_id, info in ratings.items():
                # ChatGPT-Vergleichsdaten
                chatgpt_comparison = info.get('chatgpt_comparison', {})
                bot_answer = info.get('bot_answer', '')
                gpt_answer = chatgpt_comparison.get('answer', '')
                bot_time = info.get('bot_response_time', None)
                gpt_time = chatgpt_comparison.get('response_time', None)
                
                # KPIs berechnen
                bot_len = len(bot_answer) if bot_answer else 0
                gpt_len = len(gpt_answer) if gpt_answer else 0
                len_diff = bot_len - gpt_len if (bot_answer and gpt_answer) else None
                time_diff = None
                if isinstance(bot_time, (int, float)) and isinstance(gpt_time, (int, float)):
                    time_diff = bot_time - gpt_time
                
                # Vergleichsbewertung
                comparison_rating = chatgpt_comparison.get('comparison_rating', None)
                comparison_label = get_comparison_label(comparison_rating) if comparison_rating else 'N/A'
                
                # ChatGPT-Modell
                chatgpt_model = chatgpt_comparison.get('model', 'N/A')
                
                table_data.append({
                    'Test-ID': test_id,
                    'Frage': info.get('testfrage', '')[:50] + '...' if info.get('testfrage') and len(info.get('testfrage', '')) > 50 else (info.get('testfrage', '') or 'N/A'),
                    'Kategorie': info.get('kategorie', 'N/A'),
                    'Bewertung': info.get('rating', 'N/A'),
                    'Label': get_likert_label(info.get('rating')) if info.get('rating') is not None else 'Keine Bewertung',
                    'Bot Antwort': bot_answer[:80] + '...' if bot_answer and len(bot_answer) > 80 else (bot_answer or 'N/A'),
                    'Bot Zeit (s)': f"{bot_time:.2f}" if isinstance(bot_time, (int, float)) else 'N/A',
                    'Bot Zeichen': f"{bot_len:,}" if bot_answer else 'N/A',
                    'ChatGPT Modell': chatgpt_model,
                    'ChatGPT Antwort': gpt_answer[:80] + '...' if gpt_answer and len(gpt_answer) > 80 else (gpt_answer or 'N/A'),
                    'ChatGPT Zeit (s)': f"{gpt_time:.2f}" if isinstance(gpt_time, (int, float)) else 'N/A',
                    'ChatGPT Zeichen': f"{gpt_len:,}" if gpt_answer else 'N/A',
                    'Zeichen-Diff': f"{len_diff:+,}" if len_diff is not None else 'N/A',
                    'Zeit-Diff (s)': f"{time_diff:+.2f}" if time_diff is not None else 'N/A',
                    'Vergleichs-Bewertung': str(comparison_rating) if comparison_rating else 'N/A',
                    'Vergleichs-Label': comparison_label,
                    'Notizen': info.get('notes', '')[:40] + '...' if info.get('notes') and len(info.get('notes', '')) > 40 else (info.get('notes', '') or ''),
                    'Datum': info.get('timestamp', '')[:10] if info.get('timestamp') else 'N/A'
                })
            
            df_ratings = pd.DataFrame(table_data)
            
            # Spalten basierend auf Filtern auswählen
            base_columns = ['Test-ID', 'Frage', 'Kategorie', 'Bewertung', 'Label', 'Notizen', 'Datum']
            answer_columns = ['Bot Antwort', 'Bot Zeit (s)', 'Bot Zeichen', 'ChatGPT Modell', 'ChatGPT Antwort', 'ChatGPT Zeit (s)', 'ChatGPT Zeichen']
            comparison_columns = ['Zeichen-Diff', 'Zeit-Diff (s)', 'Vergleichs-Bewertung', 'Vergleichs-Label']
            
            columns_to_show = []
            if show_basic:
                columns_to_show.extend(base_columns)
            if show_answers:
                columns_to_show.extend(answer_columns)
            if show_comparison:
                columns_to_show.extend(comparison_columns)
            
            # Nur Spalten anzeigen, die auch im DataFrame existieren
            available_columns = [col for col in columns_to_show if col in df_ratings.columns]
            df_display = df_ratings[available_columns] if available_columns else df_ratings
            
            # Nach Bewertung sortieren (N/A-Werte nach hinten)
            if 'Bewertung' in df_display.columns:
                df_display['Bewertung_Sort'] = df_display['Bewertung'].apply(lambda x: float('-inf') if x == 'N/A' or x is None else x)
                df_display = df_display.sort_values('Bewertung_Sort', ascending=False)
                df_display = df_display.drop(columns=['Bewertung_Sort'])
            
            # Spaltenbreiten anpassen für bessere Lesbarkeit
            st.dataframe(
                df_display,
                width='stretch',
                hide_index=True,
                use_container_width=True
            )
            
            # Download-Button für Bewertungen
            st.download_button(
                label="📥 Bewertungen als JSON herunterladen",
                data=json.dumps(ratings, ensure_ascii=False, indent=2),
                file_name=f"manual_ratings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    # Tab 3: Statistiken
    with tab3:
        st.header("Statistiken & Visualisierungen")
        
        if not ratings:
            st.info("Noch keine Bewertungen vorhanden.")
        else:
            # Metriken - nur Bewertungen mit tatsächlichem rating (nicht None)
            valid_ratings = [r['rating'] for r in ratings.values() if r.get('rating') is not None]
            
            # ChatGPT-Vergleichsbewertungen
            chatgpt_comparison_ratings = []
            for r in ratings.values():
                comp = r.get('chatgpt_comparison', {})
                if comp.get('comparison_rating') is not None:
                    chatgpt_comparison_ratings.append(comp.get('comparison_rating'))
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Bewertete Tests", len(valid_ratings))
                if chatgpt_comparison_ratings:
                    st.markdown(f'<span style="color: green;">ChatGPT: {len(chatgpt_comparison_ratings)}</span>', unsafe_allow_html=True)
            
            with col2:
                if valid_ratings:
                    avg_rating = sum(valid_ratings) / len(valid_ratings)
                    st.metric("Durchschn. Bewertung", f"{avg_rating:.2f}")
                    if chatgpt_comparison_ratings:
                        avg_chatgpt = sum(chatgpt_comparison_ratings) / len(chatgpt_comparison_ratings)
                        st.markdown(f'<span style="color: green;">ChatGPT: {avg_chatgpt:.2f}</span>', unsafe_allow_html=True)
                else:
                    st.metric("Durchschn. Bewertung", "N/A")
            
            with col3:
                good_ratings = sum(1 for r in valid_ratings if r >= 4)
                st.metric("Gute Bewertungen (≥4)", good_ratings)
                if chatgpt_comparison_ratings:
                    good_chatgpt = sum(1 for r in chatgpt_comparison_ratings if r >= 4)
                    st.markdown(f'<span style="color: green;">ChatGPT: {good_chatgpt}</span>', unsafe_allow_html=True)
            
            with col4:
                bad_ratings = sum(1 for r in valid_ratings if r <= 2)
                st.metric("Schlechte Bewertungen (≤2)", bad_ratings)
                if chatgpt_comparison_ratings:
                    bad_chatgpt = sum(1 for r in chatgpt_comparison_ratings if r <= 2)
                    st.markdown(f'<span style="color: green;">ChatGPT: {bad_chatgpt}</span>', unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Visualisierungen
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.subheader("Verteilung der Bewertungen")
                
                # Histogramm - nur gültige Bewertungen
                if valid_ratings or chatgpt_comparison_ratings:
                    # Daten für beide Bewertungen vorbereiten
                    rating_counts = pd.Series(valid_ratings).value_counts().sort_index() if valid_ratings else pd.Series()
                    chatgpt_counts = pd.Series(chatgpt_comparison_ratings).value_counts().sort_index() if chatgpt_comparison_ratings else pd.Series()
                    
                    # Alle möglichen Bewertungswerte (1-5)
                    all_ratings = sorted(set(list(rating_counts.index) + list(chatgpt_counts.index)))
                    
                    fig = go.Figure()
                    
                    # Eigene Bewertungen
                    if not rating_counts.empty:
                        fig.add_trace(go.Bar(
                            x=all_ratings,
                            y=[rating_counts.get(r, 0) for r in all_ratings],
                            name='Eigener Bot',
                            marker_color='lightblue'
                        ))
                    
                    # ChatGPT-Bewertungen
                    if not chatgpt_counts.empty:
                        fig.add_trace(go.Bar(
                            x=all_ratings,
                            y=[chatgpt_counts.get(r, 0) for r in all_ratings],
                            name='ChatGPT Vergleich',
                            marker_color='lightgreen'
                        ))
                    
                    fig.update_layout(
                        xaxis_title='Bewertung',
                        yaxis_title='Anzahl',
                        title="Häufigkeit der Bewertungen",
                        barmode='group',
                        xaxis=dict(tickmode='linear', tick0=1, dtick=1)
                    )
                    st.plotly_chart(fig, width='stretch')
                else:
                    st.info("Keine Bewertungen vorhanden für Visualisierung.")
            
            with col_right:
                st.subheader("Bewertungen nach Kategorie")
                
                # Durchschnitt pro Kategorie - nur gültige Bewertungen
                cat_ratings = {}
                cat_chatgpt_ratings = {}
                
                for test_id, info in ratings.items():
                    cat = info.get('kategorie', 'Unbekannt')
                    
                    # Eigene Bewertungen
                    rating = info.get('rating')
                    if rating is not None:
                        if cat not in cat_ratings:
                            cat_ratings[cat] = []
                        cat_ratings[cat].append(rating)
                    
                    # ChatGPT-Vergleichsbewertungen
                    comp = info.get('chatgpt_comparison', {})
                    comp_rating = comp.get('comparison_rating')
                    if comp_rating is not None:
                        if cat not in cat_chatgpt_ratings:
                            cat_chatgpt_ratings[cat] = []
                        cat_chatgpt_ratings[cat].append(comp_rating)
                
                if cat_ratings or cat_chatgpt_ratings:
                    # Alle Kategorien sammeln
                    all_cats = sorted(set(list(cat_ratings.keys()) + list(cat_chatgpt_ratings.keys())))
                    
                    cat_avg = {k: sum(v)/len(v) for k, v in cat_ratings.items()}
                    cat_chatgpt_avg = {k: sum(v)/len(v) for k, v in cat_chatgpt_ratings.items()}
                    
                    fig2 = go.Figure()
                    
                    # Eigene Bewertungen
                    if cat_avg:
                        fig2.add_trace(go.Bar(
                            x=all_cats,
                            y=[cat_avg.get(cat, 0) for cat in all_cats],
                            name='Eigener Bot',
                            marker_color='lightblue'
                        ))
                    
                    # ChatGPT-Bewertungen
                    if cat_chatgpt_avg:
                        fig2.add_trace(go.Bar(
                            x=all_cats,
                            y=[cat_chatgpt_avg.get(cat, 0) for cat in all_cats],
                            name='ChatGPT Vergleich',
                            marker_color='lightgreen'
                        ))
                    
                    fig2.update_layout(
                        xaxis_title='Kategorie',
                        yaxis_title='Durchschn. Bewertung',
                        title="Durchschnittliche Bewertung pro Kategorie",
                        barmode='group',
                        yaxis=dict(range=[0, 5])
                    )
                    st.plotly_chart(fig2, width='stretch')
                else:
                    st.info("Keine Bewertungen vorhanden für Visualisierung.")
            
            # Fortschritt
            st.markdown("---")
            st.subheader("Bewertungsfortschritt")
            
            total_tests = len(results)
            rated_tests = len(ratings)
            progress = rated_tests / total_tests if total_tests > 0 else 0
            
            st.progress(progress)
            st.write(f"**{rated_tests} von {total_tests} Tests bewertet** ({progress*100:.1f}%)")
            
            # Kategorie-Fortschritt
            st.markdown("**Fortschritt nach Kategorie:**")
            
            for kategorie in kategorien:
                kat_tests = [r for r in results if r.get('kategorie') == kategorie]
                kat_rated = sum(1 for r in kat_tests if r.get('test_id') in ratings and ratings[r.get('test_id')].get('rating') is not None)
                kat_progress = kat_rated / len(kat_tests) if kat_tests else 0
                
                # ChatGPT-Vergleichsfortschritt
                kat_chatgpt_rated = sum(1 for r in kat_tests 
                                        if r.get('test_id') in ratings 
                                        and ratings[r.get('test_id')].get('chatgpt_comparison', {}).get('comparison_rating') is not None)
                kat_chatgpt_progress = kat_chatgpt_rated / len(kat_tests) if kat_tests else 0
                
                col_kat1, col_kat2 = st.columns([3, 1])
                with col_kat1:
                    st.write(f"**{kategorie}**")
                    st.write(f"Eigener Bot: {kat_rated}/{len(kat_tests)} ({kat_progress*100:.1f}%)")
                    st.progress(kat_progress)
                with col_kat2:
                    st.markdown(f'<span style="color: green;">ChatGPT: {kat_chatgpt_rated}/{len(kat_tests)}</span>', unsafe_allow_html=True)
                    st.progress(kat_chatgpt_progress)
                
                st.markdown("---")
    
    # Tab 4: ChatGPT Vergleich
    with tab4:
        st.header("ChatGPT Vergleich")
        
        if not chatgpt_api_key:
            st.error("⚠️ OPENAI_API_KEY nicht gefunden!")
            st.info("💡 Bitte füge `OPENAI_API_KEY=sk-...` in die `.env` Datei im Projekt-Root ein.")
            st.code("OPENAI_API_KEY=sk-your-api-key-here", language="env")
            return
        
        # Nur Tests anzeigen, die bereits bewertet wurden (rating ist nicht None)
        rated_test_ids = [test_id for test_id, info in ratings.items() if info.get('rating') is not None]
        
        if not rated_test_ids:
            st.warning("⚠️ Keine bewerteten Tests gefunden!")
            st.info("💡 Bitte bewerte zuerst Tests im Tab 'Bewertung', bevor du sie hier vergleichen kannst.")
            return
        
        # Gefilterte Ergebnisse: nur bewertete Tests
        rated_results = [r for r in results if r.get('test_id') in rated_test_ids]
        
        # Weitere Filter anwenden
        if selected_kategorie != "Alle":
            rated_results = [r for r in rated_results if r.get('kategorie') == selected_kategorie]
        
        if selected_typ:
            rated_results = [r for r in rated_results if r.get('test_typ') in selected_typ]
        
        if not rated_results:
            st.warning("Keine bewerteten Tests gefunden, die den Filterkriterien entsprechen.")
            return
        
        # Test-Auswahl
        test_options = {
            f"{r.get('test_id')} - {r.get('testfrage', '')[:50]}...": i 
            for i, r in enumerate(rated_results)
        }
        
        selected_test = st.selectbox(
            f"Test wählen ({len(rated_results)} bewertete Tests):",
            list(test_options.keys()),
            key="test_select_chatgpt"
        )
        
        if selected_test:
            idx = test_options[selected_test]
            test = rated_results[idx]
            test_id = test.get('test_id')
            testfrage = test.get('testfrage', '')
            
            # Gespeicherte Bewertung laden
            saved_rating = ratings.get(test_id, {})
            
            # Test-Informationen anzeigen
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.subheader("Test-Information")
                st.markdown(f"""
                **Test-ID:** {test_id}  
                **Kategorie:** {test.get('kategorie', 'N/A')}  
                **Test-Typ:** {test.get('test_typ', 'N/A')}
                """)
                st.markdown("**Testfrage:**")
                st.info(testfrage)
            
            with col2:
                st.subheader("Erwartete Antwort")
                st.success(test.get('erwartete_antwort', 'N/A'))
            
            st.markdown("---")
            
            # Antworten vergleichen
            col_bot, col_gpt = st.columns([1, 1])
            
            with col_bot:
                st.subheader("Eigener Chatbot")
                # Antwort aus gespeicherten Ratings laden
                bot_answer = saved_rating.get('bot_answer', 'Keine Antwort gespeichert')
                bot_time = saved_rating.get('bot_response_time', 'N/A')
                st.caption(f"Antwortzeit: {bot_time}s")
                
                if len(bot_answer) > 500:
                    st.text_area(
                        "Antwort",
                        bot_answer,
                        height=300,
                        disabled=True,
                        key="bot_answer"
                    )
                else:
                    st.info(bot_answer)
            
            with col_gpt:
                st.subheader("ChatGPT")
                
                # Prüfen ob bereits eine ChatGPT-Antwort vorhanden ist
                chatgpt_data = saved_rating.get('chatgpt_comparison', {})
                
                if chatgpt_data and chatgpt_data.get('answer'):
                    # Vorhandene Antwort anzeigen
                    gpt_answer = chatgpt_data.get('answer', '')
                    gpt_time = chatgpt_data.get('response_time', 'N/A')
                    st.caption(f"Antwortzeit: {gpt_time}s")
                    
                    if len(gpt_answer) > 500:
                        st.text_area(
                            "Antwort",
                            gpt_answer,
                            height=300,
                            disabled=True,
                            key="gpt_answer"
                        )
                    else:
                        st.success(gpt_answer)
                    
                    st.info(f"🕒 Abgerufen: {chatgpt_data.get('timestamp', '')[:19]}")
                else:
                    st.info("Noch keine ChatGPT-Antwort abgerufen.")
            
            # KPIs anzeigen, wenn beide Antworten vorhanden sind
            if bot_answer and bot_answer != 'Keine Antwort gespeichert' and chatgpt_data and chatgpt_data.get('answer'):
                st.markdown("---")
                st.subheader("📊 KPIs")
                
                gpt_answer = chatgpt_data.get('answer', '')
                gpt_time = chatgpt_data.get('response_time', 0)
                
                # KPI-Metriken
                col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
                
                with col_kpi1:
                    bot_len = len(bot_answer)
                    st.metric("Eigener Bot - Zeichen", f"{bot_len:,}")
                
                with col_kpi2:
                    gpt_len = len(gpt_answer)
                    st.metric("ChatGPT - Zeichen", f"{gpt_len:,}")
                
                with col_kpi3:
                    len_diff = bot_len - gpt_len
                    st.metric("Zeichen-Differenz", f"{len_diff:+,}", delta=f"{abs(len_diff)} Zeichen")
                
                with col_kpi4:
                    if isinstance(bot_time, (int, float)) and isinstance(gpt_time, (int, float)):
                        time_diff = bot_time - gpt_time
                        st.metric("Antwortzeit-Differenz", f"{time_diff:+.2f}s", delta=f"{abs(time_diff):.2f}s")
                    else:
                        st.metric("Antwortzeit-Differenz", "N/A")
            
            # Button zum Abrufen der ChatGPT-Antwort
            if st.button("🔄 ChatGPT-Antwort abrufen", type="primary"):
                with st.spinner("ChatGPT-Antwort wird abgerufen..."):
                    # Sicherstellen, dass ein gültiges Modell verwendet wird
                    model_to_use = chatgpt_model if chatgpt_model and chatgpt_model != 'N/A' else "gpt-4o-mini"
                    chatgpt_response = get_chatgpt_answer(chatgpt_api_key, testfrage, model_to_use)
                    
                    if chatgpt_response['error']:
                        st.error(f"❌ Fehler: {chatgpt_response['error']}")
                    else:
                        st.success("✅ ChatGPT-Antwort erfolgreich abgerufen!")
                        
                        # Ratings neu laden, um sicherzustellen, dass wir die neueste Version haben
                        ratings = load_ratings()
                        
                        # Vorhandene Bewertung beibehalten, falls vorhanden
                        if test_id not in ratings:
                            ratings[test_id] = {
                                'rating': None,
                                'notes': '',
                                'timestamp': datetime.now().isoformat(),
                                'testfrage': testfrage,
                                'kategorie': test.get('kategorie', ''),
                                'bot_answer': saved_rating.get('bot_answer', ''),
                                'bot_response_time': saved_rating.get('bot_response_time', None)
                            }
                        else:
                            # Sicherstellen, dass bot_answer und bot_response_time erhalten bleiben
                            if 'bot_answer' not in ratings[test_id]:
                                ratings[test_id]['bot_answer'] = saved_rating.get('bot_answer', '')
                            if 'bot_response_time' not in ratings[test_id]:
                                ratings[test_id]['bot_response_time'] = saved_rating.get('bot_response_time', None)
                        
                        ratings[test_id]['chatgpt_comparison'] = {
                            'answer': chatgpt_response['answer'],
                            'response_time': chatgpt_response['response_time'],
                            'model': chatgpt_model,
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        save_ratings(ratings)
                        st.rerun()
            
            # Daten nach dem Speichern neu laden
            ratings = load_ratings()
            saved_rating = ratings.get(test_id, {})
            chatgpt_data = saved_rating.get('chatgpt_comparison', {})
            
            # Vergleich anzeigen, wenn beide Antworten vorhanden
            if chatgpt_data and chatgpt_data.get('answer') and bot_answer:
                st.markdown("---")
                st.subheader("📊 Vergleich")
                
                # Vergleichsbewertung
                col_comp, col_notes = st.columns([1, 2])
                
                with col_comp:
                    st.markdown("**Vergleichsbewertung**")
                    st.caption("Wie gut ist die eigene Antwort im Vergleich zu ChatGPT?")
                    
                    comparison_rating = st.radio(
                        "Bewertung:",
                        options=[1, 2, 3, 4, 5],
                        index=chatgpt_data.get('comparison_rating', 3) - 1 if chatgpt_data.get('comparison_rating') else 2,
                        format_func=lambda x: f"{x} - {get_comparison_label(x)}",
                        key=f"comp_rating_{test_id}"
                    )
                    
                    st.progress(comparison_rating / 5)
                
                with col_notes:
                    st.markdown("**Vergleichsnotizen**")
                    comparison_notes = st.text_area(
                        "Notizen zum Vergleich:",
                        value=chatgpt_data.get('comparison_notes', ''),
                        height=150,
                        placeholder="Was ist besser/schlechter? Welche Unterschiede gibt es?",
                        key=f"comp_notes_{test_id}"
                    )
                
                # Speichern-Button für Vergleich
                if st.button("💾 Vergleich speichern", type="primary", key=f"save_comp_{test_id}"):
                    # Ratings neu laden, um sicherzustellen, dass wir die neueste Version haben
                    ratings = load_ratings()
                    
                    if test_id not in ratings:
                        ratings[test_id] = saved_rating.copy() if saved_rating else {
                            'rating': None,
                            'notes': '',
                            'timestamp': datetime.now().isoformat(),
                            'testfrage': testfrage,
                            'kategorie': test.get('kategorie', '')
                        }
                    
                    if 'chatgpt_comparison' not in ratings[test_id]:
                        ratings[test_id]['chatgpt_comparison'] = chatgpt_data.copy() if chatgpt_data else {}
                    
                    ratings[test_id]['chatgpt_comparison']['comparison_rating'] = comparison_rating
                    ratings[test_id]['chatgpt_comparison']['comparison_notes'] = comparison_notes
                    ratings[test_id]['chatgpt_comparison']['comparison_timestamp'] = datetime.now().isoformat()
                    
                    save_ratings(ratings)
                    st.success("✅ Vergleich gespeichert!")
                    st.rerun()


if __name__ == "__main__":
    main()

