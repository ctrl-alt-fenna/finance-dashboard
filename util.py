import json
from pathlib import Path
import pandas as pd
import datetime

global CONFIG_FILENAME
global CATEGORIES_FILENAME
CONFIG_FILENAME = "config.json"
CATEGORIES_FILENAME = "categories.json"

def parse_date_value(value, date_format):
    """Parse date-like values using the configured format, with a few common fallbacks."""
    if value is None:
        return None
    if isinstance(value, datetime.datetime):
        return value

    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()

    # If the date is in int or float format, convert to string for easier conversion
    if isinstance(value, (int, float)):
        try:
            text = str(value).strip()
            if not text:
                return None
            return(parse_date_value(text, date_format))
        except Exception:
            return None

    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None

        normalized_format = date_format.replace("%M", "%m") if date_format else None
        formats_to_try = []
        if normalized_format:
            formats_to_try.append(normalized_format)
        formats_to_try.extend(["%Y%m%d", "%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"])

        for fmt in formats_to_try:
            try:
                return datetime.datetime.strptime(text, fmt)
            except ValueError:
                continue

        try:
            return pd.to_datetime(text, errors="coerce").to_pydatetime()
        except Exception:
            return None

    try:
        return pd.to_datetime(value, errors="coerce").to_pydatetime()
    except Exception:
        return None


def load_config():
    """Load the configuration. Returns the needed values so they can be used in the data-cleaning functions.
       
    Returns:
        Dictionary with all the parsed data from the config file so they can be used by the script.
    """
    filename = CONFIG_FILENAME
    if not filename.endswith(".json"):
        raise TypeError("File must be JSON format")

    # Convert the config file name to a Path object and check that it exists.
    config_path = Path(filename)
    if not config_path.is_file():
        raise FileNotFoundError(f"Config file '{filename}' was not found.")

    # Read the JSON settings from the configuration file.
    with open(config_path, "r") as config_file:
        data = json.load(config_file)

        # Make sure the finance file is present and uses an Excel extension.
        finance_file = data["finance_file"]
        if not finance_file.endswith(".xls") and not finance_file.endswith(".xlsx"):
            raise TypeError("Finance file must be in .xls or .xlsx format")
        if not Path(finance_file).is_file():
            raise FileNotFoundError("Finance file cannot be found")

        # Read optional settings from the config file.
        expense_categories = data.get("expense_categories", [])
        income_categories = data.get("income_categories", [])
        excluded_descriptions = data.get("excluded_descriptions", [])
        filter_descriptions = data.get("filter_descriptions", [])
        date_format = data.get("date_format", '%Y%m%d')
        currency = data.get("currency", "usd")

        start_date_raw = data.get("start_date", "")
        end_date_raw = data.get("end_date", "")

        # Parse the start and end dates from the config file.
        start_date = parse_date_value(start_date_raw, date_format)
        end_date = parse_date_value(end_date_raw, date_format)

        # If no dates are provided, use the full possible date range.
        if start_date is None:
            start_date = datetime.datetime.min
        if end_date is None:
            end_date = datetime.datetime.max

    # Return all relevant settings so other functions can use them.
    return {
        "finance_file": finance_file,
        "expense_categories": expense_categories,
        "income_categories": income_categories,
        "excluded_descriptions": excluded_descriptions,
        "filter_descriptions": filter_descriptions,
        "start_date" : start_date,
        "end_date": end_date,
        "date_format": date_format,
        "currency": currency
    }
    
def filter_data():
    """Filter the Excel file by removing any transactions with an excluded description or a date outside of the date range"""
    # Load the configuration settings first.
    config = load_config()
    start_date = config["start_date"]
    end_date = config["end_date"]
    date_format = config["date_format"]

    # Combine all excluded descriptions into one regular expression pattern.
    excluded_descriptions = '|'.join(config["excluded_descriptions"])

    # Read the relevant columns from the Excel file.
    transactions = pd.read_excel(config["finance_file"])[["Amount", "Date", "Description"]]

    # Convert the amount column to numeric values and replace missing values with 0.
    transactions["Amount"] = pd.to_numeric(transactions["Amount"], errors="coerce").fillna(0.0).astype(float)

    # Parse the date column using the configured format.
    parsed_dates = pd.Series(
        [parse_date_value(value, date_format) for value in transactions["Date"]],
        index=transactions.index,
    )
    # Exclude rows if description matches any excluded pattern.
    description_mask = pd.Series(True, index=transactions.index)
    if excluded_descriptions:
        description_mask = transactions["Description"].str.contains(excluded_descriptions, case=False, na=False) == False

    # Keep only rows within the selected date range and not excluded by description.
    mask = description_mask & parsed_dates.between(start_date, end_date, inclusive="both")
    filtered = transactions[mask].copy()

    return filtered
