from typing import List
from database.client import supabase_client
from database.models import ConversationHistory, Document
from core.logger import logger

class ConversationRepository:
    def __init__(self):
        self.client = supabase_client.get_client()
    
    def save_message(self, session_id: str, role: str, content: str, metadata: dict = None):
        try:
            data = {
                "session_id": session_id,
                "role": role,
                "content": content,
                "metadata": metadata or {}
            }
            result = self.client.table("conversation_history").insert(data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to save message: {e}")
            return None
    
    def get_session_history(self, session_id: str, limit: int = 50) -> List[ConversationHistory]:
        try:
            result = self.client.table("conversation_history")\
                .select("*")\
                .eq("session_id", session_id)\
                .order("created_at", desc=False)\
                .limit(limit)\
                .execute()
            return [ConversationHistory(**item) for item in result.data]
        except Exception as e:
            logger.error(f"Failed to get session history: {e}")
            return []
    
    def clear_session(self, session_id: str):
        try:
            self.client.table("conversation_history")\
                .delete()\
                .eq("session_id", session_id)\
                .execute()
        except Exception as e:
            logger.error(f"Failed to clear session: {e}")

conversation_repo = ConversationRepository()
