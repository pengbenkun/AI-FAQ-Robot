import sys
print("Python version:", sys.version)

try:
    import uvicorn
    print("uvicorn: OK")
except ImportError as e:
    print("uvicorn: FAIL -", e)

try:
    import fastapi
    print("fastapi: OK")
except ImportError as e:
    print("fastapi: FAIL -", e)

try:
    import langchain_qwq
    print("langchain_qwq: OK")
except ImportError as e:
    print("langchain_qwq: FAIL -", e)

try:
    import sqlalchemy
    print("sqlalchemy: OK")
except ImportError as e:
    print("sqlalchemy: FAIL -", e)

try:
    import chromadb
    print("chromadb: OK")
except ImportError as e:
    print("chromadb: FAIL -", e)

try:
    import pydantic_settings
    print("pydantic_settings: OK")
except ImportError as e:
    print("pydantic_settings: FAIL -", e)
