"""
Module for testing main functionality
"""

import json
from pathlib import Path
from sys import path as sys_path

import pytest
from httpx import AsyncClient

TEST_FOLDER = Path(__file__).resolve().parent
PROJECT_FOLDER = Path(__file__).resolve().parent.parent
sys_path.append(PROJECT_FOLDER.absolute().as_posix())

from app.main import app


@pytest.mark.anyio
async def test_root():
    async with AsyncClient(app=app, base_url="http://localhost:8000") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "root page"}


@pytest.mark.anyio
async def test_image():
    async with AsyncClient(app=app, base_url="http://localhost:8000") as ac:
        response = await ac.get("/image/",
                                params=dict(depth_min=9050.1,
                                            depth_max=9050.7,
                                            colormap=2)
                                )
    assert response.status_code == 200
    with open(TEST_FOLDER.joinpath("dump.json").as_posix(), mode="r") as fd:
        data = json.load(fd)
    assert response.json() == data
