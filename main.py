import json
from pathlib import Path
import pandas as pd
import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Load and validate the configuration file used by the script.
def load_config(filename):
    """
    Load the configuration. Returns the needed values so they can be used in the data-cleaning functions.
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
        date_format = data.get("date_format", '%Y%m%d')
        currency = data.get("currency", "usd")

        start_date_raw = data.get("start_date", "")
        end_date_raw = data.get("end_date", "")

        # Helper function to parse dates using the configured format.
        def parse_date(value):
            if not value:
                return None
            try:
                return datetime.datetime.strptime(value, date_format)
            except ValueError as exc:
                raise ValueError("Date format doesn't match the input dates") from exc

        # Parse the start and end dates from the config file.
        start_date = parse_date(start_date_raw)
        end_date = parse_date(end_date_raw)

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
        "start_date" : start_date,
        "end_date": end_date,
        "date_format": date_format,
        "currency": currency
    }
    
# Read the Excel finance data, clean it, and split it into income and expenses.
def filter_data(config_filename):
    # Load the configuration settings first.
    config = load_config(config_filename)
    start_date = config["start_date"]
    end_date = config["end_date"]
    date_format = config["date_format"]

    # Combine all excluded descriptions into one regular expression pattern.
    excluded_descriptions = '|'.join(config["excluded_descriptions"])

    # Read the relevant columns from the Excel file.
    # TODO: Add automatic conversion based in input fields. Descriptions would always inclued letters, amount would include decimals, date would probably be 8 characters in length. 
    transactions = pd.read_excel(config["finance_file"])[["Amount", "Date", "Description"]]

    # Convert the amount column to numeric values and replace missing values with 0.
    transactions["Amount"] = pd.to_numeric(transactions["Amount"], errors="coerce").fillna(0.0).astype(float)

    # Parse the date column using the configured format.
    parsed_dates = pd.to_datetime(transactions["Date"], format=date_format, errors="coerce")

    # Exclude rows if description matches any excluded pattern.
    description_mask = pd.Series(True, index=transactions.index)
    if excluded_descriptions:
        description_mask = transactions["Description"].str.contains(excluded_descriptions, case=False, na=False) == False

    # Keep only rows within the selected date range and not excluded by description.
    mask = description_mask & parsed_dates.between(start_date, end_date, inclusive="both")
    filtered = transactions[mask].copy()

    # Split the filtered data into positive income values and negative expense values.
    income_data = filtered.loc[filtered["Amount"] >= 0, ["Date", "Amount"]].reset_index(drop=True)
    expense_data = filtered.loc[filtered["Amount"] < 0, ["Date", "Amount"]].reset_index(drop=True)
    return {
        "total_income": income_data,
        "total_expenses": expense_data
    }

# Create the chart showing cumulative income, cumulative expenses, and the net difference.
def plot_data():
    # Load the cleaned and separated income/expense data.
    config = load_config("debug_config.json")
    data = filter_data("debug_config.json")
    fig, ax = plt.subplots()

    # Work on copies so the source data stays unchanged.
    income = data["total_income"].copy()
    expenses = data["total_expenses"].copy()

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


plot_data()