import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, inspect
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import Chroma
from app.core.config import get_settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_table_descriptions(engine) -> list[tuple[str, str]]:
    inspector = inspect(engine)
    descriptions = []
    
    for table_name in inspector.get_table_names():
        try:
            columns = inspector.get_columns(table_name)
            comment = inspector.get_table_comment(table_name)
            
            col_parts = []
            for col in columns:
                col_name = col['name']
                col_type = str(col['type'])
                col_comment = col.get('comment', '')
                if col_comment:
                    col_parts.append(f"{col_name}({col_type}, {col_comment})")
                else:
                    col_parts.append(f"{col_name}({col_type})")
            
            col_str = ", ".join(col_parts)
            table_comment = comment.get('text', '') if comment else ''
            
            if table_comment:
                desc = f"表名：{table_name}，表注释：{table_comment}，列：{col_str}"
            else:
                desc = f"表名：{table_name}，列：{col_str}"
            
            descriptions.append((table_name, desc))
            logger.info(f"Found table: {table_name}")
        except Exception as e:
            logger.warning(f"Error processing table {table_name}: {e}")
    
    return descriptions


def build_index():
    settings = get_settings()
    
    if not settings.dashscope_api_key:
        logger.error("DASHSCOPE_API_KEY is not configured")
        return
    
    os.environ["DASHSCOPE_API_KEY"] = settings.dashscope_api_key
    
    logger.info("Connecting to business database...")
    engine = create_engine(settings.business_db_url)
    
    logger.info("Scanning table structures...")
    descriptions = get_table_descriptions(engine)
    
    if not descriptions:
        logger.warning("No tables found in the database")
        return
    
    logger.info(f"Found {len(descriptions)} tables, generating embeddings...")
    
    embeddings = DashScopeEmbeddings(
        model="text-embedding-v3"
    )
    
    texts = [desc[1] for desc in descriptions]
    ids = [desc[0] for desc in descriptions]
    
    os.makedirs(settings.chroma_persist_directory, exist_ok=True)
    
    logger.info("Creating Chroma vector store...")
    vectorstore = Chroma.from_texts(
        texts=texts,
        ids=ids,
        embedding=embeddings,
        persist_directory=settings.chroma_persist_directory
    )
    vectorstore.persist()
    
    logger.info(f"Vector index built successfully!")
    logger.info(f"Total tables indexed: {len(descriptions)}")
    logger.info(f"Chroma persist directory: {settings.chroma_persist_directory}")


if __name__ == "__main__":
    build_index()
