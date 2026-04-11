from pathlib import Path

import pandas as pd


def read_excel_sheet(file_path: Path, sheet_name: str) -> pd.DataFrame:
    return pd.read_excel(file_path, sheet_name=sheet_name)