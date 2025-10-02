"""
OpenAI API Wrapper für SWiFty-Chatbot

Dieser Wrapper kapselt alle Anfragen an OpenAI und bietet eine einheitliche
Schnittstelle für die Verwendung im SWiFty-Chat. Er nutzt LangChain unter der
Haube und ermöglicht einfaches Debugging und wenige Eingriffe.
"""

from typing import Optional, Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
import logging

logger = logging.getLogger(__name__)


class OpenAIWrapper:
    """
    Wrapper-Klasse für OpenAI API-Aufrufe via LangChain.
    
    Diese Klasse bietet eine stabile Schnittstelle für OpenAI-Anfragen
    und kapselt die Konfiguration und Fehlerbehandlung.
    """
    
    def __init__(
        self,
        model: str = "gpt-4o",
        temperature: float = 0.7,
        streaming: bool = True,
        **kwargs
    ):
        """
        Initialisiert den OpenAI Wrapper.
        
        Args:
            model: Das zu verwendende OpenAI-Modell (Standard: "gpt-4o")
            temperature: Temperatur für die Antwortgenerierung (0.0-2.0, Standard: 0.7)
            streaming: Ob Streaming aktiviert sein soll (Standard: True)
            **kwargs: Weitere Parameter für ChatOpenAI
        """
        self.model_name = model
        self.temperature = temperature
        self.streaming = streaming
        self.additional_params = kwargs
        
        # Initialisiere das LangChain ChatOpenAI Modell
        self._initialize_model()
        
        logger.info(
            f"OpenAI Wrapper initialisiert mit Modell: {model}, "
            f"Temperature: {temperature}, Streaming: {streaming}"
        )
    
    def _initialize_model(self) -> None:
        """Initialisiert das ChatOpenAI Modell mit den konfigurierten Parametern."""
        try:
            self._model = ChatOpenAI(
                model=self.model_name,
                temperature=self.temperature,
                streaming=self.streaming,
                **self.additional_params
            )
            logger.debug("ChatOpenAI Modell erfolgreich initialisiert")
        except Exception as e:
            logger.error(f"Fehler bei der Initialisierung des ChatOpenAI Modells: {e}")
            raise
    
    def get_model(self) -> BaseChatModel:
        """
        Gibt das konfigurierte LangChain ChatModel zurück.
        
        Returns:
            Das konfigurierte ChatOpenAI Modell
        """
        return self._model
    
    def update_config(
        self,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        streaming: Optional[bool] = None,
        **kwargs
    ) -> None:
        """
        Aktualisiert die Konfiguration des Wrappers.
        
        Args:
            model: Neues Modell (optional)
            temperature: Neue Temperatur (optional)
            streaming: Neuer Streaming-Status (optional)
            **kwargs: Weitere Parameter für ChatOpenAI
        """
        if model is not None:
            self.model_name = model
        if temperature is not None:
            self.temperature = temperature
        if streaming is not None:
            self.streaming = streaming
        
        self.additional_params.update(kwargs)
        
        # Modell mit neuer Konfiguration neu initialisieren
        self._initialize_model()
        
        logger.info(
            f"Konfiguration aktualisiert: Modell={self.model_name}, "
            f"Temperature={self.temperature}, Streaming={self.streaming}"
        )
    
    def get_config(self) -> Dict[str, Any]:
        """
        Gibt die aktuelle Konfiguration zurück.
        
        Returns:
            Dictionary mit der aktuellen Konfiguration
        """
        return {
            "model": self.model_name,
            "temperature": self.temperature,
            "streaming": self.streaming,
            **self.additional_params
        }
    
    def __repr__(self) -> str:
        """Gibt eine String-Repräsentation des Wrappers zurück."""
        return (
            f"OpenAIWrapper(model={self.model_name}, "
            f"temperature={self.temperature}, "
            f"streaming={self.streaming})"
        )


def create_openai_wrapper(
    model: str = "gpt-4o",
    temperature: float = 0.7,
    streaming: bool = True,
    **kwargs
) -> OpenAIWrapper:
    """
    Factory-Funktion zum Erstellen eines OpenAI Wrappers.
    
    Args:
        model: Das zu verwendende OpenAI-Modell (Standard: "gpt-4o")
        temperature: Temperatur für die Antwortgenerierung (0.0-2.0, Standard: 0.7)
        streaming: Ob Streaming aktiviert sein soll (Standard: True)
        **kwargs: Weitere Parameter für ChatOpenAI
    
    Returns:
        Konfigurierter OpenAIWrapper
    """
    return OpenAIWrapper(
        model=model,
        temperature=temperature,
        streaming=streaming,
        **kwargs
    )
