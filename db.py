# file: db.py
"""
Database helper functions used by the Streamlit app.

Safe patterns:
- Always close SQLAlchemy sessions (try/finally).
- Use Decimal for numeric math with SQLAlchemy Numeric columns.
- Return ORM objects where the app expects them (existing code uses attributes).
"""

from decimal import Decimal
import datetime
import json
from typing import List, Any, Dict

from models import SessionLocal, Account, Transaction, User


def create_account(user_id: int, name: str, acct_type: str = "checking", balance: float = 0.0) -> Account:
    """
    Create an account for a user and return the Account instance.
    """
    db = SessionLocal()
    try:
        acct = Account(user_id=user_id, name=name, type=acct_type, balance=Decimal(str(balance)))
        db.add(acct)
        db.commit()
        db.refresh(acct)
        return acct
    finally:
        db.close()


def list_accounts(user_id: int) -> List[Account]:
    """
    Return a list of Account objects for the given user.
    """
    db = SessionLocal()
    try:
        return db.query(Account).filter(Account.user_id == user_id).all()
    finally:
        db.close()


def create_transaction(
    user_id: int,
    account_id: int,
    amount: float,
    date: datetime.date = None,
    description: str = "",
    category: str = None,
    imported: bool = False,
) -> Transaction:
    """
    Create a transaction, update the related account balance, and return the Transaction object.
    Amount should be positive for deposits and negative for spends (matching earlier UI).
    """
    db = SessionLocal()
    try:
        if date is None:
            date = datetime.date.today()

        tx = Transaction(
            user_id=user_id,
            account_id=account_id,
            amount=Decimal(str(amount)),
            date=date,
            description=description,
            category=category,
            imported=imported,
        )
        db.add(tx)

        # Update account balance safely using Decimal
        acct = db.query(Account).filter(Account.id == account_id, Account.user_id == user_id).first()
        if acct is not None:
            prev = acct.balance or Decimal("0")
            acct.balance = prev + Decimal(str(amount))

        db.commit()
        db.refresh(tx)
        return tx
    finally:
        db.close()


def list_transactions(user_id: int, limit: int = 200) -> List[Transaction]:
    """
    Return recent transactions for a user (ordered by date desc).
    """
    db = SessionLocal()
    try:
        return db.query(Transaction).filter(Transaction.user_id == user_id).order_by(Transaction.date.desc()).limit(limit).all()
    finally:
        db.close()


def net_worth(user_id: int) -> float:
    """
    Sum up the balances of all accounts for a user and return a float.
    """
    db = SessionLocal()
    try:
        total = Decimal("0")
        for acct in db.query(Account).filter(Account.user_id == user_id).all():
            total += acct.balance or Decimal("0")
        return float(total)
    finally:
        db.close()


def export_user_json(user_id: int) -> Dict[str, Any]:
    """
    Export user, accounts, and transactions as a JSON-serializable dict.
    """
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {}

        data = {
            "user": {"id": user.id, "email": user.email, "created_at": str(user.created_at)},
            "accounts": [],
            "transactions": [],
        }

        for acct in user.accounts:
            data["accounts"].append(
                {"id": acct.id, "name": acct.name, "type": acct.type, "balance": float(acct.balance or 0)}
            )

        for tx in user.transactions:
            data["transactions"].append(
                {
                    "id": tx.id,
                    "account_id": tx.account_id,
                    "amount": float(tx.amount),
                    "date": str(tx.date),
                    "description": tx.description,
                    "category": tx.category,
                }
            )

        return data
    finally:
        db.close()


def user_count() -> int:
    """
    Return number of users in the DB. Added because app imports this helper.
    """
    db = SessionLocal()
    try:
        return db.query(User).count()
    finally:
        db.close()
