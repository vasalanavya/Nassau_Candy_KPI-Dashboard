import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Nassau Candy KPI Dashboard",
    layout="wide"
)

st.title("Nassau Candy - KPI Dashboard")
st.write("Product Profitability and Margin Performance Analysis")

# 1. Upload CSV file
uploaded_file = st.file_uploader(
    "Upload Nassau Candy CSV file",
    type=["csv"]
)

if uploaded_file is not None:

    df = pd.read_csv(uploaded_file)

    # 2. Clean column names
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
    )

    # Check required columns
    required_columns = [
        "product_name",
        "sales",
        "gross_profit",
        "units",
        "order_date"
    ]

    missing = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing:
        st.error(f"Missing columns: {missing}")
        st.write("Available columns:", df.columns.tolist())
        st.stop()

    # 3. Convert columns into correct data types
    for col in ["sales", "gross_profit", "units"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["order_date"] = pd.to_datetime(
        df["order_date"], errors="coerce"
    )

    df["product_name"] = (
        df["product_name"].fillna("Unknown")
    )

    # 4. Remove rows with missing KPI inputs
    df = df.dropna(
        subset=["sales", "gross_profit", "units"]
    )

    # 5. Calculate overall KPIs
    total_sales = df["sales"].sum()
    total_profit = df["gross_profit"].sum()
    total_units = df["units"].sum()

    gross_margin = (
        total_profit / total_sales * 100
        if total_sales != 0 else 0
    )

    profit_per_unit = (
        total_profit / total_units
        if total_units != 0 else 0
    )

    # 6. Product-level calculations
    product_kpi = (
        df.groupby("product_name")
        .agg(
            Sales=("sales", "sum"),
            Gross_Profit=("gross_profit", "sum"),
            Units=("units", "sum")
        )
        .reset_index()
    )

    product_kpi["Gross_Margin_%"] = (
        product_kpi["Gross_Profit"]
        .div(product_kpi["Sales"].replace(0, float("nan")))
        * 100
    )

    product_kpi["Profit_Per_Unit"] = (
        product_kpi["Gross_Profit"]
        .div(product_kpi["Units"].replace(0, float("nan")))
    )

    # Revenue contribution
    if total_sales != 0:
        product_kpi["Revenue_Contribution_%"] = (
            product_kpi["Sales"] / total_sales * 100
        )
    else:
        product_kpi["Revenue_Contribution_%"] = 0

    # Profit contribution
    if total_profit != 0:
        product_kpi["Profit_Contribution_%"] = (
            product_kpi["Gross_Profit"] / total_profit * 100
        )
    else:
        product_kpi["Profit_Contribution_%"] = 0

    # 7. Margin volatility calculation
    df["Month"] = (
        df["order_date"].dt.to_period("M").astype(str)
    )

    monthly = (
        df[df["sales"] != 0]
        .groupby(["product_name", "Month"])
        .agg(
            Sales=("sales", "sum"),
            Gross_Profit=("gross_profit", "sum")
        )
        .reset_index()
    )

    monthly["Monthly_Margin_%"] = (
        monthly["Gross_Profit"] / monthly["Sales"] * 100
    )

    volatility = (
        monthly.groupby("product_name")[
            "Monthly_Margin_%"
        ]
        .std()
        .reset_index(name="Margin_Volatility")
    )

    product_kpi = product_kpi.merge(
        volatility,
        on="product_name",
        how="left"
    )

    # 8. Dashboard KPI cards
    st.header("Key Performance Indicators")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Gross Margin %",
        f"{gross_margin:.2f}%"
    )

    c2.metric(
        "Profit Per Unit",
        f"{profit_per_unit:,.2f}"
    )

    top_revenue = (
        product_kpi["Revenue_Contribution_%"].max()
        if not product_kpi.empty else 0
    )

    top_profit = (
        product_kpi["Profit_Contribution_%"].max()
        if not product_kpi.empty else 0
    )

    c3.metric(
        "Top Revenue Contribution",
        f"{top_revenue:.2f}%"
    )

    c4.metric(
        "Top Profit Contribution",
        f"{top_profit:.2f}%"
    )

    # 9. Display product KPI table
    st.header("Product Level KPI Analysis")

    st.dataframe(
        product_kpi.sort_values(
            "Gross_Profit", ascending=False
        ),
        use_container_width=True
    )

    # 10. Gross Margin chart
    st.subheader("Gross Margin Percentage by Product")

    margin_chart = product_kpi.nlargest(
        15, "Gross_Margin_%"
    )

    fig1 = px.bar(
        margin_chart,
        x="product_name",
        y="Gross_Margin_%",
        title="Top 15 Products by Gross Margin",
        labels={
            "product_name": "Product",
            "Gross_Margin_%": "Gross Margin %"
        }
    )

    st.plotly_chart(fig1, use_container_width=True)

    # 11. Profit per Unit chart
    st.subheader("Profit Per Unit by Product")

    fig2 = px.bar(
        product_kpi.nlargest(15, "Profit_Per_Unit"),
        x="product_name",
        y="Profit_Per_Unit",
        title="Top 15 Products by Profit Per Unit"
    )

    st.plotly_chart(fig2, use_container_width=True)

    # 12. Revenue Contribution chart
    st.subheader("Revenue Contribution by Product")

    revenue_data = product_kpi.nlargest(
        10, "Revenue_Contribution_%"
    )

    fig3 = px.pie(
        revenue_data,
        names="product_name",
        values="Revenue_Contribution_%",
        title="Top 10 Products Revenue Contribution"
    )

    st.plotly_chart(fig3, use_container_width=True)

    # 13. Profit Contribution chart
    st.subheader("Product Profit Contribution")

    profit_data = product_kpi.nlargest(
        10, "Profit_Contribution_%"
    )

    fig4 = px.bar(
        profit_data,
        x="product_name",
        y="Profit_Contribution_%",
        title="Top 10 Products by Profit Contribution"
    )

    st.plotly_chart(fig4, use_container_width=True)

    # 14. Margin Volatility chart
    st.subheader("Monthly Margin Volatility")

    available_products = monthly["product_name"].unique()

    if len(available_products) > 0:

        selected_product = st.selectbox(
            "Select Product",
            available_products
        )

        trend = monthly[
            monthly["product_name"] == selected_product
        ]

        fig5 = px.line(
            trend,
            x="Month",
            y="Monthly_Margin_%",
            markers=True,
            title=f"Monthly Margin Trend - {selected_product}"
        )

        st.plotly_chart(fig5, use_container_width=True)

        selected_volatility = volatility[
            volatility["product_name"] == selected_product
        ]["Margin_Volatility"]

        if not selected_volatility.empty:
            st.write(
                "Margin Volatility (Standard Deviation):",
                selected_volatility.iloc[0]
            )

    else:
        st.info("No valid monthly margin data available.")

else:
    st.info("Please upload your Nassau_Candy.csv file.")
 
