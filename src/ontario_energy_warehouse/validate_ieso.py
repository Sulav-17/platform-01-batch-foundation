import pandas as pd


REQUIRED_COLUMNS = [
    "Date",
    "Hour",
    "Market Demand",
    "Ontario Demand",
]

def validate_ieso_data(data: pd.DataFrame) -> None:
    """Check whether the IESO demand data follows our basic rules."""

    if list(data.columns) != REQUIRED_COLUMNS:
        raise ValueError("The file has unexpected columns.")

    if data.isna().any().any():
        raise ValueError("The file contains missing values.")

    parsed_dates = pd.to_datetime(data["Date"], errors="coerce")

    if parsed_dates.isna().any():
        raise ValueError("The file contains invalid dates.")

    if not data["Hour"].between(1, 24).all():
        raise ValueError("Hours must be between 1 and 24.")

    demand_columns = ["Market Demand", "Ontario Demand"]

    for column in demand_columns:
        numeric_values = pd.to_numeric(data[column], errors="coerce")

        if numeric_values.isna().any():
            raise ValueError(f"{column} contains non-numeric values.")

        if not numeric_values.gt(0).all():
            raise ValueError(f"{column} must contain positive values.")

    if data.duplicated(subset=["Date", "Hour"]).any():
        raise ValueError("Duplicate Date and Hour records were found.")