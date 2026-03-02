import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import Chroma
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class TableRetrieval:
    def __init__(self):
        settings = get_settings()
        if not settings.dashscope_api_key:
            raise ValueError("DASHSCOPE_API_KEY is not configured")
        os.environ["DASHSCOPE_API_KEY"] = settings.dashscope_api_key
        self.embeddings = DashScopeEmbeddings(
            model="text-embedding-v3"
        )
        self.vectorstore = None
        self.top_k = settings.retrieval_top_k
    
    def _get_vectorstore(self):
        if self.vectorstore is None:
            settings = get_settings()
            self.vectorstore = Chroma(
                persist_directory=settings.chroma_persist_directory,
                embedding_function=self.embeddings
            )
        return self.vectorstore
    
    async def retrieve(self, question: str) -> list[str]:
        vectorstore = self._get_vectorstore()
        docs = vectorstore.similarity_search(question, k=self.top_k)
        table_descriptions = [doc.page_content for doc in docs]
        
        logger.info(f"检索到的表描述数量: {len(table_descriptions)}")
        for i, desc in enumerate(table_descriptions, 1):
            logger.info(f"表描述 {i}: {desc}")
        
        return table_descriptions
    
    def is_index_ready(self) -> bool:
        try:
            vectorstore = self._get_vectorstore()
            return vectorstore._collection.count() > 0
        except Exception:
            return False
