"""
Module for resizing and uploading images to PostgresSQL database.
"""
import argparse

import numpy as np

from utils import *


def read_csv(fpath: str | Path) -> pd.DataFrame:
    """
    Read csv file
    :param fpath: path to csv file
    :return: DataFrame without NA rows
    """
    # load data from the csv file
    dataset = pd.read_csv(Path(fpath).as_posix(), index_col=None, )
    # drop empty rows
    dataset.dropna(axis=0, inplace=True)
    return dataset


def convert_df_to_ndarray(dataset: pd.DataFrame) -> Tuple[np.ndarray, int, int]:
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


def resize(dataset: np.ndarray, height: int, width: int, interpolation=cv2.INTER_AREA) -> np.ndarray:
    """
    Resize the image to specified size 'height', 'width' and 'interpolation'
    :param dataset: Dataset to be resized
    :param height: Height of resized image
    :param width: Width of resized image
    :param interpolation: Interpolation type
    :return: Resized image numpy array
    """
    # resize with interpolation
    dataset = cv2.resize(dataset, dsize=(width, height), interpolation=interpolation)
    return dataset


def ndarray_apply_colormap(arr: ndarray, colormap=cv2.COLORMAP_JET) -> np.ndarray:
    """
    Apply color map to an array and return new array
    :param arr: ndarray to apply color
    :param colormap: colormap
    :return: ndarray with colormap applied
    """
    # Apply color map
    return cv2.applyColorMap(arr, colormap=colormap)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-w", "--width", type=int, default=None, help="Set new width to resize.")
    parser.add_argument("-f", "--fpath", type=str, default=None, help="The target csv file.")
    args = parser.parse_args()
    fpath = get_full_name(args.fpath)
    if not fpath.is_file():
        raise FileNotFoundError("File does not exist")
    df = read_csv(fpath)
    arr, default_height, default_width = convert_df_to_ndarray(df)
    if args.width is not None and args.width > 0:
        logger.info(f"Resizing image to 'height:{default_height}', 'width: {args.width}'")
        arr = resize(arr, default_height, args.width)
    else:
        logger.info(f"Resized image skip. args.width is '{args.width}'")
    df = make_vertical_dataset(arr, df[COLUMN_DEPTH_NAME])
    upload_to_db(df)
