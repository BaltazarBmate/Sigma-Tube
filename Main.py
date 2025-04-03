import streamlit as st

# --- PAGE SETUP ---

Dashboard_page = st.Page(
    page="views/1_Dashboard.py",
    title="Dashboard",
    default=True,
)

ROP_page = st.Page(
    page="views/2_ROP.py",
    title="ROP",

)



# --- Navigation Setup ---

pg = st.navigation(pages=[Dashboard_page,ROP_page])


# --- SHARED ON ALL PAGES ---
st.logo("assets/SigmaTube-Bar.jpeg",size="large")



# --- Run Navigation ---
pg.run()