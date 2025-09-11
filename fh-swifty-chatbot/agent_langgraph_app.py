import chainlit as cl
from langchain_openai import ChatOpenAI
from typing import cast
from helpers.tools import find_info_on_fhswf_website
from langgraph.prebuilt import create_react_agent
from helpers.prompts import prompt_langgraph
from langchain.schema.runnable import Runnable, RunnableConfig
from langchain_core.messages import HumanMessage

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
    