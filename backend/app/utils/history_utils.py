from typing import List
from langchain_core.messages import HumanMessage, AIMessage
from app.models.conversation import Conversation

def format_chat_history(history: List[Conversation]):
    """
    Converts database conversation records into LangChain message format.
    """
    formatted = []
    # Take only the last 5-10 messages to keep context window clean
    for item in history[-10:]:
        formatted.append(HumanMessage(content=item.question))
        formatted.append(AIMessage(content=item.answer))
    return formatted
