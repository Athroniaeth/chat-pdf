import os
from typing import Dict, Optional

import chainlit as cl
from chainlit.types import ThreadDict
from fastapi import Request, Response
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer

from chainlit.input_widget import Select, Switch, Slider
from uuid import uuid4

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+asyncpg://chainlit:chainlitpassword@localhost:5432/chainlitdb"
)


@cl.data_layer
def get_data_layer():
    return SQLAlchemyDataLayer(conninfo=DATABASE_URL)


@cl.header_auth_callback
def header_auth_callback(headers: Dict) -> Optional[cl.User]:
    random_user = uuid4()
    return cl.User(identifier=f"{random_user}", metadata={"role": "user", "provider": "header"})


@cl.on_chat_start
async def on_chat_start():
    settings = await cl.ChatSettings(
        [
            Select(
                id="Model",
                label="OpenAI - Model",
                values=["gpt-3.5-turbo", "gpt-3.5-turbo-16k", "gpt-4", "gpt-4-32k"],
                initial_index=0,
            ),
            Switch(id="Streaming", label="OpenAI - Stream Tokens", initial=True),
            Slider(
                id="Temperature",
                label="OpenAI - Temperature",
                initial=1,
                min=0,
                max=2,
                step=0.1,
            ),
            Slider(
                id="SAI_Steps",
                label="Stability AI - Steps",
                initial=30,
                min=10,
                max=150,
                step=1,
                description="Amount of inference steps performed on image generation.",
            ),
            Slider(
                id="SAI_Cfg_Scale",
                label="Stability AI - Cfg_Scale",
                initial=7,
                min=1,
                max=35,
                step=0.1,
                description="Influences how strongly your generation is guided to match your prompt.",
            ),
            Slider(
                id="SAI_Width",
                label="Stability AI - Image Width",
                initial=512,
                min=256,
                max=2048,
                step=64,
                tooltip="Measured in pixels",
            ),
            Slider(
                id="SAI_Height",
                label="Stability AI - Image Height",
                initial=512,
                min=256,
                max=2048,
                step=64,
                tooltip="Measured in pixels",
            ),
        ]
    ).send()


@cl.on_message
async def on_message(msg: cl.Message):
    print("The user sent: ", msg.content)
    return await cl.Message(content=msg.content).send()


@cl.on_stop
async def on_stop():
    print("The user wants to stop the task!")
    return cl.Message(content="User stopped the task").send()


@cl.on_chat_resume
async def on_chat_resume(thread: ThreadDict):
    print("The user resumed a previous chat session!")


@cl.on_logout
def on_logout(request: Request, response: Response):
    response.delete_cookie("my_cookie")


@cl.set_chat_profiles
async def chat_profile():
    return [
        cl.ChatProfile(
            name="GPT-3.5",
            markdown_description="The underlying LLM model is **GPT-3.5**.",
        ),
        cl.ChatProfile(
            name="GPT-4",
            markdown_description="The underlying LLM model is **GPT-4**.",
        ),
    ]


@cl.set_starters
async def set_starters():
    return [
        cl.Starter(
            label="Morning routine ideation",
            message="Can you help me create a personalized morning routine that would help increase my productivity throughout the day? Start by asking me about my current habits and what activities energize me in the morning.",
            icon="/static/idea.svg",
        ),
        cl.Starter(
            label="Explain superconductors",
            message="Explain superconductors like I'm five years old.",
            icon="/static/cart.svg",
        ),
        cl.Starter(
            label="Python script for daily email reports",
            message="Write a script to automate sending daily email reports in Python, and walk me through how I would set it up.",
            icon="/static/drug.svg",
        ),
        cl.Starter(
            label="Text inviting friend to wedding",
            message="Write a text asking a friend to be my plus-one at a wedding next month. I want to keep it super short and casual, and offer an out.",
            icon="/static/paper_airplane.svg",
        ),
    ]


@cl.on_settings_update
async def setup_agent(settings):
    print("on_settings_update", settings)
