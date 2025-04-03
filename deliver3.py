import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO

def assign_deliveries(deliveries_df, agents_df):
    try:
        # Debug: Print column names
        st.write("\ud83d\udccc Deliveries Columns:", deliveries_df.columns.tolist())
        st.write("\ud83d\udccc Agents Columns:", agents_df.columns.tolist())

        # Standardize column names (case-insensitive matching)
        deliveries_df.columns = deliveries_df.columns.str.lower()
        agents_df.columns = agents_df.columns.str.lower()

        required_delivery_cols = {"pincode", "awb no", "remark", "vehicle"}
        required_agent_cols = {"agent_id", "agent", "pincode"}

        if not required_delivery_cols.issubset(deliveries_df.columns):
            st.error(f"⚠️ Missing columns in Deliveries File: {required_delivery_cols - set(deliveries_df.columns)}")
            return None

        if not required_agent_cols.issubset(agents_df.columns):
            st.error(f"⚠️ Missing columns in Agents File: {required_agent_cols - set(agents_df.columns)}")
            return None

        # Extract pincodes from the agent file (assuming multiple pincodes in a single column)
        agents_df["pincode"] = agents_df["pincode"].astype(str)
        agents_df["pincode_list"] = agents_df["pincode"].apply(lambda x: [p.strip() for p in x.split(",")] if pd.notna(x) else [])
        
        # Create a mapping {agent_name: [pincode1, pincode2, ...]}
        agent_pincode_mapping = agents_df.set_index("agent")["pincode_list"].to_dict()

        # Generate a 10-day delivery schedule
        start_date = datetime(2025, 4, 2)
        date_range = [start_date + timedelta(days=i) for i in range(10)]
        date_columns = [date.strftime("%d-%m-%Y") for date in date_range]

        # Add empty date columns
        for date_col in date_columns:
            deliveries_df[date_col] = ""

        # Daily limits
        DAILY_ASSIGNMENT = 55
        TOTAL_DAILY_LIMIT = 18 * DAILY_ASSIGNMENT

        # Track workload
        agent_workload = {agent: {date: 0 for date in date_range} for agent in agents_df["agent"].unique()}
        assigned_awbs = set()

        # Assign deliveries
        for date in date_range:
            date_col = date.strftime("%d-%m-%Y")
            total_daily_assigned = 0

            for agent_name, pincodes in agent_pincode_mapping.items():
                if total_daily_assigned >= TOTAL_DAILY_LIMIT:
                    break

                for pincode in pincodes:
                    if total_daily_assigned >= TOTAL_DAILY_LIMIT:
                        break

                    # Find deliveries for this pincode that are not yet assigned and have vehicle type 'ST'
                    pending_deliveries = deliveries_df[
                        (deliveries_df["pincode"].astype(str) == pincode) & 
                        (deliveries_df[date_col] == "") & 
                        (~deliveries_df["awb no"].isin(assigned_awbs)) & 
                        (deliveries_df["remark"] != "CD") & 
                        (deliveries_df["vehicle"] == "ST")  # Only assign if vehicle type is 'ST'
                    ]

                    if pending_deliveries.empty:
                        continue

                    num_assignments = min(len(pending_deliveries), DAILY_ASSIGNMENT)
                    assigned_deliveries = pending_deliveries.head(num_assignments)

                    # Update workload & total assignments
                    agent_workload[agent_name][date] += num_assignments
                    total_daily_assigned += num_assignments

                    # Assign the deliveries to the agent
                    deliveries_df.loc[deliveries_df["awb no"].isin(assigned_deliveries["awb no"]), date_col] = agent_name
                    assigned_awbs.update(assigned_deliveries["awb no"])

        return deliveries_df
    except Exception as e:
        st.error(f"❌ Error occurred: {e}")
        return None

def convert_df_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Assigned Deliveries")
    return output.getvalue()

# Streamlit UI
st.title("\ud83d\udce6 Delivery Assignment System")

uploaded_deliveries = st.file_uploader("Upload Deliveries File (Excel)", type=["xlsx"])
uploaded_agents = st.file_uploader("Upload Agents File (Excel)", type=["xlsx"])

if uploaded_deliveries and uploaded_agents:
    deliveries_df = pd.read_excel(uploaded_deliveries, engine='openpyxl')
    agents_df = pd.read_excel(uploaded_agents, engine='openpyxl')
    
    assigned_df = assign_deliveries(deliveries_df, agents_df)

    if assigned_df is not None:
        st.success("✅ Deliveries Assigned Successfully!")
        st.dataframe(assigned_df.head(10))

        excel_data = convert_df_to_excel(assigned_df)
        st.download_button("\ud83d\udcc5 Download Assigned Deliveries", data=excel_data, file_name="assigned_deliveries.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")