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

LOCAL_BASE_URL = "http://localhost:8000"


@pytest.mark.anyio
async def test_root():
    async with AsyncClient(app=app, base_url=LOCAL_BASE_URL) as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "root page"}


@pytest.mark.anyio
async def test_image_colormap():
    with open(TEST_FOLDER.joinpath("image_with_colormap.json").as_posix(), mode="r") as fd:
        test_params, data = json.load(fd)
    async with AsyncClient(app=app, base_url=LOCAL_BASE_URL) as ac:
        response = await ac.get("/image/",
                                params=test_params,
                                )
    assert response.status_code == 200
    assert response.json() == data


@pytest.mark.anyio
async def test_image():
    with open(TEST_FOLDER.joinpath("simple_image.json").as_posix(), mode="r") as fd:
        test_params, data = json.load(fd)
    async with AsyncClient(app=app, base_url=LOCAL_BASE_URL) as ac:
        response = await ac.get("/image/",
                                params=test_params,
                                )
    assert response.status_code == 200
    assert response.json() == data
