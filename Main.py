import streamlit as st

# --- PAGE SETUP ---
ROP_page = st.Page(
    page="views/1_ROP.py",
    title="ROP",
    default=True,
)

Dashboard_page = st.Page(
    page="views/2_Dashboard.py",
    title="Dashboard",
)

# --- Navigation Setup ---

pg = st.navigation(pages=[ROP_page,Dashboard_page])


# --- SHARED ON ALL PAGES ---
st.logo("assets/SigmaTube-Bar.jpeg",size="large")



# --- Run Navigation ---
pg.run()