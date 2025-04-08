import uuid
from typing import Sequence, List, AsyncIterable

from dotenv import load_dotenv
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from loguru import logger
from langsmith import Client


class PreprocessQuery(StrOutputParser):
    """Preprocess by improving the query before passing it to the LLM."""

    def parse(self, text: str) -> str:
        # Replace properly the question mark
        text = text.replace("?", "")

        # Capitalize the sentence
        text = text.capitalize()

        # Remove any trailing spaces
        text = text.strip()

        # Replace the removed question mark
        text = text + " ?"

        return text


def format_chat_history(chat_history: List[BaseMessage]) -> str:
    formatted_history = ""

    for message in chat_history:
        if isinstance(message, HumanMessage):
            role = "user"
        elif isinstance(message, AIMessage):
            role = "assistant"
        else:
            role = "unknown"
        formatted_history += f"{role.capitalize()}: {message.text}\n"
    return formatted_history


# Load dotenv file
load_dotenv()

# Db for storing the history and retriever
stores_history = {}
stores_retriever = {}

# Global components for each user
client = Client()
prompt = client.pull_prompt("hunkim/rag-qa-with-history")
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
llm = ChatOpenAI(
    streaming=True,
    temperature=0,
    model="gpt-4o-mini",
)
preprocess_query = PreprocessQuery()
str_output_parser = StrOutputParser()


def _get_or_create_session_history(client: str) -> BaseChatMessageHistory:
    global stores_history
    return stores_history.get(client, ChatMessageHistory())


def _get_session_retriever(client: str) -> VectorStoreRetriever:
    global stores_retriever
    retriever = stores_retriever.get(client)

    if retriever is None:
        raise ValueError(f"Client {client} not found in stores.")

    return retriever


def _format_docs(docs: list[Document]) -> str:
    """Format the documents into a string."""
    return "\n---\n".join([doc.page_content for doc in docs])


def _get_retriever(vectorstore: FAISS) -> VectorStoreRetriever:
    return vectorstore.as_retriever(search_type="similarity", k=4)


async def load_document(pdf_path: str) -> Sequence[Document]:
    loader = PyPDFLoader(pdf_path)
    docs = loader.aload()
    return await docs


async def _split_document(docs: Sequence[Document]) -> Sequence[Document]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    return await splitter.atransform_documents(docs)


async def _create_vectorstore(chunks: Sequence[Document]) -> FAISS:
    global embeddings
    return await FAISS.afrom_documents(chunks, embedding=embeddings)  # type: ignore


async def create_session_retriever(client: str, docs: List[Document]) -> str:
    """Create a client for processing the PDF document."""
    global stores_retriever
    logger.info(f"Creating a new client with ID: {client}")

    if client in stores_retriever:
        logger.warning(f"Client '{client}' already exists in stores. Erasing it.")

    chunks = await _split_document(docs)
    vectorstore = await _create_vectorstore(chunks)
    retriever = _get_retriever(vectorstore)
    history = _get_or_create_session_history(client)

    # Create a new retriever and history for the client
    stores_retriever[client] = retriever
    stores_history[client] = history

    return client

async def run(client: str, query: str):
    history = _get_or_create_session_history(client)
    retriever = _get_session_retriever(client)

    # Preprocess the question
    query = await preprocess_query.ainvoke(query)

    # Get the relevant documents
    docs = await retriever.ainvoke(query)

    # Format the documents
    context = _format_docs(docs)

    # Update the history with the new query and answer
    message = HumanMessage(content=query)
    history.add_message(message)
    chat_history = format_chat_history(history.messages)

    # Add the context to the history
    prompt_output = await prompt.ainvoke(
        {
            "chat_history": chat_history,
            "context": context,
            "question": query,
        }
    )

    answer = await llm.ainvoke(prompt_output)
    answer = await str_output_parser.ainvoke(answer)

    message = AIMessage(content=answer)
    history.add_message(message)
    stores_history[client] = history

    return answer


async def run_stream(client: str, query: str) -> AsyncIterable[str]:
    """Streaming version of the run function that yields chunks of the response as they are generated."""
    history = _get_or_create_session_history(client)
    retriever = _get_session_retriever(client)

    # Preprocess the question
    query = await preprocess_query.ainvoke(query)

    # Get the relevant documents
    docs = await retriever.ainvoke(query)

    # Format the documents
    context = _format_docs(docs)

    # Update the history with the new query
    message = HumanMessage(content=query)
    history.add_message(message)
    chat_history = format_chat_history(history.messages)

    # Add the context to the history
    prompt_output = await prompt.ainvoke(
        {
            "chat_history": chat_history,
            "context": context,
            "question": query,
        }
    )

    # Initialize the complete answer for history
    complete_answer = ""

    # Stream the chunks
    async for chunk in llm.astream(prompt_output):
        chunk_text = chunk.content
        complete_answer += chunk_text
        yield chunk_text

    # After streaming is complete, update the history with the full answer
    message = AIMessage(content=complete_answer)
    history.add_message(message)
    stores_history[client] = history
