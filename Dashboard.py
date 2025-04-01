import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st  # Streamlit for web display

# Sample mock data simulating your inventory structure
data = [
    {"Item Code": "51503", "Description": "Bar 1.25\"", "OD": 1.25, "ID": None, "Wall": None,
     "Grade": "4140", "Origin": "USA", "Weeks Left": 45, "Usage/Week": 36.4, "In Stock (ft)": 1650,
     "PO Incoming (ft)": 0},
    {"Item Code": "52102", "Description": "Tube", "OD": 11, "ID": 8.25, "Wall": 1.38,
     "Grade": "4130M", "Origin": "China++", "Weeks Left": 15, "Usage/Week": 10.2, "In Stock (ft)": 152,
     "PO Incoming (ft)": 260},
    {"Item Code": "50086", "Description": "Bar 2.5\"", "OD": 2.5, "ID": None, "Wall": None,
     "Grade": "4140", "Origin": "USA", "Weeks Left": 12, "Usage/Week": 15, "In Stock (ft)": 300,
     "PO Incoming (ft)": 180},
    {"Item Code": "51012", "Description": "Tube", "OD": 3, "ID": 2, "Wall": 0.5,
     "Grade": "4140", "Origin": "Mexico", "Weeks Left": 8, "Usage/Week": 25, "In Stock (ft)": 200,
     "PO Incoming (ft)": 0},
    {"Item Code": "50203", "Description": "Bar 4\"", "OD": 4, "ID": None, "Wall": None,
     "Grade": "4130M", "Origin": "Italy", "Weeks Left": 31, "Usage/Week": 12, "In Stock (ft)": 600,
     "PO Incoming (ft)": 320},
]

df = pd.DataFrame(data)

# Reorder flag logic
df["Reorder Flag"] = df.apply(
    lambda x: "✅ No" if x["Weeks Left"] > 26 else ("⚠️ Caution" if 12 < x["Weeks Left"] <= 26 else "❌ Yes"), axis=1
)

# Summary tiles
summary = {
    "Total Active Items": len(df),
    "Items Below 12 Weeks": (df['Weeks Left'] < 12).sum(),
    "Avg Inventory Weeks": round(df['Weeks Left'].mean(), 1),
    "Total Feet On Hand": df['In Stock (ft)'].sum(),
    "Total PO Feet In Transit": df['PO Incoming (ft)'].sum()
}

# Dashboard Title
st.title("📊 Inventory Dashboard")

# Display Summary Metrics
st.write("## Summary")
col1, col2, col3 = st.columns(3)
col1.metric("Total Active Items", summary["Total Active Items"])
col2.metric("Items < 12 Weeks", summary["Items Below 12 Weeks"])
col3.metric("Avg Inventory Weeks", summary["Avg Inventory Weeks"])

col4, col5 = st.columns(2)
col4.metric("Feet On Hand", summary["Total Feet On Hand"])
col5.metric("PO Feet In Transit", summary["Total PO Feet In Transit"])

# Bar Plot: Inventory Weeks by Grade
st.write("## Inventory Weeks by Grade")
plt.figure(figsize=(8, 5))
sns.barplot(data=df, x="Grade", y="Weeks Left", hue="Reorder Flag")
plt.title("Inventory Weeks by Grade")
plt.ylabel("Weeks Left")
plt.xlabel("Grade")
plt.legend(title="Reorder Flag")
plt.tight_layout()
st.pyplot(plt)

# Pie Chart: Origin Distribution
st.write("## Stock by Origin")
plt.figure(figsize=(6, 6))
origin_counts = df['Origin'].value_counts()
origin_counts.plot.pie(autopct='%1.1f%%', title='Stock by Origin')
plt.ylabel('')
plt.tight_layout()
st.pyplot(plt)

# Optional: Display full table
st.write("## Full Inventory Data")
st.dataframe(df)
