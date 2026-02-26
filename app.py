import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

st.title("NovaRetail Customer Intelligence Dashboard")
st.subheader("Revenue, Segmentation & Growth Insights")

# ---------------------- Load Data ---------------------- #
try:
    df = pd.read_excel("NR_dataset.xlsx")
except FileNotFoundError:
    st.error("NR_dataset.xlsx file not found. Ensure it is in the same directory as app.py.")
    st.stop()
except Exception as e:
    st.error(f"Error loading file: {e}")
    st.stop()

# Normalize column names
df.columns = (
    df.columns
    .str.strip()
    .str.lower()
    .str.replace(" ", "_")
)

# Required fields
required_fields = [
    "purchaseamount",
    "customersatisfaction",
    "transactiondate",
    "label",
    "productcategory",
    "customerregion",
    "retailchannel",
    "customergender",
    "customeragegroup",
    "customerid"
]

missing_fields = [col for col in required_fields if col not in df.columns]

if missing_fields:
    st.error(f"Missing required fields: {missing_fields}")
    st.write("Available columns:", df.columns.tolist())
    st.stop()

# Type conversions
df["purchaseamount"] = pd.to_numeric(df["purchaseamount"], errors="coerce")
df["customersatisfaction"] = pd.to_numeric(df["customersatisfaction"], errors="coerce")
df["transactiondate"] = pd.to_datetime(df["transactiondate"], errors="coerce")

df = df.dropna(subset=["purchaseamount"])

# ---------------------- Sidebar Filters ---------------------- #
st.sidebar.header("Filters")

def multiselect_filter(column_name):
    options = sorted(df[column_name].dropna().unique().tolist())
    selected = st.sidebar.multiselect(
        column_name.replace("_", " ").title(),
        options=["All"] + options,
        default=["All"]
    )
    return selected

label_filter = multiselect_filter("label")
category_filter = multiselect_filter("productcategory")
region_filter = multiselect_filter("customerregion")
channel_filter = multiselect_filter("retailchannel")
gender_filter = multiselect_filter("customergender")
agegroup_filter = multiselect_filter("customeragegroup")

# ---------------------- Filtering Logic ---------------------- #
filtered_df = df.copy()

def apply_filter(dataframe, column, selected_values):
    if "All" in selected_values:
        return dataframe
    return dataframe[dataframe[column].isin(selected_values)]

filtered_df = apply_filter(filtered_df, "label", label_filter)
filtered_df = apply_filter(filtered_df, "productcategory", category_filter)
filtered_df = apply_filter(filtered_df, "customerregion", region_filter)
filtered_df = apply_filter(filtered_df, "retailchannel", channel_filter)
filtered_df = apply_filter(filtered_df, "customergender", gender_filter)
filtered_df = apply_filter(filtered_df, "customeragegroup", agegroup_filter)

if filtered_df.empty:
    st.warning("No data available for selected filters.")
    st.stop()

# ---------------------- KPIs ---------------------- #
total_revenue = filtered_df["purchaseamount"].sum()
total_transactions = filtered_df.shape[0]
active_customers = filtered_df["customerid"].nunique()
avg_satisfaction = filtered_df["customersatisfaction"].mean()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Revenue", f"${total_revenue:,.2f}")
col2.metric("Total Transactions", f"{total_transactions:,}")
col3.metric("Active Customers", f"{active_customers:,}")
col4.metric("Average Satisfaction", f"{avg_satisfaction:.2f}")

# ---------------------- Aggregations ---------------------- #
rev_by_segment = (
    filtered_df.groupby("label")["purchaseamount"]
    .sum()
    .reset_index()
    .sort_values("purchaseamount", ascending=False)
)

rev_by_region = (
    filtered_df.groupby("customerregion")["purchaseamount"]
    .sum()
    .reset_index()
    .sort_values("purchaseamount", ascending=False)
)

rev_by_category = (
    filtered_df.groupby("productcategory")["purchaseamount"]
    .sum()
    .reset_index()
    .sort_values("purchaseamount", ascending=False)
)

rev_by_channel = (
    filtered_df.groupby("retailchannel")["purchaseamount"]
    .sum()
    .reset_index()
    .sort_values("purchaseamount", ascending=False)
)

early_warning = (
    filtered_df.groupby("label")
    .agg(
        total_revenue=("purchaseamount", "sum"),
        avg_satisfaction=("customersatisfaction", "mean")
    )
    .reset_index()
)

# ---------------------- Visualizations ---------------------- #
st.markdown("### Revenue by Segment")
fig_segment = px.bar(
    rev_by_segment,
    x="label",
    y="purchaseamount",
    title="Revenue by Segment"
)
fig_segment.update_layout(template="plotly_white")
st.plotly_chart(fig_segment, use_container_width=True)

st.markdown("### Revenue by Region")
fig_region = px.bar(
    rev_by_region,
    x="customerregion",
    y="purchaseamount",
    title="Revenue by Region"
)
fig_region.update_layout(template="plotly_white")
st.plotly_chart(fig_region, use_container_width=True)

st.markdown("### Revenue by Product Category")
fig_category = px.bar(
    rev_by_category,
    x="productcategory",
    y="purchaseamount",
    title="Revenue by Product Category"
)
fig_category.update_layout(template="plotly_white")
st.plotly_chart(fig_category, use_container_width=True)

st.markdown("### Revenue by Channel")
fig_channel = px.pie(
    rev_by_channel,
    names="retailchannel",
    values="purchaseamount",
    title="Revenue by Channel"
)
fig_channel.update_layout(template="plotly_white")
st.plotly_chart(fig_channel, use_container_width=True)

# ---------------------- Top Customers ---------------------- #
st.markdown("### Top 10 Customers by Revenue")
top_customers = (
    filtered_df.groupby("customerid")["purchaseamount"]
    .sum()
    .reset_index()
    .sort_values("purchaseamount", ascending=False)
    .head(10)
)
st.dataframe(top_customers, use_container_width=True)

# ---------------------- Strategic Insights ---------------------- #
highest_segment = rev_by_segment.iloc[0]["label"]
highest_region = rev_by_region.iloc[0]["customerregion"]
highest_category = rev_by_category.iloc[0]["productcategory"]
lowest_satisfaction_segment = (
    early_warning.sort_values("avg_satisfaction")
    .iloc[0]["label"]
)

st.markdown("### Strategic Insights")

st.write(f"• Highest Revenue Segment: {highest_segment}")
st.write(f"• Highest Revenue Region: {highest_region}")
st.write(f"• Highest Revenue Product Category: {highest_category}")
st.write(f"• Segment with Lowest Satisfaction (Decline Risk): {lowest_satisfaction_segment}")
