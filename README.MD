# Finance dashboard
A python program to plot income against expenses, showing the difference as a seperate plot. 

## Requirements
This program needs an Excel formatted file with extension .xls or .xlsx, with columns labeled Date, Amount and Description. In the config.json file you can specify any requirements, see the explanation below for more in depth instructions. You need to install any missing python libraries by using `pip install [module]`.

## Config
The config.json file needs to be set up with a few required and a few optional configuration parameters. Required parameters are bold, optional ones are italic.
- **filename (e.g. finance_2026.xls)**
- *excluded_descriptions (e.g. ["transfer", "takeout"])*
- *start_date (e.g. "2026-01-01)*
- *end_date (e.g. "2026-12-31)*
- *date_format (e.g. "%Y-%m-%d)*
- *currency (e.g. eur)*

N.B.: The default date_format is "%Y%m%d". Note that this does not include dashes (example date "20260101). If **ANY** date parameter is filled in with any other format, **make sure to fill in the date_format accordingly**! Only one of the two date fields can be filled in, any empty field will be defaulted to a max value (01-01-0000 for start_date and 31-31-9999 for end_date).

## Categories
In categories.json, add any description markers for certain transactions. For example, your rent might always have "RENT" in the description, and your insurance might always have "Insurance company" in the description. Supported categories:
- housing
- utilities
- insurance
- groceries
- streaming
- transportation
- hobbies
- loans

Currencies currently supported:
- usd ($)
- eur (€)
- gbp (£)
- jpy (¥)

Default is usd.

## Necessary python libraries:
- openpyxl
- matplotlib
- pandas
- json
- numpy