from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.messages import BaseMessage
from typing import Dict, List


class MemoryManager:
    def __init__(self):
        self.sessions: Dict[str, BaseChatMessageHistory] = {}
    
    def get_session_history(self, session_id: str) -> BaseChatMessageHistory:
        if session_id not in self.sessions:
            self.sessions[session_id] = ChatMessageHistory()
        return self.sessions[session_id]
    
    def add_message(self, session_id: str, message: BaseMessage):
        history = self.get_session_history(session_id)
        history.add_message(message)
    
    def get_messages(self, session_id: str) -> List[BaseMessage]:
        return self.get_session_history(session_id).messages
    
    def clear_session(self, session_id: str):
        if session_id in self.sessions:
            self.sessions[session_id].clear()


memory_manager = MemoryManager()
