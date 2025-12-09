# file: db.py
from models import SessionLocal, Account, Transaction, User
from sqlalchemy.orm import Session
import datetime
import json

def create_account(user_id: int, name: str, acct_type: str = "checking", balance=0):
    db: Session = SessionLocal()
    acct = Account(user_id=user_id, name=name, type=acct_type, balance=balance)
    db.add(acct)
    db.commit()
    db.refresh(acct)
    db.close()
    return acct

def list_accounts(user_id: int):
    db = SessionLocal()
    accts = db.query(Account).filter(Account.user_id == user_id).all()
    db.close()
    return accts

def create_transaction(user_id: int, account_id: int, amount: float, date: datetime.date = None, description: str = "", category: str = None, imported=False):
    db = SessionLocal()
    if date is None:
        date = datetime.date.today()
    tx = Transaction(user_id=user_id, account_id=account_id, amount=amount, date=date, description=description, category=category, imported=imported)
    db.add(tx)
    # update account balance
    acct = db.query(Account).filter(Account.id == account_id, Account.user_id == user_id).first()
    if acct:
        acct.balance = acct.balance + amount
    db.commit()
    db.refresh(tx)
    db.close()
    return tx

def list_transactions(user_id: int, limit: int = 200):
    db = SessionLocal()
    rows = db.query(Transaction).filter(Transaction.user_id == user_id).order_by(Transaction.date.desc()).limit(limit).all()
    db.close()
    return rows

def net_worth(user_id: int):
    db = SessionLocal()
    total = 0
    for acct in db.query(Account).filter(Account.user_id == user_id).all():
        total += float(acct.balance or 0)
    db.close()
    return total

def export_user_json(user_id: int):
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        db.close()
        return {}
    data = {
        "user": {"id": user.id, "email": user.email, "created_at": str(user.created_at)},
        "accounts": [],
        "transactions": []
    }
    for acct in user.accounts:
        data["accounts"].append({"id": acct.id, "name": acct.name, "type": acct.type, "balance": float(acct.balance or 0)})
    for tx in user.transactions:
        data["transactions"].append({
            "id": tx.id,
            "account_id": tx.account_id,
            "amount": float(tx.amount),
            "date": str(tx.date),
            "description": tx.description,
            "category": tx.category
        })
    db.close()
    return data