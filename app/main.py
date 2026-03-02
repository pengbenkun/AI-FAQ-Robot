import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from app.api.routes import router
from app.api.permissions import router as permissions_router
from app.core.config import get_settings
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="煤炭设计院数据中台AI问答机器人",
    description="自然语言转SQL查询系统",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")
app.include_router(permissions_router, prefix="/api/v1")


@app.on_event("startup")
async def startup():
    logger.info("AI问答机器人服务启动")
    settings = get_settings()
    logger.info(f"服务配置: host={settings.app_host}, port={settings.app_port}")
    logger.info(f"Chroma路径: {settings.chroma_persist_directory}")


@app.get("/", response_class=HTMLResponse)
async def root():
    template_path = os.path.join(
        os.path.dirname(__file__),
        "templates",
        "index.html"
    )
    
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()


@app.get("/admin", response_class=HTMLResponse)
async def admin():
    template_path = os.path.join(
        os.path.dirname(__file__),
        "templates",
        "admin.html"
    )
    
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(app, host=settings.app_host, port=settings.app_port)
