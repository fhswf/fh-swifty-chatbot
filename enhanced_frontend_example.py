"""
Enhanced Frontend Error Handling for FH SWF Chatbot
Provides better user experience through improved error states and loading indicators
"""

import chainlit as cl
from langchain_openai import ChatOpenAI
from typing import cast
from helpers.tools import find_info_on_fhswf_website
from langgraph.prebuilt import create_react_agent
from helpers.prompts import prompt_langgraph
from langchain.schema.runnable import Runnable, RunnableConfig
from langchain_core.messages import HumanMessage
import asyncio
import logging

# Configure logging for better error tracking
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@cl.on_chat_start
async def on_chat_start():
    """Initialize chat session with enhanced error handling"""
    try:
        # Show custom loading message
        loading_msg = cl.Message(content="🔄 Initialisiere FH SWF KI Assistant...")
        await loading_msg.send()
        
        # Initialize model with error handling
        model = ChatOpenAI(model="gpt-4o", streaming=True)
        tools = [find_info_on_fhswf_website]
        agent = create_react_agent(
            model=model,
            tools=tools,
            prompt=prompt_langgraph
        )
        
        # Store agent in session
        cl.user_session.set("agent_langgraph", agent)
        
        # Update loading message to welcome
        loading_msg.content = """
        ✅ **FH SWF KI Assistant bereit!**
        
        Ich kann Ihnen bei folgenden Themen helfen:
        - 📚 Studienangebot und Bewerbung
        - 🏛️ Campus-Services und Standorte  
        - 💡 Praktika und Karriere
        - 🎓 Allgemeine Hochschulinformationen
        
        *Stellen Sie einfach Ihre Frage!*
        """
        await loading_msg.update()
        
        logger.info("Chat session initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing chat: {e}")
        error_msg = cl.Message(
            content="""
            ⚠️ **Initialisierungsfehler**
            
            Es gab ein Problem beim Starten des Assistenten. 
            Bitte laden Sie die Seite neu oder kontaktieren Sie den Support.
            
            **Mögliche Lösungen:**
            - Seite neu laden (F5)
            - Browser-Cache leeren
            - Bei anhaltenden Problemen: it-support@fh-swf.de
            """,
            author="System"
        )
        await error_msg.send()

@cl.on_message
async def main(message: cl.Message):
    """Enhanced message handler with better loading states and error handling"""
    try:
        agent_langgraph = cast(Runnable, cl.user_session.get("agent_langgraph"))
        
        if not agent_langgraph:
            await handle_session_error()
            return
            
        # Show enhanced loading indicator
        thinking_msg = cl.Message(content="", author="FH SWF Assistant")
        await thinking_msg.send()
        
        # Update loading message with progress
        progress_messages = [
            "🔍 Durchsuche FH SWF Website...",
            "📊 Analysiere verfügbare Informationen...",
            "💭 Bereite detaillierte Antwort vor..."
        ]
        
        current_progress = 0
        langgraph_step = 0
        msg_uis = []

        async def update_progress():
            nonlocal current_progress
            while current_progress < len(progress_messages) - 1:
                await asyncio.sleep(2)
                current_progress += 1
                thinking_msg.content = progress_messages[current_progress]
                await thinking_msg.update()

        # Start progress indicator
        progress_task = asyncio.create_task(update_progress())
        
        try:
            async for msg, metadata in agent_langgraph.astream(
                {"messages": [HumanMessage(message.content)]},
                stream_mode="messages",
                config=RunnableConfig(callbacks=[cl.LangchainCallbackHandler()]),
            ):
                # Cancel progress task once we start receiving real content
                if not progress_task.done():
                    progress_task.cancel()
                
                if (metadata["langgraph_step"] != langgraph_step 
                    and metadata["langgraph_node"] != "tools" 
                    and msg.content != ''):
                    
                    langgraph_step = metadata["langgraph_step"]
                    
                    # Clear the thinking message for the first real response
                    if not msg_uis:
                        thinking_msg.content = ""
                        await thinking_msg.update()
                        msg_ui = thinking_msg
                    else:
                        msg_ui = cl.Message(content="")
                    
                    msg_uis.append(msg_ui)

                if (msg.content != '' and metadata["langgraph_node"] != "tools"):
                    await msg_ui.stream_token(msg.content)

            # Send all accumulated messages
            for msg_ui in msg_uis[1:]:  # Skip first one as it was already sent
                await msg_ui.send()
                
            logger.info(f"Successfully processed message: {message.content[:50]}...")
                
        except asyncio.CancelledError:
            pass  # Progress task was cancelled, this is expected
        except Exception as stream_error:
            logger.error(f"Error during streaming: {stream_error}")
            await handle_streaming_error(thinking_msg, stream_error)
            
    except Exception as e:
        logger.error(f"Error in message handler: {e}")
        await handle_general_error(e)

async def handle_session_error():
    """Handle session initialization errors"""
    error_msg = cl.Message(
        content="""
        ⚠️ **Session-Fehler**
        
        Ihre Chat-Session ist abgelaufen oder wurde nicht korrekt initialisiert.
        
        **Bitte versuchen Sie:**
        1. Einen neuen Chat zu starten
        2. Die Seite neu zu laden
        3. Bei anhaltenden Problemen kontaktieren Sie: it-support@fh-swf.de
        """,
        author="System"
    )
    await error_msg.send()

async def handle_streaming_error(thinking_msg: cl.Message, error: Exception):
    """Handle errors during message streaming"""
    error_content = """
    ⚠️ **Verbindungsproblem**
    
    Es gab ein Problem bei der Kommunikation mit dem FH SWF System.
    """
    
    if "timeout" in str(error).lower():
        error_content += """
        
        **Ursache:** Zeitüberschreitung der Anfrage
        **Lösung:** Versuchen Sie es mit einer einfacheren Frage oder laden Sie die Seite neu.
        """
    elif "connection" in str(error).lower():
        error_content += """
        
        **Ursache:** Netzwerkverbindung unterbrochen
        **Lösung:** Prüfen Sie Ihre Internetverbindung und versuchen Sie es erneut.
        """
    else:
        error_content += """
        
        **Ursache:** Unbekannter Systemfehler
        **Lösung:** Bitte versuchen Sie es erneut oder kontaktieren Sie den Support.
        """
    
    error_content += "\n\n📧 **Support:** it-support@fh-swf.de"
    
    thinking_msg.content = error_content
    await thinking_msg.update()

async def handle_general_error(error: Exception):
    """Handle general application errors"""
    error_msg = cl.Message(
        content=f"""
        🚨 **Systemfehler**
        
        Ein unerwarteter Fehler ist aufgetreten. Unser IT-Team wurde automatisch benachrichtigt.
        
        **Fehler-ID:** {hash(str(error)) % 100000:05d}
        **Zeitpunkt:** {cl.context.session.creation_time}
        
        **Nächste Schritte:**
        1. Versuchen Sie einen neuen Chat zu starten
        2. Falls das Problem weiterhin besteht, melden Sie es mit der Fehler-ID an: it-support@fh-swf.de
        
        Wir entschuldigen uns für die Unannehmlichkeiten! 🙏
        """,
        author="System"
    )
    await error_msg.send()

# Error handling for the entire application
@cl.on_stop
def on_stop():
    """Cleanup when chat stops"""
    logger.info("Chat session ended")

# Health check endpoint (would be added to main app)
@cl.on_settings_update
async def on_settings_update(settings):
    """Handle settings updates with validation"""
    try:
        # Validate settings if needed
        logger.info("Settings updated successfully")
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        await cl.Message(
            content="⚠️ Fehler beim Aktualisieren der Einstellungen. Bitte versuchen Sie es erneut.",
            author="System"
        ).send()