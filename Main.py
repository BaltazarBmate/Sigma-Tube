import streamlit as st

st.title("📂 Main Page - Inventory Management")

st.write("Select an application to launch:")

col1, col2 = st.columns(2)

with col1:
    if st.button("📊 Open Inventory Dashboard"):
        st.query_params(page="dashboard")
        st.write("Redirecting to Dashboard...")
        st.experimental_rerun()

with col2:
    if st.button("📦 Open Full Inventory Report"):
        st.query_params(page="full_report")
        st.write("Redirecting to Full Inventory Report...")
        st.experimental_rerun()

# Check the query parameters to determine which page to load
query_params = st.experimental_get_query_params()

if query_params.get("page") == ["dashboard"]:
    exec(open("Dashboard.py").read())
elif query_params.get("page") == ["full_report"]:
    exec(open("import_streamlit_as_st.py").read())
else:
    st.write("Please select an application from the buttons above.")