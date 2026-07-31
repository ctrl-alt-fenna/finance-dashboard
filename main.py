import json
from pathlib import Path
import pandas as pd
import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

global CONFIG_FILENAME
global CATEGORIES_FILENAME
CONFIG_FILENAME = "debug_config.json"
CATEGORIES_FILENAME = "categories.json"


def parse_date_value(value, date_format):
    """Parse date-like values using the configured format, with a few common fallbacks."""
    if value is None:
        return None
    if isinstance(value, datetime.datetime):
        return value

    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()

    # If the date is in int format, convert to string for easier conversion
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


def load_config(filename=CONFIG_FILENAME):
    """Load the configuration. Returns the needed values so they can be used in the data-cleaning functions.
    
    Args:
        A string with the config filename. 
    
    Returns:
        Dictionary with all the parsed data from the config file so they can be used by the script.
    """
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
    config = load_config(CONFIG_FILENAME)
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

def plot_totals():
    """ Plot the data in a graph, showing cumulative income, cumulative expenses, and the net difference."""
    
    # Load the cleaned and separated income/expense data.
    config = load_config(CONFIG_FILENAME)
    data = filter_data()
    fig, ax = plt.subplots()

    # Work on copies so the source data stays unchanged.
    income = data.loc[data["Amount"] >= 0, ["Date", "Amount"]].reset_index(drop=True).copy()
    expenses = data.loc[data["Amount"] < 0, ["Date", "Amount"]].reset_index(drop=True).copy()

    # Convert date strings into real datetime values.
    income["Date"] = pd.to_datetime(income["Date"], format="%Y%m%d")
    expenses["Date"] = pd.to_datetime(expenses["Date"], format="%Y%m%d")
    

    # Group transactions by date and sum them so repeated dates are combined.
    income_daily = (
        income.groupby("Date", as_index=False)["Amount"]
        .sum()
        .rename(columns={"Amount": "income"})
    )

    expenses_daily = (
        expenses.groupby("Date", as_index=False)["Amount"]
        .sum()
        .rename(columns={"Amount": "expenses"})
    )

    # Merge income and expenses into one table and make sure missing values become 0.
    daily = income_daily.merge(expenses_daily, on="Date", how="outer").fillna(0)

    # Expenses are stored as negative values, so convert them to positive values for plotting.
    daily["expenses"] = daily["expenses"].abs()
    daily = daily.sort_values("Date").reset_index(drop=True)

    # Calculate cumulative totals and the net difference between them.
    daily["income_cumulative"] = daily["income"].cumsum()
    daily["expenses_cumulative"] = daily["expenses"].cumsum()
    daily["difference"] = daily["income_cumulative"] - daily["expenses_cumulative"]

    # Format the x-axis as dates for easier reading.
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonthday=1))
    fig.autofmt_xdate()

    # Plot the cumulative income and expenses lines.
    ax.plot(daily["Date"], daily["income_cumulative"], label="Income (sum)", color="green")
    ax.plot(daily["Date"], daily["expenses_cumulative"], label="Expenses (sum)", color="red")

    # Choose a color for each difference point based on whether it is positive, negative, or zero.
    point_colors = [
        "green" if value > 0 else "red" if value < 0 else "black"
        for value in daily["difference"]
    ]

    # Draw the difference line and mark each point with the matching color.
    ax.plot(daily["Date"], daily["difference"], label="Difference", color="black", linewidth=2)
    for date, value, color in zip(daily["Date"], daily["difference"], point_colors):
        ax.scatter(date, value, color=color, s=20)

    currency_symbols = {
        "usd": "$",
        "eur": "€",
        "gbp": "£",
        "jpy": "¥"
    }
    currency_symbol = currency_symbols.get(config["currency"].lower(), config["currency"])

    # Add labels and show the finished chart.
    ax.set_title("Income vs Expenses")
    ax.set_xlabel("Date")
    ax.set_ylabel(f"Cumulative amount ({currency_symbol})")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda value, _: f"{currency_symbol}{value:,.0f}"))
    ax.legend()

    ax.grid(True, which='major', axis='x', color='grey', linewidth=0.5, alpha=0.5)
    ax.grid(True, which='major', axis='y', color='grey', linewidth=0.5, alpha=0.5)

    # Grab the final totals to show next to the graph.
    last_date = daily["Date"].iloc[-1]
    final_income = daily["income_cumulative"].iloc[-1]
    final_expenses = daily["expenses_cumulative"].iloc[-1]
    final_difference = daily["difference"].iloc[-1]

    # Add box to annotate the final totals.
    ax.annotate(
        f"Income: {currency_symbol}{final_income:,.0f}\n"
        f"Expenses: {currency_symbol}{final_expenses:,.0f}\n"
        f"Difference: {currency_symbol}{final_difference:,.0f}",
        xy=(last_date, final_difference),
        xytext=(10, 10),
        textcoords="offset points",
        fontsize=9,
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="lightgray")
    )
    
    fig.canvas.manager.set_window_title("Finance Dashboard")
    fig.canvas.manager.resize(1280, 720)
    plt.show()

def graph_expenses():
    
    # Load the cleaned and separated income/expense data.
    config = load_config(CONFIG_FILENAME)
    from categorize_data import categorize_expenses
    data = categorize_expenses()
    fig, ax = plt.subplots()

    # Work on copies so the source data stays unchanged.
    housing = data["housing"]
    utilities = data["utilities"]
    insurance = data["insurance"]
    other = data["other"]

    # Convert date strings into real datetime values.
    housing["Date"] = pd.to_datetime(housing["Date"], format="%Y%m%d")
    housing["Date"] = housing["Date"].dt.to_period("M")
    utilities["Date"] = pd.to_datetime(utilities["Date"], format="%Y%m%d")
    utilities["Date"] = utilities["Date"].dt.to_period("M")
    insurance["Date"] = pd.to_datetime(insurance["Date"], format="%Y%m%d")
    insurance["Date"] = insurance["Date"].dt.to_period("M")
    other["Date"] = pd.to_datetime(other["Date"], format="%Y%m%d")
    other["Date"] = other["Date"].dt.to_period("M")
    

    # Group transactions by date and sum them so repeated dates are combined.
    housing_monthly = (
        housing.groupby("Date", as_index=False)["Amount"]
        .sum()
        .rename(columns={"Amount": "housing"})
    )

    utilities_monthly = (
        utilities.groupby("Date", as_index=False)["Amount"]
        .sum()
        .rename(columns={"Amount": "utilities"})
    )
    
    insurance_monthly = (
        insurance.groupby("Date", as_index=False)["Amount"]
        .sum()
        .rename(columns={"Amount": "insurance"})
    )
    other_monthly = (
        other.groupby("Date", as_index=False)["Amount"]
        .sum()
        .rename(columns={"Amount": "other"})
    )

    # Merge all expenses into one table and make sure missing values become 0.
    monthly = housing_monthly.merge(utilities_monthly, on="Date", how="outer").merge(insurance_monthly, on="Date", how="outer").merge(other_monthly, on="Date", how="outer").fillna(0)

    # Expenses are stored as negative values, so convert them to positive values for plotting.
    monthly["housing"] = monthly["housing"].abs()
    monthly["utilities"] = monthly["utilities"].abs()
    monthly["insurance"] = monthly["insurance"].abs()
    monthly["other"] = monthly["other"].abs()
    monthly = monthly.sort_values("Date").reset_index(drop=True)

    x = np.arange(len(monthly))
    width = 0.25

    ax.bar(x - width, monthly["housing"], width=width, label="Housing", color="green")
    ax.bar(x, monthly["utilities"], width=width, label="Utilities", color="red")
    ax.bar(x + width, monthly["insurance"], width=width, label="Insurance", color="blue")
    ax.bar(x + width + width, monthly["other"], width=width, label="other", color="black")

    ax.set_xticks(x)
    ax.set_xticklabels(
        [month.strftime("%b") if hasattr(month, "strftime") else str(month) for month in monthly["Date"]],
        rotation=45,
        ha="right"
    )
    ax.set_title("Monthly expenses")
    ax.legend()

    fig.autofmt_xdate()

    currency_symbols = {
        "usd": "$",
        "eur": "€",
        "gbp": "£",
        "jpy": "¥"
    }
    currency_symbol = currency_symbols.get(config["currency"].lower(), config["currency"])

    # Add labels and show the finished chart.
    ax.set_title("Expenses")
    ax.set_xlabel("Date")
    ax.set_ylabel(f"Amount ({currency_symbol})")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda value, _: f"{currency_symbol}{value:,.0f}"))
    ax.legend()

    ax.grid(True, which='major', axis='x', color='grey', linewidth=0.5, alpha=0.5)
    ax.grid(True, which='major', axis='y', color='grey', linewidth=0.5, alpha=0.5)
   
       # Grab the totals to show next to the graph.
    last_x = x[-1]
    totals_housing = monthly["housing"].cumsum().iloc[-1]
    totals_utilities = monthly["utilities"].cumsum().iloc[-1]
    totals_insurance = monthly["insurance"].cumsum().iloc[-1]
    totals_other = monthly["other"].cumsum().iloc[-1]

    # Add box to annotate the final totals.
    ax.annotate(
        f"Total housing: {currency_symbol}{totals_housing:,.0f}\n"
        f"Total utilities: {currency_symbol}{totals_utilities:,.0f}\n"
        f"Total insurance: {currency_symbol}{totals_insurance:,.0f}\n"
        f"Total other: {currency_symbol}{totals_other:,.0f}",
        xy = (last_x, 0),
        xytext=(10, 10),
        textcoords="offset points",
        fontsize=9,
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="lightgray")
    )
   
    fig.canvas.manager.set_window_title("Finance Dashboard")
    fig.canvas.manager.resize(1280, 720)
    plt.show()

if __name__ == "__main__":
    graph_expenses()
    # plot_totals()