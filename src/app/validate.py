"""
Module for validate functions or variables.
"""
from pathlib import Path
from sys import path as sys_path

from fastapi.exceptions import HTTPException

PROJECT_FOLDER = Path(__file__).resolve().parent.parent
sys_path.append(PROJECT_FOLDER.absolute().as_posix())

from app.utils import logger, read_sql_query


def check_min_max(sql_query: str, depth_min: float, depth_max: float) -> None:
    df = read_sql_query(sql_query)
    if df.empty:
        raise HTTPException(
            status_code=404, detail=f"Table is empty in database. Please check the database and try again."
        )
    min_max = df.loc[0, ["min", "max"]].to_dict()
    logger.debug(min_max)
    tbl_depth_min, tbl_depth_max = min_max["min"], min_max["max"]
    if (depth_min < tbl_depth_min or depth_min > tbl_depth_max
            or depth_max < tbl_depth_min or depth_max > tbl_depth_max):
        raise HTTPException(
            status_code=404, detail=f"No valid variables: {depth_min=} or {depth_max=}. "
                                    f"Valid variable depth values: {tbl_depth_min=} and {tbl_depth_max=}. "
                                    f"Please try again."
        )


def validate_parameters(depth_min: float, depth_max: float, colormap: int = None):
    if None in (depth_min, depth_max):
        raise HTTPException(
            status_code=404, detail=f"Required variables are not valid: {depth_min=}, {depth_max=}. Please try again."
        )

    if not isinstance(depth_min, float):
        raise HTTPException(
            status_code=404, detail="Variable 'depth_min' must be float. Please try again."
        )

    if not isinstance(depth_max, float):
        raise HTTPException(
            status_code=404, detail="Variable 'depth_max' must be float. Please try again."
        )

    if depth_min > depth_max:
        raise HTTPException(
            status_code=404, detail="Got depth_min > then depth_max. Please try again."
        )

    if colormap is not None:
        if not isinstance(colormap, int):
            raise HTTPException(
                status_code=404, detail=f"Variable 'colormap' must be int. Please try again."
            )
        if colormap not in range(22):
            raise HTTPException(
                status_code=404, detail=f"Variable 'colormap' must be in the range from 0 to 21. Please try again."
            )
