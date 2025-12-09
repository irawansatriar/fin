# file: app.py (edit login_ui function)
from db import user_count
from auth import create_user

def login_ui():
    st.title("Personal Finance — Login / Register")
    # Show password rules
    st.info("Passwords must be at least 8 characters. Avoid >72 bytes when using bcrypt.")
    tab = st.radio("Action", ["Login", "Register"])
    email = st.text_input("Email", value=st.session_state.get("email", ""))
    password = st.text_input("Password", type="password")

    # If no users exist offer a demo account to speed testing
    if user_count() == 0:
        st.warning("No users found. You can create a demo account for testing.")
        if st.button("Create demo account (demo@example.com / demo12345)"):
            try:
                create_user("demo@example.com", "demo12345")
                st.success("Demo account created. Use demo@example.com / demo12345 to log in.")
            except Exception as e:
                st.error(str(e))

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
