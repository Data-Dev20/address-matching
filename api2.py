# Updated Address Assignment System with Enhancements
import streamlit as st
import pandas as pd
import numpy as np
import requests
import time
from sklearn.cluster import KMeans
import plotly.express as px
from io import BytesIO
from datetime import datetime, timedelta

# Configuration
st.set_page_config(page_title="Address Assignment System", page_icon="namalogo.webp", layout="wide")

# Header
col1, col2 = st.columns([0.09, 0.9])
with col1:
    st.image("logo-3.png", width=70)
with col2:
    st.markdown("""
        <h1 style='font-size: 32px; color: #0047AB;'>Namaskar Distribution Solutions Pvt Ltd</h1>
    """, unsafe_allow_html=True)

# Constants
GEOAPIFY_API_KEY = "1dce308a2d0d41c4a4ed07709b5a0552"

# Address Preprocessing
def preprocess_address(address):
    mapping = {
        ' rd ': ' road ', 'no': 'number', ' marg ': ' road ', ' ngr ': ' nagar ', ' nr ': ' near ',
        ' opp ': ' opposite ', ' bldg ': ' building ', ' soc ': ' society ', ' apt ': ' apartment ',
        'mkt': 'market', 'ch': 'church', 'stn': 'station', 'sv': 'swami vivekananda', 'mg': 'mahatma gandhi',
        'govt': 'government', 'talkies': 'cinema', 'flr': 'floor', 'sec': 'sector', 'village': 'nagar'
    }
    address = str(address).lower()
    address = ' ' + address + ' '
    for short, full in mapping.items():
        address = address.replace(short, full)
    return ' '.join(address.replace(',', ' ').replace('.', ' ').split())

# Geocoding
@st.cache_data(show_spinner=False)
def geocode_address(full_address):
    try:
        url = f"https://api.geoapify.com/v1/geocode/search?text={full_address}&apiKey={GEOAPIFY_API_KEY}"
        res = requests.get(url).json()
        features = res.get('features', [])
        if features:
            props = features[0]['properties']
            coords = features[0]['geometry']['coordinates']
            return coords[1], coords[0], props.get('suburb', ''), props.get('city', '')
    except:
        return None, None, '', ''
    return None, None, '', ''

# Agent Assignment Logic

def assign_agents(df, agent_count, rolls_per_agent, min_weight, max_weight, start_date, num_days):
    df_sorted = df.copy()
    df_sorted['Agent'] = None
    df_sorted['Day'] = None
    df_sorted['Remark'] = None
    df_sorted['Date'] = None

    delivery_day = 0
    agent_weights = {i: 0 for i in range(1, agent_count + 1)}

    for cluster in df_sorted['Cluster Name'].unique():
        cluster_df = df_sorted[df_sorted['Cluster Name'] == cluster].copy()
        cluster_df = cluster_df.sort_values(by=['Latitude', 'Longitude'])
        for idx, row in cluster_df.iterrows():
            weight = row['Weight']
            if weight >= 3.0:
                df_sorted.at[idx, 'Remark'] = 'Vehicle'
                df_sorted.at[idx, 'Agent'] = 'Vehicle Required'
                df_sorted.at[idx, 'Day'] = f"V{delivery_day+1}"
                df_sorted.at[idx, 'Date'] = start_date + timedelta(days=delivery_day % num_days)
            else:
                assigned = False
                for agent in agent_weights:
                    if agent_weights[agent] + weight <= max_weight:
                        agent_weights[agent] += weight
                        df_sorted.at[idx, 'Agent'] = f"Agent {agent}"
                        df_sorted.at[idx, 'Remark'] = 'Normal'
                        df_sorted.at[idx, 'Day'] = f"N{delivery_day+1}"
                        df_sorted.at[idx, 'Date'] = start_date + timedelta(days=delivery_day % num_days)
                        assigned = True
                        break
                if not assigned:
                    delivery_day += 1
                    agent_weights = {i: 0 for i in range(1, agent_count + 1)}
                    agent_weights[1] += weight
                    df_sorted.at[idx, 'Agent'] = "Agent 1"
                    df_sorted.at[idx, 'Remark'] = 'Normal'
                    df_sorted.at[idx, 'Day'] = f"N{delivery_day+1}"
                    df_sorted.at[idx, 'Date'] = start_date + timedelta(days=delivery_day % num_days)

    return df_sorted

# Streamlit Interface
st.title("📦 Enhanced Courier Assignment App")

uploaded_file = st.file_uploader("Upload Excel/CSV File", type=["xlsx", "csv"])

if uploaded_file:
    agent_count = st.number_input("Number of Agents", min_value=1, value=5)
    rolls_per_agent = st.number_input("Max Rolls per Agent", min_value=1, value=200)
    min_weight = st.number_input("Min Normal Weight (kg)", min_value=1, value=15)
    max_weight = st.number_input("Max Normal Weight (kg)", min_value=1, value=25)
    radius_km = st.slider("Clustering Radius (km)", 1, 15, 5)
    start_date = st.date_input("Start Delivery Date", value=datetime.today())
    num_days = st.number_input("Number of Delivery Days", min_value=1, value=5)

    if st.button("Start Processing"):
        ext = uploaded_file.name.split(".")[-1]
        df = pd.read_excel(uploaded_file) if ext == 'xlsx' else pd.read_csv(uploaded_file)
        input_shape = df.shape

        df['Address'] = df['Address'].astype(str).apply(preprocess_address)
        df['City'] = df['City'].astype(str).str.lower()
        df['Pincode'] = df['Pincode'].astype(str)

        if 'Weight' not in df.columns:
            df['Weight'] = df['Roll Qty'] * 46 / 1000

        latitudes, longitudes, areas, cities = [], [], [], []
        for _, row in df.iterrows():
            full_address = f"{row['Address']}, {row['City']}, {row['Pincode']}, India"
            lat, lon, area, city = geocode_address(full_address)
            latitudes.append(lat)
            longitudes.append(lon)
            areas.append(area)
            cities.append(city)
            time.sleep(0.1)

        df['Latitude'], df['Longitude'] = latitudes, longitudes
        df['Area'], df['City'] = areas, cities
        df = df.dropna(subset=['Latitude', 'Longitude'])
        output_shape = df.shape

        coords = df[['Latitude', 'Longitude']].dropna()
        cluster_count = max(1, int(len(coords) / (radius_km * 10)))
        kmeans = KMeans(n_clusters=cluster_count, random_state=42, n_init=10)
        df['Cluster'] = kmeans.fit_predict(coords)
        df['Cluster Name'] = df['Area'].fillna(df['City']) + ' Area'

        final_df = assign_agents(df, agent_count, rolls_per_agent, min_weight, max_weight, start_date, num_days)

        st.success("✅ Assignment Completed!")
        st.dataframe(final_df)

        st.write(f"📊 Input Rows: {input_shape[0]} | Output Rows After Geocoding: {output_shape[0]}")

        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            final_df.to_excel(writer, sheet_name='Assigned Data', index=False)

            summary = pd.DataFrame({
                'Metric': ['Input Rows', 'Output Rows', 'Clusters Formed'],
                'Value': [input_shape[0], output_shape[0], cluster_count]
            })
            summary.to_excel(writer, sheet_name='Summary', index=False)

            final_df.groupby(['Cluster Name', 'Remark'])['Weight'].sum().reset_index().to_excel(
                writer, sheet_name='Cluster Summary', index=False)

        output.seek(0)
        st.download_button(
            label="Download Final Excel",
            data=output,
            file_name="Assigned_Courier_Data_Enhanced.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 10px; font-size: 14px;'>
    <b>Namaskar Distribution Solutions Pvt Ltd</b> <br>
    Created by <b>Siddhi Patade</b> | © 2025 Address Assignment System
</div>
""", unsafe_allow_html=True)
