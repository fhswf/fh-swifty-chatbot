import chainlit as cl
from langchain_openai import ChatOpenAI
from typing import cast
from helpers.tools import find_info_on_fhswf_website
from langgraph.prebuilt import create_react_agent
from helpers.prompts import prompt_langgraph
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.messages import HumanMessage

@cl.set_starters
async def set_starters():
    return [
        cl.Starter(
            label="Informatikstudiengänge",
            message="Welche Informatikstudiengänge gibt es an der FH Südwestfalen? Können Sie mir Details zu den verschiedenen Programmen und deren Schwerpunkten geben?",
            icon="/public/study.svg",
        ),
        cl.Starter(
            label="Duales Studium",
            message="Wie funktioniert das duale Studium an der FH Südwestfalen? Welche Vorteile bietet es und wie läuft die Praxisphase ab?",
            icon="/public/university.svg",
        ),
        cl.Starter(
            label="KI-Recht Prüfungsanmeldung",
            message="Wann ist die Prüfungsanmeldung für KI-Recht? Wie melde ich mich an und was sind die Voraussetzungen?",
            icon="/public/schedule.svg",
        ),
        cl.Starter(
            label="Raum P107 heute",
            message="Was findet heute in Raum P107 statt? Können Sie mir den aktuellen Belegungsplan oder Stundenplan für diesen Raum zeigen?",
            icon="/public/time.svg",
        ),
        cl.Starter(
            label="Sprechstunde Herr Gawron",
            message="Wann hat Herr Gawron Sprechstunde? Wie kann ich einen Termin vereinbaren und wo findet die Sprechstunde statt?",
            icon="/public/professor.svg",
        )
    ]

@cl.on_chat_start
async def on_chat_start():
    model = ChatOpenAI(model="gpt-4o", streaming=True)
    tools = [find_info_on_fhswf_website]
    agent = create_react_agent(
        model=model,
        tools=tools,
        prompt=prompt_langgraph
    )
    cl.user_session.set("agent_langgraph", agent)


@cl.on_message
async def main(message: cl.Message):
    agent_langgraph = cast(Runnable, cl.user_session.get("agent_langgraph"))
    langgraph_step = 0
    msg_uis = []

    async for msg, metadata  in agent_langgraph.astream(
        {"messages": [HumanMessage(message.content)]},
        stream_mode="messages",
        config=RunnableConfig(callbacks=[cl.LangchainCallbackHandler()]),
    ):
        if (metadata["langgraph_step"] != langgraph_step and metadata["langgraph_node"] != "tools" and msg.content != ''):
            langgraph_step = metadata["langgraph_step"]
            msg_ui = cl.Message(content="")
            msg_uis.append(msg_ui)

        if (
            msg.content != ''
            and metadata["langgraph_node"] != "tools"
        ):
            await msg_ui.stream_token(msg.content)

    for msg_ui in msg_uis:
        await msg_ui.send()
    