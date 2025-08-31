#!/usr/bin/env python3
"""
Gridiron Guru AI - Fantasy Football Draft Assistant
Main entry point for the application
"""

import uvicorn
from app.api.main import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
