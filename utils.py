# file: utils.py
import pandas as pd
from db import create_transaction
import datetime

def parse_transactions_csv(file_like):
    # Expects CSV columns: date,amount,description,account,category
    df = pd.read_csv(file_like)
    # Normalize columns
    df.columns = [c.strip().lower() for c in df.columns]
    required = {"date", "amount"}
    if not required.issubset(set(df.columns)):
        raise ValueError("CSV must contain at least 'date' and 'amount' columns")
    # parse date
    df['date'] = pd.to_datetime(df['date']).dt.date
    return df.to_dict(orient="records")

def import_transactions(user_id: int, default_account_id: int, parsed_rows):
    results = []
    for r in parsed_rows:
        date = r.get("date")
        amount = float(r.get("amount"))
        desc = r.get("description") or ""
        category = r.get("category")
        # Create tx (mark as imported)
        tx = create_transaction(user_id=user_id, account_id=default_account_id, amount=amount, date=date, description=desc, category=category, imported=True)
        results.append(tx)
    return results