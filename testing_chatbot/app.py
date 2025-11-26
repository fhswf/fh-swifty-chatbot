#!/usr/bin/env python3
"""
Streamlit Dashboard zur Bewertung der Chatbot-Antworten.
Ermöglicht manuelle Bewertung mit Likert-Skala (1-5) und Notizen.

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

# Seitenkonfiguration
st.set_page_config(
    page_title="Chatbot Evaluation Dashboard",
    page_icon="🤖",
    layout="wide"
)

# Pfade
RESULTS_DIR = Path("testing_chatbot/test_results")
RATINGS_FILE = Path("testing_chatbot/test_results/manual_ratings.json")


def load_evaluation_results():
    """Lädt die neueste Evaluation-Datei"""
    json_files = sorted(RESULTS_DIR.glob("chatbot_evaluation_*.json"))
    
    if not json_files:
        return None
    
    # Neueste Datei nehmen
    latest_file = json_files[-1]
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data, latest_file.name


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


def main():
    st.title("🤖 Chatbot Evaluation Dashboard")
    st.markdown("---")
    
    # Daten laden
    result = load_evaluation_results()
    
    if result is None:
        st.error("Keine Evaluation-Ergebnisse gefunden!")
        st.info("Führe zuerst `python testing_chatbot/test_auswertung.py` aus.")
        return
    
    data, filename = result
    ratings = load_ratings()
    
    # Sidebar für Filterung
    st.sidebar.header("Filter")
    
    # Metadata anzeigen
    metadata = data.get("metadata", {})
    st.sidebar.markdown(f"""
    **Datei:** {filename}  
    **Institution:** {metadata.get('institution', 'N/A')}  
    **Tests:** {metadata.get('total_tests', 'N/A')}  
    **Datum:** {metadata.get('evaluation_date', 'N/A')[:10]}
    """)
    
    # Kategorien für Filter
    results = data.get("results", [])
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
    
    # Ergebnisse filtern
    filtered_results = results
    if selected_kategorie != "Alle":
        filtered_results = [r for r in filtered_results if r.get('kategorie') == selected_kategorie]
    
    if selected_typ:
        filtered_results = [r for r in filtered_results if r.get('test_typ') in selected_typ]
    
    if nur_unbewertete:
        filtered_results = [r for r in filtered_results if r.get('test_id') not in ratings]
    
    # Tabs für verschiedene Ansichten
    tab1, tab2, tab3 = st.tabs(["📝 Bewertung", "📊 Übersicht", "📈 Statistiken"])
    
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
            list(test_options.keys())
        )
        
        if selected_test:
            idx = test_options[selected_test]
            test = filtered_results[idx]
            test_id = test.get('test_id')
            
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
                st.markdown(f"**Antwortzeit:** {test.get('antwortzeit_sekunden', 'N/A')}s")
                
                tatsaechliche_antwort = test.get('tatsaechliche_antwort', 'Keine Antwort')
                st.markdown("**Tatsächliche Antwort:**")
                
                # Lange Antworten scrollbar machen
                if len(tatsaechliche_antwort) > 500:
                    st.text_area(
                        "Antwort", 
                        tatsaechliche_antwort, 
                        height=300, 
                        disabled=True
                    )
                else:
                    st.warning(tatsaechliche_antwort)
            
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
                    ratings[test_id] = {
                        'rating': rating,
                        'notes': notes,
                        'timestamp': datetime.now().isoformat(),
                        'testfrage': test.get('testfrage', ''),
                        'kategorie': test.get('kategorie', '')
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
            # Übersicht als Tabelle
            df_ratings = pd.DataFrame([
                {
                    'Test-ID': test_id,
                    'Frage': info['testfrage'][:60] + '...',
                    'Kategorie': info['kategorie'],
                    'Bewertung': info['rating'],
                    'Label': get_likert_label(info['rating']),
                    'Notizen': info.get('notes', '')[:50] + '...' if info.get('notes') else '',
                    'Datum': info.get('timestamp', '')[:10]
                }
                for test_id, info in ratings.items()
            ])
            
            # Nach Bewertung sortieren
            df_ratings = df_ratings.sort_values('Bewertung', ascending=False)
            
            st.dataframe(
                df_ratings,
                width='stretch',
                hide_index=True
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
            # Metriken
            col1, col2, col3, col4 = st.columns(4)
            
            avg_rating = sum(r['rating'] for r in ratings.values()) / len(ratings)
            
            with col1:
                st.metric("Bewertete Tests", len(ratings))
            
            with col2:
                st.metric("Durchschn. Bewertung", f"{avg_rating:.2f}")
            
            with col3:
                good_ratings = sum(1 for r in ratings.values() if r['rating'] >= 4)
                st.metric("Gute Bewertungen (≥4)", good_ratings)
            
            with col4:
                bad_ratings = sum(1 for r in ratings.values() if r['rating'] <= 2)
                st.metric("Schlechte Bewertungen (≤2)", bad_ratings)
            
            st.markdown("---")
            
            # Visualisierungen
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.subheader("Verteilung der Bewertungen")
                
                # Histogramm
                rating_counts = pd.Series([r['rating'] for r in ratings.values()]).value_counts().sort_index()
                
                fig = px.bar(
                    x=rating_counts.index,
                    y=rating_counts.values,
                    labels={'x': 'Bewertung', 'y': 'Anzahl'},
                    title="Häufigkeit der Bewertungen"
                )
                fig.update_xaxes(tickmode='linear', tick0=1, dtick=1)
                st.plotly_chart(fig, width='stretch')
            
            with col_right:
                st.subheader("Bewertungen nach Kategorie")
                
                # Durchschnitt pro Kategorie
                cat_ratings = {}
                for test_id, info in ratings.items():
                    cat = info.get('kategorie', 'Unbekannt')
                    if cat not in cat_ratings:
                        cat_ratings[cat] = []
                    cat_ratings[cat].append(info['rating'])
                
                cat_avg = {k: sum(v)/len(v) for k, v in cat_ratings.items()}
                
                fig2 = px.bar(
                    x=list(cat_avg.keys()),
                    y=list(cat_avg.values()),
                    labels={'x': 'Kategorie', 'y': 'Durchschn. Bewertung'},
                    title="Durchschnittliche Bewertung pro Kategorie"
                )
                fig2.update_yaxes(range=[0, 5])
                st.plotly_chart(fig2, width='stretch')
            
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
                kat_rated = sum(1 for r in kat_tests if r.get('test_id') in ratings)
                kat_progress = kat_rated / len(kat_tests) if kat_tests else 0
                
                st.write(f"{kategorie}: {kat_rated}/{len(kat_tests)}")
                st.progress(kat_progress)


if __name__ == "__main__":
    main()

