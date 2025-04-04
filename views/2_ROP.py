import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import altair as alt
from sqlalchemy import create_engine
import re

# Page title
st.title("📦 Full Inventory Report")

# Database connection
engine = create_engine(f"mssql+pymssql://{st.secrets["username"]}:{st.secrets["password"]}@{st.secrets["server"]}:{st.secrets["port"]}/{st.secrets["database"]}")

# Text input for item ID
item_id = st.text_input("Enter Item Number", value="50002")

# ---------- Button 1: Report by ITEM ----------
if st.button("Report by ITEM"):
    full_report_query = f"""
        SELECT [Size Text], Description, SMO
        FROM ROPData
        WHERE Item = {item_id};

        WITH Months AS (
            SELECT FORMAT(DATEADD(MONTH, -n, CAST(GETDATE() AS DATE)), 'yyyy-MM') AS Month
            FROM (SELECT TOP 13 ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) - 1 AS n FROM sys.all_objects) AS x
        ),
        Aggregated AS (
            SELECT
                FORMAT(DATEFROMPARTS(2000 + IHTRYY, IHTRMM, 1), 'yyyy-MM') AS Month,
                CASE 
                    WHEN CONVERT(VARCHAR(10), IHTRNT) = 'IA' THEN IHTQTY
                    WHEN CONVERT(VARCHAR(10), IHTRNT) IN ('OW', 'OR') THEN IHTQTY
                    WHEN CONVERT(VARCHAR(10), IHTRNT) = 'IN' THEN IHTQTY
                    ELSE 0
                END AS Qty,
                CONVERT(VARCHAR(10), IHTRNT) AS Type
            FROM UsageData
            WHERE IHITEM = {item_id}
              AND DATEFROMPARTS(2000 + IHTRYY, IHTRMM, 1) >= DATEADD(MONTH, -13, CAST(GETDATE() AS DATE))
        )
        SELECT 
            m.Month,
            CASE 
                WHEN SUM(CASE WHEN a.Type = 'IA' THEN a.Qty ELSE 0 END) = 0 THEN '-'
                ELSE FORMAT(SUM(CASE WHEN a.Type = 'IA' THEN a.Qty ELSE 0 END), 'N2')
            END AS [IA (Inventory Adjustments)],
            CASE 
                WHEN SUM(CASE WHEN a.Type IN ('OW', 'OR') THEN a.Qty ELSE 0 END) = 0 THEN '-'
                ELSE FORMAT(SUM(CASE WHEN a.Type IN ('OW', 'OR') THEN a.Qty ELSE 0 END), 'N2')
            END AS [MP (Material Processed)],
            CASE 
                WHEN SUM(CASE WHEN a.Type = 'IN' THEN a.Qty ELSE 0 END) = 0 THEN '-'
                ELSE FORMAT(SUM(CASE WHEN a.Type = 'IN' THEN a.Qty ELSE 0 END), 'N2')
            END AS [SO (Sales Orders)]
        FROM Months m
        LEFT JOIN Aggregated a ON m.Month = a.Month
        GROUP BY m.Month
        ORDER BY m.Month;

        SELECT [OnHand], [Rsrv], [OnHand] - [Rsrv] AS [Available Inv]
        FROM ROPData
        WHERE Item = {item_id};

        SELECT 'Usage and Vendor' AS [Title], [#/ft], [UOM], [$/ft], [con/wk], [Vndr]
        FROM ROPData
        WHERE Item = {item_id};

        SELECT 'When do we need to purchase and how much' AS [Question],
            [OnHand] - [Rsrv] AS [Available Inv],
            ([#/ft] * ([OnHand] - [Rsrv])) AS [Pounds],
            [$/ft] * ([OnHand] - [Rsrv]) AS [Dollars],
            ([OnHand] - [Rsrv]) / [con/wk] AS [Weeks],
            DATEADD(WEEK, ([OnHand] - [Rsrv]) / [con/wk], CAST(GETDATE() AS DATE)) AS [Expected Depletion Date]
        FROM ROPData
        WHERE Item = {item_id};
    """

    try:
        result_sets = []
        with engine.begin() as conn:
            for sql in full_report_query.strip().split(";"):
                if sql.strip():
                    result = pd.read_sql(sql, conn)
                    result_sets.append(result)

        st.success("✅ All data loaded successfully!")

        titles = [
            "🔍 Item Being Reviewed",
            "📈 IA / MP / SO Summary (Last 13 Months)",
            "📦 Inventory On Hand vs Reserved",
            "🧪 Usage and Vendor",
            "📅 Depletion Forecast",
        ]

        for i, df in enumerate(result_sets):
            st.subheader(titles[i] if i < len(titles) else f"Result {i + 1}")
            st.dataframe(df)

        if len(result_sets) >= 3 and not result_sets[2].empty:
            inventory_df = result_sets[2]
            chart_data = pd.DataFrame({
                "Metric": ["OnHand", "Reserved", "Available"],
                "Value": [
                    float(inventory_df.at[0, "OnHand"]),
                    float(-inventory_df.at[0, "Rsrv"]),
                    float(inventory_df.at[0, "Available Inv"])
                ]
            })

            st.subheader("📊 Inventory Overview Chart")
            bar_chart = alt.Chart(chart_data).mark_bar().encode(
                x=alt.X("Metric", title="Metric"),
                y=alt.Y("Value", title="Feet", scale=alt.Scale(zero=True)),
                color=alt.Color("Metric", legend=None)
            ).properties(width=500, height=300)

            st.altair_chart(bar_chart)

    except Exception as e:
        st.error(f"❌ Failed to run the report: {e}")

# ---------- Button 2: Show full ROP table ----------
if st.button("Show ROP Table"):
    try:
        with engine.begin() as conn:
            st.write("🔄 Fetching full ROP table...")
            df = pd.read_sql("SELECT * FROM ROP", conn)
            st.success("✅ ROP table loaded successfully!")
            st.dataframe(df)
    except Exception as e:
        st.error(f"❌ Failed to fetch ROP table: {e}")

# ---------- Button 3: Count ROP by group ----------
if st.button("Count ROP by group"):
    try:
        with engine.begin() as conn:
            df = pd.read_sql("""
                SELECT 
                    RTRIM(CAST(Column3 AS VARCHAR(MAX))) AS Type,
                    COUNT(*) AS Total
                FROM ROP
                WHERE Column3 IS NOT NULL
                GROUP BY RTRIM(CAST(Column3 AS VARCHAR(MAX)))
                ORDER BY Total DESC;
            """, conn)
            st.success("✅ Count by ROP loaded successfully!")
            st.dataframe(df)
    except Exception as e:
        st.error(f"❌ Failed to fetch ROP Count: {e}")

# ---------- Button 4: Summary Dashboard ----------
if st.button("📦 Show Summary Dashboard"):
    try:
        st.write("🔄 Fetching live data from ROPData...")

        with engine.begin() as conn:
            df = pd.read_sql("SELECT * FROM ROPData", conn)

        df = df.rename(columns={
            "OnHand": "In Stock (ft)",
            "OnPO": "PO Incoming (ft)",
            "#/ft": "Feet per Unit",
            "con/wk": "Usage/Week",
            "FastPathSort": "Grade"
        })

        df = df[df["Usage/Week"].notnull() & (df["Usage/Week"] != 0)]
        df["Weeks Left"] = (df["In Stock (ft)"] / df["Usage/Week"]).round(1)

        df["Reorder Flag"] = df["Weeks Left"].apply(
            lambda w: "✅ No" if w > 26 else ("⚠️ Caution" if 12 < w <= 26 else "❌ Yes")
        )

        df["Origin"] = df["Description"].apply(lambda x: "China" if "++" in str(x) else "Other")

        st.subheader("📋 Summary")
        summary = {
            "Total Active Items": len(df),
            "Items Below 12 Weeks": (df['Weeks Left'] < 12).sum(),
            "Avg Inventory Weeks": round(df['Weeks Left'].mean(), 1),
            "Total Feet On Hand": df['In Stock (ft)'].sum(),
            "Total PO Feet In Transit": df['PO Incoming (ft)'].sum()
        }

        for k, v in summary.items():
            st.metric(label=k, value=v)

        st.subheader("📊 Inventory Weeks by Grade")
        plt.figure(figsize=(8, 5))
        sns.barplot(data=df, x="Grade", y="Weeks Left", hue="Reorder Flag")
        plt.title("Inventory Weeks by Grade")
        plt.tight_layout()
        st.pyplot(plt)

        st.subheader("🌍 Stock by Origin")
        origin_counts = df["Origin"].value_counts()
        plt.figure(figsize=(6, 6))
        origin_counts.plot.pie(autopct='%1.1f%%', title="Stock by Origin")
        plt.ylabel('')
        plt.tight_layout()
        st.pyplot(plt)
  
    except Exception as e:
        st.error(f"❌ Failed to load dashboard: {e}")


### ---- Filter
st.subheader("📦 ROP Summary")
st.write("Select Vendors")
with engine.begin() as conn:
    df = pd.read_sql("SELECT * FROM ROPData", conn)

df = df.rename(columns={
    "OnHand": "In Stock (ft)",
    "OnPO": "PO Incoming (ft)",
    "#/ft": "Feet per Unit",
    "con/wk": "Usage/Week",
    "FastPathSort": "Grade"
})

df = df[df["Usage/Week"].notnull() & (df["Usage/Week"] != 0)]
df["Weeks Left"] = (df["In Stock (ft)"] / df["Usage/Week"]).round(1)

df["Reorder Flag"] = df["Weeks Left"].apply(
    lambda w: "✅ No" if w > 26 else ("⚠️ Caution" if 12 < w <= 26 else "❌ Yes")
)

df["Origin"] = df["Description"].apply(lambda x: "China" if "++" in str(x) else "Other")


unique_vendors = sorted(df["Vndr"].unique())
selected_vendors = st.multiselect("Select Vendors to Include", unique_vendors, default=unique_vendors)

# Button to generate the filtered and ordered table
if st.button("Run Filtered ROPData Report"):
    
    # Filter the DataFrame based on selected vendors
    filtered_df = df[df["Vndr"].isin(selected_vendors)]

    # Reorder the dataframe based on the Reorder Flag
    reorder_priority = {"❌ Yes": 0, "⚠️ Caution": 1, "✅ No": 2}
    filtered_df["Reorder Priority"] = filtered_df["Reorder Flag"].map(reorder_priority)
    filtered_df = filtered_df.sort_values(by="Reorder Priority").drop(columns=["Reorder Priority"])

    # Select and reorder the columns as specified
    columns_to_display = ["Item", "Description", "OD", "ID", "Wall", "Usage/Week", "Weeks Left", "Reorder Flag"]
    filtered_df = filtered_df[columns_to_display]

    # Display the filtered and sorted dataframe
    st.write("📄 Filtered ROPData Table")
    st.dataframe(filtered_df)


    # ---- Family Existence Calculation ----
    def extract_family_items(comment):
        """Extracts item numbers from the comment field."""
        import re
        matches = re.findall(r'!(\d+)', str(comment))
        return [int(match) for match in matches]

    # Filter to include only rows classified as "Yes" and "Caution"
    critical_df = filtered_df[filtered_df["Reorder Flag"].isin(["❌ Yes", "⚠️ Caution"])].copy()

    # Initialize the Family Existence column
    critical_df["Family Existence"] = 0.0

    for idx, row in critical_df.iterrows():
        # Get the family items from the full df, not just filtered
        family_items = extract_family_items(df.loc[df["Item"] == row["Item"], "comment"].values[0])
        
        # Start with the existence of the current item  
        family_existence = df.loc[df["Item"] == row["Item"], "In Stock (ft)"].sum()

        # Sum existence of all related family items from the full df
        for family_item in family_items:
            family_existence += df.loc[df["Item"] == family_item, "In Stock (ft)"].sum()

        critical_df.at[idx, "Family Existence"] = family_existence

    # Select and reorder the columns for the critical table
    critical_columns = ["Item", "Description", "Usage/Week", "Weeks Left", "Reorder Flag", "Family Existence"]
    critical_df = critical_df[critical_columns]

    # Display the critical table with Family Existence
    st.write("🚨 Critical Items with Family Existence")
    st.dataframe(critical_df)