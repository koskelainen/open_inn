"""
Module for launch FastAPI application.
"""
from pathlib import Path
from sys import path as sys_path
from typing import Annotated, Dict, Optional, Any

from fastapi import FastAPI
from fastapi.exceptions import HTTPException

PROJECT_FOLDER = Path(__file__).resolve().parent.parent
sys_path.append(PROJECT_FOLDER.absolute().as_posix())

from app.validate import check_min_max, validate_parameters
from app.utils import logger, apply_colormap, read_sql_query, make_horizontal_dataset, COLUMN_PX_ID_NAME, \
    COLUMN_PX_VAL_NAME, IMAGE_TABLE_NAME, COLUMN_DEPTH_NAME

app = FastAPI(
    title="FastAPI-PostgreSQL",
)


@app.get("/")
async def root():
    return {"message": "root page"}


@app.get("/image/")
async def read_item(
        depth_min: float = None,
        depth_max: float = None,
        colormap: Optional[int] = None,
) -> Annotated[Dict[str, Any], None]:
    logger.info(f"Reading {depth_min=} and {depth_max=} for {colormap=}")
    validate_parameters(depth_min=depth_min, depth_max=depth_max, colormap=colormap)

    sql_query = f"SELECT {COLUMN_DEPTH_NAME}, {COLUMN_PX_ID_NAME}, {COLUMN_PX_VAL_NAME} FROM {IMAGE_TABLE_NAME} " \
                f"WHERE {COLUMN_DEPTH_NAME} >= {depth_min} and {COLUMN_DEPTH_NAME} <= {depth_max}"
    sql_min_max_query = f"select min({COLUMN_DEPTH_NAME}), max({COLUMN_DEPTH_NAME}) from {IMAGE_TABLE_NAME};"

    df = read_sql_query(sql_query)
    check_min_max(sql_min_max_query, depth_min=depth_min, depth_max=depth_max)

    if df.empty:
        raise HTTPException(
            status_code=404, detail=f"With current {depth_min=} and {depth_max=} "
                                    f"database returned an empty dataset. Please try again."
        )

    df = make_horizontal_dataset(df)
    if colormap is not None:
        df = apply_colormap(df, colormap)
    return {"columns": df.columns.tolist(), "data": df.to_json(orient="values")}
