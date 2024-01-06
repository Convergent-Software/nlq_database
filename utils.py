import pandas as pd

from typing import List, Dict, Any


def format_as_dataframe(rows: List[List[Any]], column_names: List[str]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=column_names)


def format_as_dict(
    rows: List[List[Any]], column_names: List[str]
) -> List[Dict[str, Any]]:
    return [dict(zip(column_names, row)) for row in rows]
