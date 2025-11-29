from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from typing import List, Optional
from pathlib import Path
from core.models import ModelManager
from config import settings


class RAGManager:
    def __init__(self, persist_directory: Optional[str] = None):
        self.persist_directory = persist_directory or settings.vector_store_path
        self.embeddings = ModelManager.get_embeddings()
        self.vectorstore = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
    
    def initialize_vectorstore(self):
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
        self.vectorstore = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings
        )
        return self.vectorstore
    
    def add_documents(self, documents: List[Document]):
        if not self.vectorstore:
            self.initialize_vectorstore()
        
        splits = self.text_splitter.split_documents(documents)
        self.vectorstore.add_documents(splits)
        return len(splits)
    
    def add_texts(self, texts: List[str], metadatas: Optional[List[dict]] = None):
        if not self.vectorstore:
            self.initialize_vectorstore()
        
        documents = [Document(page_content=text, metadata=meta or {}) 
                    for text, meta in zip(texts, metadatas or [{}] * len(texts))]
        return self.add_documents(documents)
    
    def similarity_search(self, query: str, k: int = 4):
        if not self.vectorstore:
            self.initialize_vectorstore()
        return self.vectorstore.similarity_search(query, k=k)
    
    def as_retriever(self, **kwargs):
        if not self.vectorstore:
            self.initialize_vectorstore()
        return self.vectorstore.as_retriever(**kwargs)


rag_manager = RAGManager()
