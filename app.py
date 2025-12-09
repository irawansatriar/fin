# file: app.py
import streamlit as st
from models import init_db
from auth import create_user, authenticate
from db import create_account, list_accounts, create_transaction, list_transactions, net_worth, export_user_json
from utils import parse_transactions_csv, import_transactions
import io
import json

init_db()

st.set_page_config(page_title="Personal Finance (Streamlit)", layout="wide")

if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "email" not in st.session_state:
    st.session_state.email = ""

def login_ui():
    st.title("Personal Finance — Login / Register")
    tab = st.radio("Action", ["Login", "Register"])
    email = st.text_input("Email", value=st.session_state.get("email", ""))
    password = st.text_input("Password", type="password")
    if tab == "Register":
        if st.button("Create account"):
            try:
                user = create_user(email=email, password=password)
                st.success("Account created. Please login.")
            except Exception as e:
                st.error(str(e))
    else:
        if st.button("Login"):
            user = authenticate(email=email, password=password)
            if user:
                st.session_state.user_id = user.id
                st.session_state.email = user.email
                st.experimental_rerun()
            else:
                st.error("Invalid credentials")

def main_ui():
    st.sidebar.title(f"Hi, {st.session_state.email}")
    if st.sidebar.button("Logout"):
        st.session_state.user_id = None
        st.session_state.email = ""
        st.experimental_rerun()

    page = st.sidebar.selectbox("Navigation", ["Overview", "Accounts", "Transactions", "Import CSV", "Export / Backup"])
    user_id = st.session_state.user_id

    if page == "Overview":
        st.header("Net Worth")
        nw = net_worth(user_id)
        st.metric("Net Worth (approx)", f"${nw:,.2f}")
        st.header("Recent Transactions")
        rows = list_transactions(user_id, limit=50)
        st.dataframe([{
            "date": str(r.date),
            "account": r.account.name if r.account else r.account_id,
            "amount": float(r.amount),
            "desc": r.description,
            "category": r.category
        } for r in rows])

    elif page == "Accounts":
        st.header("Accounts")
        if st.button("Add account"):
            with st.form("account_form", clear_on_submit=True):
                name = st.text_input("Account name")
                typ = st.selectbox("Type", ["checking", "credit", "cash", "investment"])
                balance = st.number_input("Balance", value=0.0, format="%.2f")
                submitted = st.form_submit_button("Create")
                if submitted:
                    create_account(user_id=user_id, name=name, acct_type=typ, balance=balance)
                    st.success("Account created.")
        accts = list_accounts(user_id)
        st.table([{"id": a.id, "name": a.name, "type": a.type, "balance": float(a.balance or 0)} for a in accts])

    elif page == "Transactions":
        st.header("Add Transaction")
        accts = list_accounts(user_id)
        if not accts:
            st.info("Create an account first.")
        else:
            with st.form("tx_form", clear_on_submit=True):
                account_map = {f"{a.name} (id:{a.id})": a.id for a in accts}
                acct_choice = st.selectbox("Account", list(account_map.keys()))
                amount = st.number_input("Amount (use negative for spend)", format="%.2f")
                date = st.date_input("Date")
                desc = st.text_input("Description")
                cat = st.text_input("Category")
                submitted = st.form_submit_button("Add")
                if submitted:
                    create_transaction(user_id=user_id, account_id=account_map[acct_choice], amount=amount, date=date, description=desc, category=cat)
                    st.success("Transaction added.")
        st.header("Recent")
        rows = list_transactions(user_id, limit=100)
        st.dataframe([{"date": str(r.date), "account": r.account.name if r.account else r.account_id, "amount": float(r.amount), "desc": r.description, "category": r.category} for r in rows])

    elif page == "Import CSV":
        st.header("Import CSV")
        st.markdown("CSV needs at least `date` and `amount` columns. Optional: `description`, `category`.")
        uploaded = st.file_uploader("Choose CSV", type="csv")
        accts = list_accounts(user_id)
        if uploaded and accts:
            df_rows = None
            try:
                df_rows = parse_transactions_csv(io.BytesIO(uploaded.getvalue()))
                st.write("Preview:", df_rows[:5])
            except Exception as e:
                st.error(str(e))
            if df_rows:
                default_acct = accts[0].id
                if st.button("Import to first account"):
                    import_transactions(user_id=user_id, default_account_id=default_acct, parsed_rows=df_rows)
                    st.success("Imported.")
        elif not accts:
            st.info("Create an account before importing.")

    elif page == "Export / Backup":
        st.header("Export")
        data = export_user_json(user_id)
        st.download_button("Download JSON Backup", data=json.dumps(data, indent=2), file_name="pf-backup.json", mime="application/json")
        st.markdown("You can also copy/paste or use DB file `finance.db` (if running locally).")

if st.session_state.user_id:
    main_ui()
else:
    login_ui()