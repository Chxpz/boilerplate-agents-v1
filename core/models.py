from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from config import settings


class ModelManager:
    _llm_instance = None
    _embeddings_instance = None
    
    @classmethod
    def get_llm(cls, **kwargs):
        if cls._llm_instance is None:
            cls._llm_instance = ChatOpenAI(
                model=kwargs.get("model_name", settings.model_name),
                temperature=kwargs.get("temperature", settings.temperature),
                api_key=settings.openai_api_key
            )
        return cls._llm_instance
    
    @classmethod
    def get_embeddings(cls):
        if cls._embeddings_instance is None:
            cls._embeddings_instance = OpenAIEmbeddings(
                model=settings.embeddings_model,
                api_key=settings.openai_api_key
            )
        return cls._embeddings_instance
