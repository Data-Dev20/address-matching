
import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
from io import BytesIO
from geopy.geocoders import Nominatim
import time
from sklearn.cluster import KMeans
import pydeck as pdk

# --------------------------------------
# Helper Functions
# --------------------------------------

def categorize_branch(branch):
    if branch in ['Trackon West', 'POST', 'DTDC']:
        return 'CD'
    else:
        return 'SD'

def categorize_vehicle(weight):
    ST_WEIGHTS = {"100 GM", "250 GM", "500 GM", "1", "2", "3"}
    if pd.isna(weight):
        return "OT"
    weight_str = str(weight).strip().upper()
    return "ST" if weight_str in ST_WEIGHTS else "OT"

def get_lat_lon(address):
    geolocator = Nominatim(user_agent="delivery_app", timeout=10)
    for _ in range(3):  # Retry 3 times
        try:
            location = geolocator.geocode(address)
            if location:
                return pd.Series([location.latitude, location.longitude])
            break
        except Exception as e:
            print(f"Retrying for address {address} due to error: {e}")
            time.sleep(1)  # Respect rate limits
    return pd.Series([None, None])

def cluster_addresses(df, n_clusters=10):
    coords = df[['latitude', 'longitude']].dropna()
    if coords.empty:
        return df  # No coordinates to cluster
    kmeans = KMeans(n_clusters=min(n_clusters, len(coords)), random_state=42)
    df.loc[coords.index, 'cluster'] = kmeans.fit_predict(coords)
    return df

def assign_deliveries(deliveries_df, agents_df):
    st.write("📌 Deliveries Columns:", deliveries_df.columns.tolist())
    st.write("📌 Agents Columns:", agents_df.columns.tolist())

    deliveries_df.rename(columns={"Pincode": "pincode", "Cluster": "cluster_name", "AWB NO": "awb_no", "Remark": "remark", "Branch Name": "branch", "Weight Kg/Gm": "weight"}, inplace=True, errors="ignore")
    agents_df.rename(columns={"Agent_ID": "agent_id", "Agent": "agent_name"}, inplace=True, errors="ignore")

    deliveries_df["remark"] = deliveries_df["branch"].apply(categorize_branch)
    deliveries_df["vehicle"] = deliveries_df["weight"].apply(categorize_vehicle)

    st.info("🔄 Geocoding addresses...")
    deliveries_df[['latitude', 'longitude']] = deliveries_df['Address'].apply(get_lat_lon)
    time.sleep(1)

    st.info("🔄 Clustering addresses by proximity...")
    deliveries_df = cluster_addresses(deliveries_df, n_clusters=10)

    if "pincode" in agents_df.columns:
        agents_df["pincode"] = agents_df["pincode"].astype(str)
        agents_df["pincode_list"] = agents_df["pincode"].apply(lambda x: [p.strip() for p in x.split(",")] if pd.notna(x) else [])
    else:
        st.error("⚠️ 'pincode' column not found in agent file!")
        return deliveries_df

    agent_pincode_mapping = agents_df.set_index("agent_name")["pincode_list"].to_dict()

    start_date = datetime(2025, 4, 8)
    date_range = [start_date + timedelta(days=i) for i in range(10)]
    date_columns = [date.strftime("%d-%m-%Y") for date in date_range]

    for date_col in date_columns:
        deliveries_df[date_col] = ""

    DAILY_ASSIGNMENT = 55
    TOTAL_DAILY_LIMIT = 18 * DAILY_ASSIGNMENT

    agent_workload = {agent: {date: 0 for date in date_range} for agent in agents_df["agent_name"].unique()}
    assigned_awbs = set()

    for date in date_range:
        date_col = date.strftime("%d-%m-%Y")
        total_daily_assigned = 0

        for agent_name, pincodes in agent_pincode_mapping.items():
            if total_daily_assigned >= TOTAL_DAILY_LIMIT:
                break

            for pincode in pincodes:
                if total_daily_assigned >= TOTAL_DAILY_LIMIT:
                    break

                pending_deliveries = deliveries_df[
                    (deliveries_df["pincode"].astype(str) == pincode) & 
                    (deliveries_df[date_col] == "") & 
                    (~deliveries_df["awb_no"].isin(assigned_awbs)) & 
                    (deliveries_df["remark"] != "CD")
                ]

                if pending_deliveries.empty:
                    continue

                num_assignments = min(len(pending_deliveries), DAILY_ASSIGNMENT)
                assigned_deliveries = pending_deliveries.head(num_assignments)

                agent_workload[agent_name][date] += num_assignments
                total_daily_assigned += num_assignments

                deliveries_df.loc[deliveries_df["awb_no"].isin(assigned_deliveries["awb_no"]), date_col] = agent_name
                assigned_awbs.update(assigned_deliveries["awb_no"])

    return deliveries_df

def convert_df_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name="Assigned Deliveries")
    return output.getvalue()

# --------------------------------------
# Streamlit UI
# --------------------------------------

st.title("📦 Delivery Assignment & Route Optimization")

uploaded_deliveries = st.file_uploader("Upload Deliveries File (Excel)", type=["xlsx"])
uploaded_agents = st.file_uploader("Upload Agents File (Excel)", type=["xlsx"])

if uploaded_deliveries and uploaded_agents:
    deliveries_df = pd.read_excel(uploaded_deliveries)
    agents_df = pd.read_excel(uploaded_agents)

    assigned_df = assign_deliveries(deliveries_df, agents_df)

    if "pincode" in deliveries_df.columns:
        st.success("✅ Deliveries Assigned Successfully!")
        st.dataframe(assigned_df.head(10))

        excel_data = convert_df_to_excel(assigned_df)
        st.download_button("📅 Download Assigned Deliveries", data=excel_data, file_name="assigned_deliveries.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        if 'cluster' in assigned_df.columns:
            st.subheader("📍 Clustered Delivery Locations Map")
            st.pydeck_chart(pdk.Deck(
                map_style="mapbox://styles/mapbox/streets-v12",
                initial_view_state=pdk.ViewState(
                    latitude=assigned_df['latitude'].mean(),
                    longitude=assigned_df['longitude'].mean(),
                    zoom=10,
                    pitch=0,
                ),
                layers=[
                    pdk.Layer(
                        'ScatterplotLayer',
                        data=assigned_df.dropna(subset=["latitude", "longitude"]),
                        get_position='[longitude, latitude]',
                        get_color='[cluster * 20, 100, 150, 160]',
                        get_radius=100,
                    ),
                ],
            ))
