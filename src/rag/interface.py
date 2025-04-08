import os
from typing import Dict, Optional, List
from uuid import uuid4

import chainlit as cl
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer
from chainlit.element import Element
from chainlit.types import ThreadDict
from fastapi import Request, Response
from langchain_community.document_loaders import PyPDFLoader
from loguru import logger
from multipart import file_path
from pypdf import PdfReader

from rag.pipeline import create_session_retriever, run_stream

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
    """files = None

    # Wait for the user to upload a file
    while files is None:
        files = await cl.AskFileMessage(
            content="Please upload a text file to begin!",
            # accept PDF files
            accept=["text/plain", "application/pdf"],
            timeout=3600,
        ).send()

    text_file = files[0]
    
    text = ""
    pdf = PdfReader(text_file.path)
    
    for page in pdf.pages:
        text += page.extract_text()

    identifier = cl.context.session.user.identifier
    await create_session_retriever(client=identifier, filepath=text_file.path)

    # Let the user know that the system is ready
    await cl.Message(
        content=f"`{text_file.name}` uploaded, it contains {len(text)} characters!"
    ).send()"""


async def create_retriever_from_pdfs(user: str, elements: List[Element]):
    """Upload a PDF file to the server."""
    docs = []
    pdf_files = [elem for elem in elements if elem.mime == "application/pdf"]
    pdf_readers = (PyPDFLoader(file.path) for file in pdf_files)

    message = "You have uploaded the following files:"
    assistant_msg = cl.Message(content=message)
    await assistant_msg.send()

    for file, pdf_reader in zip(pdf_files, pdf_readers):
        file_docs = await pdf_reader.aload()
        length = sum(len(doc.page_content) for doc in file_docs)
        message = f"\n- {file.name} ({file.size} bytes, {length} characters)"
        await assistant_msg.stream_token(message)

        docs.extend(file_docs)

    message = (
        f"\n\nThe documents have been successfully uploaded "
        f"and indexed. You can now ask questions about "
        f"the content of the files."
    )
    await create_session_retriever(user, docs)
    await assistant_msg.stream_token(message)


@cl.on_message
async def on_message(msg: cl.Message):
    logger.info(f"Received message: {msg.content}")
    identifier = cl.context.session.user.identifier
    
    if msg.elements:
        await create_retriever_from_pdfs(identifier, msg.elements)
    
    assistant_msg = cl.Message(content="")

    async for part in run_stream(client=identifier, query=msg.content):
        if token := part or "":
            await assistant_msg.stream_token(token)

    await assistant_msg.update()


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
    ...
    """return [
        cl.ChatProfile(
            name="GPT-3.5",
            markdown_description="The underlying LLM model is **GPT-3.5**.",
        ),
        cl.ChatProfile(
            name="GPT-4",
            markdown_description="The underlying LLM model is **GPT-4**.",
        ),
    ]"""


@cl.set_starters
async def set_starters():
    return [
        cl.Starter(
            label="Morning routine ideation",
            message="Can you help me create a personalized morning routine that would help increase my productivity throughout the day? Start by asking me about my current habits and what activities energize me in the morning.",
            icon="/public/idea.svg",
        ),
        cl.Starter(
            label="Explain superconductors",
            message="Explain superconductors like I'm five years old.",
            icon="/public/cart.svg",
        ),
        cl.Starter(
            label="Python script for daily email reports",
            message="Write a script to automate sending daily email reports in Python, and walk me through how I would set it up.",
            icon="/public/drug.svg",
        ),
        cl.Starter(
            label="Text inviting friend to wedding",
            message="Write a text asking a friend to be my plus-one at a wedding next month. I want to keep it super short and casual, and offer an out.",
            icon="/public/paper_airplane.svg",
        ),
    ]


@cl.on_settings_update
async def setup_agent(settings):
    print("on_settings_update", settings)
