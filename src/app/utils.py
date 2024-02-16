"""
Module containing utility functions and variables.
"""

import logging
from contextlib import contextmanager
from os import environ
from pathlib import Path
from typing import Literal, Tuple, Union

import cv2
import pandas as pd
from dotenv import load_dotenv
from numpy import ndarray
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.inspection import inspect

PROJECT_FOLDER = Path(__file__).resolve().parent.parent

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s:%(levelname)s:%(name)s:%(message)s')
# Create logger, set level, and add stream handler
logger = logging.getLogger()

# set constants
DOTENV_PATH = PROJECT_FOLDER.parent.joinpath(".env")
# COLUMN_PX_TYPE = "int16"
COLUMN_PX_TYPE = "uint8"
COLUMN_PX_MASK = "col"
COLUMN_DEPTH_TYPE = "float64"
COLUMN_DEPTH_NAME = "depth"
COLUMN_PX_ID_NAME = "px_id"
COLUMN_PX_ID_TYPE = "int"
COLUMN_PX_VAL_NAME = "px_val"
COLUMN_PX_VAL_TYPE = COLUMN_PX_TYPE
RESIZE_WIDTH = 150

IMAGE_TABLE_NAME = "image"

# load variables from .env
load_dotenv(DOTENV_PATH)


def get_full_name(fpath: str) -> Union[Path, str]:
    fpath_absolute = Path(fpath).absolute()
    if fpath_absolute.exists():
        return fpath_absolute
    fpath_from_root_project = PROJECT_FOLDER.joinpath(fpath)
    if fpath_from_root_project.exists():
        return fpath_from_root_project
    raise ValueError(f"file path not found: {fpath}")


def make_dsn_url(
        hostname: str = None,
        port: str = None,
        database_name: str = None,
        username: str = None,
        password: str = None,
) -> str:
    """
    Create a URL to connect to PostgresSQL database.
    :param hostname: hostname
    :param port: port
    :param database_name: database_name
    :param username: username
    :param password: password
    :return: URL to connect to PostgresSQL
    """
    hostname = hostname or environ.get("HOSTNAME", "localhost")
    port = port or environ.get("PORT", "5432")
    database_name = database_name or environ.get("DATABASE_NAME", "postgres")
    username = username or environ.get("USERNAME")
    password = password or environ.get("PASSWORD")
    return f"postgresql+psycopg2://{username}:{password}@{hostname}:{port}/{database_name}"


@contextmanager
def get_engine(
        pool_pre_ping: bool = True,
        max_identifier_length: int = 128,
        pool_size: int = 10,
        max_overflow: int = 30,
        pool_recycle: int = -1,
) -> Engine:
    """
    Context manager for creating engine and connecting to PostgresSQL database.
    :param pool_pre_ping:
    :param max_identifier_length:
    :param pool_size:
    :param max_overflow:
    :param pool_recycle:
    :return: Engine
    """
    url = make_dsn_url()
    engine = None
    try:
        engine = create_engine(url, **{
            "pool_pre_ping": pool_pre_ping,
            "max_identifier_length": max_identifier_length,
            "pool_size": pool_size,
            "max_overflow": max_overflow,
            "pool_recycle": pool_recycle,
        })
        # validate engine
        _: Inspector = inspect(engine)
        yield engine
    except Exception as e:
        raise Exception(f"Error while connecting to PostgreSQL: {e}")
    finally:
        if engine is not None:
            engine.dispose()


def upload_to_db(
        dataset: pd.DataFrame,
        table_name: str = IMAGE_TABLE_NAME,
        if_exists: Literal["fail", "replace", "append"] = "replace",
        chunksize: int = 50_000,
) -> None:
    """
    Upload a dataset to PostgreSQL database
    :param dataset: origin dataset DataFrame
    :param table_name: table name
    :param if_exists: 'replace' rows if already exists
    :param chunksize: chunk size in rows
    :return: DataFrame
    """
    if if_exists not in ("fail", "replace", "append"):
        raise ValueError(f"Incorrect value for if_exists: {if_exists}")

    logger.debug(f"Dataset push to database, shape: {dataset.shape}")
    with get_engine() as engine:
        dataset.to_sql(
            name=table_name,
            con=engine,
            if_exists=if_exists,
            chunksize=chunksize,
            index=True,
            index_label="id",
        )


def read_sql_query(sql_query: str) -> pd.DataFrame:
    """
    Read data from the database through sql query
    :param sql_query: str
    :return: dataset pandas DataFrame
    """
    with get_engine() as engine:
        dataset = pd.read_sql_query(
            sql=sql_query,
            con=engine,
        )
    if not dataset.empty:
        dataset.columns = dataset.columns.str.lower()
        dataset.reset_index(inplace=True)
    logger.debug(f"Got dataset from database, shape: {dataset.shape}")
    logger.debug(f"{dataset.shape}")
    return dataset


def make_vertical_dataset(dataset: ndarray, depth_series: pd.Series) -> pd.DataFrame:
    """
    Make the vertical dataframe of the original dataframe
    :param dataset: original dataframe
    :param depth_series: vertical oriented dataframe
    :return:
    """
    # make new DataFrame from ndarray
    dataset = pd.DataFrame(dataset, columns=[i + 1 for i in range(dataset.shape[1])])
    # add origin column "depth" to dataset
    dataset[COLUMN_DEPTH_NAME] = depth_series
    # Prepare mapper before casting types
    columns_mapper = dict(zip([COLUMN_PX_ID_NAME, COLUMN_PX_VAL_NAME], [COLUMN_PX_ID_TYPE, COLUMN_PX_VAL_TYPE]))
    dataset = (dataset.melt(id_vars=COLUMN_DEPTH_NAME, var_name=COLUMN_PX_ID_NAME, value_name=COLUMN_PX_VAL_NAME)
               .astype(columns_mapper)
               .sort_values([COLUMN_DEPTH_NAME, COLUMN_PX_ID_NAME], ascending=[True, False])
               .reset_index(drop=True)
               )
    return dataset


def make_horizontal_dataset(dataset: pd.DataFrame) -> pd.DataFrame:
    """
    Make the dataframe from vertically to horizontally oriented.
    :param dataset: vertically oriented dataframe
    :return: horizontally oriented dataframe
    """
    pivot_table = dataset.pivot(index=[COLUMN_DEPTH_NAME], columns=[COLUMN_PX_ID_NAME], values=[COLUMN_PX_VAL_NAME])
    # prepare new dataset from pivot_table
    dataset = pivot_table.set_axis(pivot_table.columns.tolist(), axis=1).reset_index()
    # make new columns from pivot_table
    dataset.columns = [f"{COLUMN_PX_MASK}{col[1]}" if isinstance(col, tuple) else col for col in dataset.columns]
    return dataset


def convert_df_to_ndarray(dataset: pd.DataFrame) -> Tuple[ndarray, int, int]:
    """
    Make the numpy array from dataframe and cast types of columns.
    :param dataset: DataFrame
    :return: Tuple of numpy arrays and height img and width img
    """
    columns_px = [col for col in dataset.columns.tolist() if col.startswith(COLUMN_PX_MASK)]
    # build mapper for columns type casting
    columns_mapper = dict(zip(columns_px, [COLUMN_PX_TYPE] * len(columns_px)))
    # set default variable height and width
    height = dataset.shape[0]
    width = len(columns_px)
    # cast type
    dataset = dataset.astype(columns_mapper)
    # convert pd.DataFrame to np.ndarray
    result = dataset[columns_px].to_numpy()
    return result, height, width


def apply_colormap(df: pd.DataFrame, colormap: int) -> pd.DataFrame:
    """
    Apply the colormap to the image frames
    :param df: original dataframe
    :param colormap: color map to apply
    :return: new dataframe with colormap applied
    """
    arr, height, width = convert_df_to_ndarray(df)
    arr = cv2.applyColorMap(arr, colormap=colormap)
    arr_reshaped = arr.reshape(arr.shape[0], -1)  # return BGR array for each px
    # make new columns
    columns_px = [f"{col}_{char}" for col in df.columns.tolist() for char in "BGR" if col.startswith(COLUMN_PX_MASK)]
    # make new DataFrame from ndarray
    dataset = pd.DataFrame(arr_reshaped, columns=columns_px)
    # add origin column "depth" to dataset
    dataset[COLUMN_DEPTH_NAME] = df[COLUMN_DEPTH_NAME]
    columns = [COLUMN_DEPTH_NAME] + columns_px
    return dataset[columns]
