import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

from util import load_config, filter_data 

def plot_totals():
    """ Plot the data in a graph, showing cumulative income, cumulative expenses, and the net difference."""
    
    # Load the cleaned and separated income/expense data.
    config = load_config()
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
    config = load_config()
    from categorize_data import categorize_expenses
    data = categorize_expenses()
    
    fig, ax = plt.subplots()

    housing = data["housing"]
    utilities = data["utilities"]
    insurance = data["insurance"]
    groceries = data["groceries"]
    streaming = data["streaming"]
    transportation = data["transportation"]
    hobbies = data["hobbies"]
    loans = data["loans"]
    other = data["other"]

    # Convert date strings into real datetime values.
    housing["Date"] = pd.to_datetime(housing["Date"], format="%Y%m%d")
    housing["Date"] = housing["Date"].dt.to_period("M")
    
    utilities["Date"] = pd.to_datetime(utilities["Date"], format="%Y%m%d")
    utilities["Date"] = utilities["Date"].dt.to_period("M")
    
    insurance["Date"] = pd.to_datetime(insurance["Date"], format="%Y%m%d")
    insurance["Date"] = insurance["Date"].dt.to_period("M")
    
    groceries["Date"] = pd.to_datetime(groceries["Date"], format="%Y%m%d")
    groceries["Date"] = groceries["Date"].dt.to_period("M")
    
    streaming["Date"] = pd.to_datetime(streaming["Date"], format="%Y%m%d")
    streaming["Date"] = streaming["Date"].dt.to_period("M")
    
    transportation["Date"] = pd.to_datetime(transportation["Date"], format="%Y%m%d")
    transportation["Date"] = transportation["Date"].dt.to_period("M")
    
    hobbies["Date"] = pd.to_datetime(hobbies["Date"], format="%Y%m%d")
    hobbies["Date"] = hobbies["Date"].dt.to_period("M")
    
    loans["Date"] = pd.to_datetime(loans["Date"], format="%Y%m%d")
    loans["Date"] = loans["Date"].dt.to_period("M")
    
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
    
    groceries_monthly = (
        groceries.groupby("Date", as_index=False)["Amount"]
        .sum()
        .rename(columns={"Amount": "groceries"})
    )
    
    streaming_monthly = (
        streaming.groupby("Date", as_index=False)["Amount"]
        .sum()
        .rename(columns={"Amount": "streaming"})
    )
    
    transportation_monthly = (
        transportation.groupby("Date", as_index=False)["Amount"]
        .sum()
        .rename(columns={"Amount": "transportation"})
    )
    
    hobbies_monthly = (
        hobbies.groupby("Date", as_index=False)["Amount"]
        .sum()
        .rename(columns={"Amount": "hobbies"})
    )
    
    loans_monthly = (
        loans.groupby("Date", as_index=False)["Amount"]
        .sum()
        .rename(columns={"Amount": "loans"})
    )
    
    other_monthly = (
        other.groupby("Date", as_index=False)["Amount"]
        .sum()
        .rename(columns={"Amount": "other"})
    )

    # Merge all expenses into one table and make sure missing values become 0.
    monthly = housing_monthly.merge(utilities_monthly, on="Date", how="outer").merge(insurance_monthly, on="Date", how="outer").merge(groceries_monthly, on="Date", how="outer").merge(streaming_monthly, on="Date", how="outer").merge(transportation_monthly, on="Date", how="outer").merge(hobbies_monthly, on="Date", how="outer").merge(loans_monthly, on="Date", how="outer").merge(other_monthly, on="Date", how="outer").fillna(0)

    # Expenses are stored as negative values, so convert them to positive values for plotting.
    monthly["housing"] = monthly["housing"].abs()
    monthly["utilities"] = monthly["utilities"].abs()
    monthly["insurance"] = monthly["insurance"].abs()
    monthly["groceries"] = monthly["groceries"].abs()
    monthly["streaming"] = monthly["streaming"].abs()
    monthly["transportation"] = monthly["transportation"].abs()
    monthly["hobbies"] = monthly["hobbies"].abs()
    monthly["loans"] = monthly["loans"].abs()
    monthly["other"] = monthly["other"].abs()
    monthly = monthly.sort_values("Date").reset_index(drop=True)

    x = np.arange(len(monthly))
    num_categories = 9
    width = 1/num_categories
    offsets = np.linspace(-width * (num_categories - 1) / 2, width * (num_categories - 1) / 2, num_categories)

    ax.bar(x + offsets[0], monthly["housing"], width=width, label="Housing", color="red")
    ax.bar(x + offsets[1], monthly["utilities"], width=width, label="Utilities", color="orange")
    ax.bar(x + offsets[2], monthly["insurance"], width=width, label="Insurance", color="yellow")
    ax.bar(x + offsets[3], monthly["groceries"], width=width, label="Groceries", color="green")
    ax.bar(x + offsets[4], monthly["streaming"], width=width, label="Streaming", color="blue")
    ax.bar(x + offsets[5], monthly["transportation"], width=width, label="Transportation", color="purple")
    ax.bar(x + offsets[6], monthly["hobbies"], width=width, label="Hobbies", color="violet")
    ax.bar(x + offsets[7], monthly["loans"], width=width, label="Loans", color="grey")
    ax.bar(x + offsets[8], monthly["other"], width=width, label="Other", color="black")

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
    totals_groceries = monthly["groceries"].cumsum().iloc[-1]
    totals_streaming = monthly["streaming"].cumsum().iloc[-1]
    totals_transportation = monthly["transportation"].cumsum().iloc[-1]
    totals_hobbies = monthly["hobbies"].cumsum().iloc[-1]
    totals_loans = monthly["loans"].cumsum().iloc[-1]
    totals_other = monthly["other"].cumsum().iloc[-1]

    # Add box to annotate the final totals.
    ax.annotate(
        f"Total housing: {currency_symbol}{totals_housing:,.0f}\n"
        f"Total utilities: {currency_symbol}{totals_utilities:,.0f}\n"
        f"Total insurance: {currency_symbol}{totals_insurance:,.0f}\n"
        f"Total groceries: {currency_symbol}{totals_groceries:,.0f}\n"
        f"Total streaming: {currency_symbol}{totals_streaming:,.0f}\n"
        f"Total transportation: {currency_symbol}{totals_transportation:,.0f}\n"
        f"Total hobbies: {currency_symbol}{totals_hobbies:,.0f}\n"
        f"Total loans: {currency_symbol}{totals_loans:,.0f}\n"
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