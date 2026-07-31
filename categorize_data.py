from pathlib import Path
import json, pandas as pd
def categorize_expenses():
    """Categorize the expenses, based on description elements specified by the JSON file."""
    from util import filter_data
    data = filter_data()
    categories = parse_categories()
    
    expenses = data.loc[data["Amount"] < 0, ["Date", "Amount", "Description"]].reset_index(drop=True)

    housing = '|'.join(categories["housing"])
    insurance = '|'.join(categories["insurance"])
    utils = '|'.join(categories["utilities"])
    groceries = '|'.join(categories["groceries"])
    streaming = '|'.join(categories["streaming"])
    transportation = '|'.join(categories["transportation"])
    hobbies = '|'.join(categories["hobbies"])
    loans = '|'.join(categories["loans"])
    
    # Create masks by filtering rows if description matches any of the categories.
    housing_mask = pd.Series(True, index=expenses.index)
    insurance_mask = pd.Series(True, index=expenses.index)
    util_mask = pd.Series(True, index=expenses.index)
    grocery_mask = pd.Series(True, index=expenses.index)
    streaming_mask = pd.Series(True, index=expenses.index)
    transportation_mask = pd.Series(True, index=expenses.index)
    hobbies_mask = pd.Series(True, index=expenses.index)
    loans_mask = pd.Series(True, index=expenses.index)
    
    # Mask each category to filter easily
    if housing:
        housing_mask = expenses["Description"].str.contains(housing, case=False, na=False) == True
    if insurance:
        insurance_mask = expenses["Description"].str.contains(insurance, case=False, na=False) == True
    if utils:
        util_mask = expenses["Description"].str.contains(utils, case=False, na=False) == True
    if groceries:
        grocery_mask = expenses["Description"].str.contains(groceries, case=False, na=False) == True
    if streaming:
        streaming_mask = expenses["Description"].str.contains(streaming, case=False, na=False) == True
    if streaming:
        streaming_mask = expenses["Description"].str.contains(streaming, case=False, na=False) == True
    if transportation:
        transportation_mask = expenses["Description"].str.contains(transportation, case=False, na=False) == True
    if hobbies:
        hobbies_mask = expenses["Description"].str.contains(hobbies, case=False, na=False) == True
    if loans:
        loans_mask = expenses["Description"].str.contains(loans, case=False, na=False) == True
    
    other_mask = (~housing_mask  & ~insurance_mask & ~util_mask & ~grocery_mask & ~streaming_mask & ~transportation_mask & ~hobbies_mask & ~loans_mask)
        
    # Filter the rows based on each category, then finally add the remainder to other
    housing_transactions = expenses[housing_mask]
    insurance_transactions = expenses[insurance_mask]
    util_transactions = expenses[util_mask]
    grocery_transactions = expenses[grocery_mask]
    streaming_transactions = expenses[streaming_mask]
    transportation_transactions = expenses[transportation_mask]
    hobbies_transactions = expenses[hobbies_mask]
    loans_transactions = expenses[loans_mask]
    other_transactions = expenses[other_mask].copy()
        
    return {
        "housing" : housing_transactions,
        "insurance": insurance_transactions,
        "utilities": util_transactions,
        "groceries": grocery_transactions,
        "streaming" : streaming_transactions,
        "transportation" : transportation_transactions,
        "hobbies" : hobbies_transactions,
        "loans" : loans_transactions,
        "other": other_transactions
    }
    
def parse_categories():
    """Parses the description selectors for each category, if supplied"""
    from util import CATEGORIES_FILENAME
    if not CATEGORIES_FILENAME.endswith(".json"):
        raise TypeError("Categories file must be JSON format")

    # Convert the config file name to a Path object and check that it exists. Returns if no categories were specified
    config_path = Path(CATEGORIES_FILENAME)
    if not config_path.is_file():
        return

    # Read the JSON settings from the configuration file.
    with open(config_path, "r") as config_file:
        data = json.load(config_file)

        # Read optional settings from the config file.
        insurance = data.get("insurance", [])
        housing = data.get("housing", [])
        utils = data.get("utilities", [])
        grocery = data.get("groceries", [])
        streaming = data.get("streaming", [])
        transportation = data.get("transportation", [])
        hobbies = data.get("hobbies", [])
        loans = data.get("loans", [])
    # Return all relevant settings so other functions can use them.
    return {
        "insurance": insurance,
        "housing": housing,
        "utilities": utils,
        "groceries" : grocery,
        "streaming" : streaming,
        "transportation": transportation,
        "hobbies": hobbies,
        "loans": loans
    }