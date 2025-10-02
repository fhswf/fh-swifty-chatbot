"""
Beispiele für die Verwendung des OpenAI Wrappers.

Diese Datei zeigt verschiedene Anwendungsfälle des OpenAI API Wrappers.
"""

from helpers.openai_wrapper import create_openai_wrapper, OpenAIWrapper

# Beispiel 1: Basis-Verwendung
def example_basic_usage():
    """Zeigt die grundlegende Verwendung des Wrappers."""
    print("=== Beispiel 1: Basis-Verwendung ===")
    
    # Erstelle einen Wrapper mit Standardeinstellungen
    wrapper = create_openai_wrapper()
    
    # Hole das LangChain-Modell
    model = wrapper.get_model()
    
    print(f"Wrapper erstellt: {wrapper}")
    print(f"Modell-Typ: {type(model).__name__}")
    print()


# Beispiel 2: Benutzerdefinierte Konfiguration
def example_custom_config():
    """Zeigt die Verwendung mit benutzerdefinierten Parametern."""
    print("=== Beispiel 2: Benutzerdefinierte Konfiguration ===")
    
    # Erstelle einen Wrapper mit benutzerdefinierten Einstellungen
    wrapper = create_openai_wrapper(
        model="gpt-4o-mini",
        temperature=0.5,
        streaming=False,
        max_tokens=1000
    )
    
    print(f"Wrapper: {wrapper}")
    print(f"Konfiguration: {wrapper.get_config()}")
    print()


# Beispiel 3: Konfiguration zur Laufzeit ändern
def example_runtime_config():
    """Zeigt, wie die Konfiguration zur Laufzeit geändert wird."""
    print("=== Beispiel 3: Laufzeit-Konfiguration ===")
    
    # Erstelle einen Wrapper
    wrapper = create_openai_wrapper(model="gpt-4o", temperature=0.7)
    print(f"Initial: {wrapper.get_config()}")
    
    # Aktualisiere die Konfiguration
    wrapper.update_config(
        model="gpt-4o-mini",
        temperature=0.3,
        max_tokens=500
    )
    print(f"Nach Update: {wrapper.get_config()}")
    print()


# Beispiel 4: Integration mit LangGraph (wie im agent_langgraph_app.py)
def example_langgraph_integration():
    """Zeigt die Integration mit LangGraph."""
    print("=== Beispiel 4: LangGraph Integration ===")
    
    from langgraph.prebuilt import create_react_agent
    from helpers.tools import find_info_on_fhswf_website
    from helpers.prompts import prompt_langgraph
    
    # Erstelle den Wrapper
    wrapper = create_openai_wrapper(
        model="gpt-4o",
        temperature=0.7,
        streaming=True
    )
    
    # Hole das Modell
    model = wrapper.get_model()
    
    # Erstelle den Agenten
    tools = [find_info_on_fhswf_website]
    agent = create_react_agent(
        model=model,
        tools=tools,
        prompt=prompt_langgraph
    )
    
    print(f"Agent erstellt mit Wrapper-Modell")
    print(f"Wrapper-Konfiguration: {wrapper.get_config()}")
    print()


# Beispiel 5: Wrapper-Klasse direkt verwenden
def example_direct_class_usage():
    """Zeigt die direkte Verwendung der OpenAIWrapper-Klasse."""
    print("=== Beispiel 5: Direkte Klassen-Verwendung ===")
    
    # Erstelle Wrapper direkt mit der Klasse
    wrapper = OpenAIWrapper(
        model="gpt-4o",
        temperature=0.8,
        streaming=True
    )
    
    print(f"Wrapper: {wrapper}")
    print(f"String-Repräsentation: {repr(wrapper)}")
    print()


# Beispiel 6: Erweiterte Parameter
def example_advanced_parameters():
    """Zeigt die Verwendung erweiterter Parameter."""
    print("=== Beispiel 6: Erweiterte Parameter ===")
    
    wrapper = create_openai_wrapper(
        model="gpt-4o",
        temperature=0.7,
        streaming=True,
        max_tokens=2000,
        timeout=30,
        max_retries=2,
        request_timeout=60
    )
    
    config = wrapper.get_config()
    print(f"Erweiterte Konfiguration:")
    for key, value in config.items():
        print(f"  {key}: {value}")
    print()


if __name__ == "__main__":
    # Führe alle Beispiele aus
    example_basic_usage()
    example_custom_config()
    example_runtime_config()
    example_direct_class_usage()
    example_advanced_parameters()
    
    # Hinweis: example_langgraph_integration() benötigt zusätzliche Imports
    # und kann nur im Kontext der Anwendung ausgeführt werden
    print("Hinweis: Das LangGraph-Integrationsbeispiel kann nur im Kontext")
    print("der Chainlit-Anwendung ausgeführt werden.")
