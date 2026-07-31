from pathlib import Path
import json, pandas as pd
def categorize_expenses():
    from main import filter_data
    data = filter_data()
    categories = read_categories()
    
    # income = data.loc[data["Amount"] >= 0, ["Date", "Amount"]].reset_index(drop=True)
    expenses = data.loc[data["Amount"] < 0, ["Date", "Amount", "Description"]].reset_index(drop=True)

    housing_categories = '|'.join(categories["housing_categories"])
    insurance_categories = '|'.join(categories["insurance_categories"])
    utilities_categories = '|'.join(categories["utilities_categories"])
    
    # Create masks by filtering rows if description matches any of the categories.
    housing_mask = pd.Series(True, index=expenses.index)
    insurance_mask = pd.Series(True, index=expenses.index)
    util_mask = pd.Series(True, index=expenses.index)
    if housing_categories:
        housing_mask = expenses["Description"].str.contains(housing_categories, case=False, na=False) == True
    if insurance_categories:
        insurance_mask = expenses["Description"].str.contains(insurance_categories, case=False, na=False) == True
    if utilities_categories:
        util_mask = expenses["Description"].str.contains(utilities_categories, case=False, na=False) == True
    # Filter the rows based on each category, then finally add the remainder to other
    housing_transactions = expenses[housing_mask]
    insurance_transactions = expenses[insurance_mask]
    util_transactions = expenses[util_mask]
    other_transactions = expenses[~util_mask].merge(expenses[~insurance_mask]).merge(expenses[~housing_mask])
    return {
        "housing" : housing_transactions,
        "insurance": insurance_transactions,
        "utilities": util_transactions,
        "other": other_transactions
    }
    
def read_categories():
    from main import CATEGORIES_FILENAME
    if not CATEGORIES_FILENAME.endswith(".json"):
        raise TypeError("File must be JSON format")

    # Convert the config file name to a Path object and check that it exists.
    config_path = Path(CATEGORIES_FILENAME)
    if not config_path.is_file():
        raise FileNotFoundError(f"Config file '{CATEGORIES_FILENAME}' was not found.")

    # Read the JSON settings from the configuration file.
    with open(config_path, "r") as config_file:
        data = json.load(config_file)

        # Read optional settings from the config file.
        insurance_categories = data.get("insurance", [])
        housing_categories = data.get("housing", [])
        utilities_categories = data.get("utilities", [])
    # Return all relevant settings so other functions can use them.
    return {
        "insurance_categories": insurance_categories,
        "housing_categories": housing_categories,
        "utilities_categories": utilities_categories
    }