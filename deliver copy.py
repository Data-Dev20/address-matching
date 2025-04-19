import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO

def assign_deliveries(deliveries_df, agents_df):
    # Standardize column names
    deliveries_df.rename(columns={"Pincode": "pincode", "Cluster": "cluster_name", "AWB NO": "awb_no", "Remark": "remark"}, inplace=True, errors="ignore")
    agents_df.rename(columns={"pincode": "pincode", "Agent": "agent_name"}, inplace=True, errors="ignore")
    
    # Ensure unique delivery IDs exist
    if "MID" not in deliveries_df.columns:
        deliveries_df["MID"] = range(1, len(deliveries_df) + 1)

    # Identify the most frequent pincode per agent
    if "pincode" in agents_df.columns:
        agent_pincode_mapping = agents_df.groupby("agent_name")["pincode"].agg(lambda x: x.mode()[0] if not x.mode().empty else x.iloc[0]).to_dict()
    else:
        agent_pincode_mapping = {}

   

    # Create a 10-day delivery schedule
    start_date = datetime(2025, 4, 2)  # Fixed start date
    date_range = [start_date + timedelta(days=i) for i in range(10)]
    date_columns = [date.strftime("%d-%m-%Y") for date in date_range]

    # Add empty date columns to deliveries_df
    for date_col in date_columns:
        deliveries_df[date_col] = ""
    
    # Set fixed daily delivery limit per agent
    DAILY_ASSIGNMENT = 55
    TOTAL_DAILY_LIMIT = 18 * DAILY_ASSIGNMENT  # 990 total daily deliveries
    
    # Track agent workload
    agent_workload = {agent: {date: 0 for date in date_range} for agent in agents_df["agent_name"].unique()}
    
    # Track assigned AWB numbers to prevent reassignment
    assigned_awbs = set()
    
    # Assign deliveries to agents **over 10 days**
    for date in date_range:
        date_col = date.strftime("%d-%m-%Y")  # Column name for the current date

        # Track total deliveries assigned for the day
        total_daily_assigned = 0

        for agent_name in agents_df["agent_name"].unique():
            if total_daily_assigned >= TOTAL_DAILY_LIMIT:
                break  # Stop if the daily limit is reached

            agent_pincode = agent_pincode_mapping.get(agent_name, None)
            if not agent_pincode:
                continue  # Skip if no pincode found

            # Get pending deliveries for the agent's pincode **for the current day**
            pending_deliveries = deliveries_df[
                (deliveries_df["pincode"] == agent_pincode) &
                (deliveries_df[date_col] == "") &  # Ensure it's not already assigned
                (~deliveries_df["awb_no"].isin(assigned_awbs)) &  # Ensure AWB is not reassigned
                (deliveries_df["remark"] != "CD")  # Exclude "CD" remarks

            ]

            if pending_deliveries.empty:
                continue  # Skip if no deliveries left for this pincode

            # Select exactly 55 deliveries for this agent today
            num_assignments = min(len(pending_deliveries), DAILY_ASSIGNMENT)
            assigned_deliveries = pending_deliveries.head(num_assignments)

            # Update workload
            agent_workload[agent_name][date] += num_assignments
            total_daily_assigned += num_assignments

            # Store assignment in the corresponding date column
            deliveries_df.loc[deliveries_df["MID"].isin(assigned_deliveries["MID"]), date_col] = agent_name

            # **Add assigned AWBs to prevent future reassignment**
            assigned_awbs.update(assigned_deliveries["awb_no"])
    
    return deliveries_df

def convert_df_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name="Assigned Deliveries")
    return output.getvalue()

st.title("📦 Delivery Assign")

uploaded_deliveries = st.file_uploader("Upload Deliveries File (Excel)", type=["xlsx"])
uploaded_agents = st.file_uploader("Upload Agents File (Excel)", type=["xlsx"])

if uploaded_deliveries and uploaded_agents:
    deliveries_df = pd.read_excel(uploaded_deliveries)
    agents_df = pd.read_excel(uploaded_agents)
    
    assigned_df = assign_deliveries(deliveries_df, agents_df)
    
    st.success("Deliveries Assigned Successfully!")
    st.dataframe(assigned_df.head(10))
    
    excel_data = convert_df_to_excel(assigned_df)
    st.download_button("📥 Download Assigned Deliveries", data=excel_data, file_name="assigned_deliveries.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")