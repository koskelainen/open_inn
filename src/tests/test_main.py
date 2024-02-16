"""
Module for testing main functionality
"""

from pathlib import Path
from sys import path as sys_path

import pytest
from httpx import AsyncClient

PROJECT_FOLDER = Path(__file__).resolve().parent.parent
sys_path.append(PROJECT_FOLDER.absolute().as_posix())

from app.main import app


@pytest.mark.anyio
async def test_root():
    async with AsyncClient(app=app, base_url="http://localhost:8000") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "root page"}
