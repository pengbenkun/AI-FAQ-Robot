#!/usr/bin/env python
import sys
sys.path.insert(0, '.')

import uvicorn

def main():
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )

if __name__ == "__main__":
    main()
