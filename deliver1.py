# 🔄 Unified Streamlit App for Address Clustering, Agent Assignment & Delivery Scheduling
# Combines logic from Final_code.py (90%), a2.py (advanced clustering), and deliver3.py (agent-based delivery scheduling)

import streamlit as st
import pandas as pd
import numpy as np
import requests
import time
from sklearn.cluster import KMeans
from fuzzywuzzy import fuzz
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from io import BytesIO
from datetime import datetime, timedelta

# ------------------ PAGE SETUP ------------------
st.set_page_config(page_title="Smart Delivery Assignment System", page_icon="namalogo.webp", layout="wide")
col1, col2 = st.columns([0.09, 0.9])
with col1:
    st.image("namalogo.webp", width=70)
with col2:
    st.markdown("<h1 style='font-size: 32px; color: #0047AB;'>Namaskar Distribution Solutions Pvt Ltd</h1>", unsafe_allow_html=True)

# ------------------ SETTINGS ------------------
GEOAPIFY_API_KEY = "1dce308a2d0d41c4a4ed07709b5a0552"
ST_WEIGHT_LIMIT_KG = 3.0
DEFAULT_ROLL_WEIGHT = 45  # in grams

# ------------------ UTILITY FUNCTIONS ------------------
def preprocess_address(address):
    mapping = {' rd ': ' road ', ' marg ': ' road ', ' ngr ': ' nagar ', ' nr ': ' near ',
               ' opp ': ' opposite ', ' bldg ': ' building ', ' soc ': ' society ', ' apt ': ' apartment ',
               ' mkt ': ' market ', ' ch ': ' church ', ' stn ': ' station ', ' sv ': ' swami vivekananda ',
               ' mg ': ' mahatma gandhi ', ' govt ': ' government ', ' talkies ': ' cinema ', ' flr ': ' floor ',
               ' sec ': ' sector ', ' village ': ' nagar '}
    address = str(address).lower()
    address = ' ' + address + ' '
    for short, full in mapping.items():
        address = address.replace(short, full)
    return ' '.join(address.replace(',', ' ').replace('.', ' ').split())

def geocode_address(full_address):
    try:
        url = f"https://api.geoapify.com/v1/geocode/search?text={full_address}&apiKey={GEOAPIFY_API_KEY}"
        res = requests.get(url).json()
        coords = res['features'][0]['geometry']['coordinates']
        area = res['features'][0]['properties'].get('suburb', res['features'][0]['properties'].get('city', 'Unknown'))
        return coords[1], coords[0], area
    except:
        return None, None, 'Unknown'

# ------------------ CORE LOGIC ------------------
def assign_agents(df, agent_count, rolls_per_agent=200, min_wt=15, max_wt=25):
    df_sorted = df.copy()
    df_sorted['Agent'] = None
    df_sorted['Day'] = None
    df_sorted['Remark'] = None

    vehicle_day = 1
    normal_day = 1
    agent_weights = {i+1: 0 for i in range(agent_count)}

    for cluster in df_sorted['Cluster Name'].unique():
        cluster_df = df_sorted[df_sorted['Cluster Name'] == cluster].copy()
        for idx, row in cluster_df.iterrows():
            weight = row['Weight']
            if weight >= ST_WEIGHT_LIMIT_KG:
                df_sorted.at[idx, 'Remark'] = 'Vehicle'
                df_sorted.at[idx, 'Agent'] = 'Vehicle Required'
                df_sorted.at[idx, 'Day'] = f"V{vehicle_day}"
            else:
                assigned = False
                for agent in agent_weights:
                    if agent_weights[agent] + weight <= max_wt:
                        agent_weights[agent] += weight
                        df_sorted.at[idx, 'Agent'] = f"Agent {agent}"
                        df_sorted.at[idx, 'Remark'] = 'Normal'
                        df_sorted.at[idx, 'Day'] = f"N{normal_day}"
                        assigned = True
                        break
                if not assigned:
                    normal_day += 1
                    agent_weights = {i+1: 0 for i in range(agent_count)}
                    agent_weights[1] = weight
                    df_sorted.at[idx, 'Agent'] = 'Agent 1'
                    df_sorted.at[idx, 'Remark'] = 'Normal'
                    df_sorted.at[idx, 'Day'] = f"N{normal_day}"
    return df_sorted

# ------------------ STREAMLIT APP ------------------
st.title("📦 Smart Address-Based Agent Assignment")

uploaded_file = st.file_uploader("Upload Delivery File (Excel/CSV)", type=["xlsx", "csv"])

if uploaded_file:
    agent_count = st.number_input("Number of Agents", min_value=1, value=5)
    radius_km = st.slider("Clustering Radius (km)", 1, 15, 5)

    if st.button("Start Processing"):
        df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith("xlsx") else pd.read_csv(uploaded_file)
        df['Address'] = df['Address'].astype(str).apply(preprocess_address)
        df['City'] = df['City'].astype(str).str.lower()
        df['Pincode'] = df['Pincode'].astype(str)

        if 'Weight' not in df.columns:
            df['Weight'] = df['Roll Qty'] * DEFAULT_ROLL_WEIGHT / 1000

        latitudes, longitudes, areas = [], [], []
        for _, row in df.iterrows():
            full_address = f"{row['Address']}, {row['City']}, {row['Pincode']}, India"
            lat, lon, area = geocode_address(full_address)
            latitudes.append(lat)
            longitudes.append(lon)
            areas.append(area)
            time.sleep(0.1)

        df['Latitude'] = latitudes
        df['Longitude'] = longitudes
        df['Area'] = areas
        df = df.dropna(subset=['Latitude', 'Longitude'])

        cluster_count = max(1, int(len(df) / (radius_km * 10)))
        kmeans = KMeans(n_clusters=cluster_count, random_state=42, n_init=10)
        df['Cluster'] = kmeans.fit_predict(df[['Latitude', 'Longitude']])
        df['Cluster Name'] = df['Area'].fillna(df['City']) + ' Area'

        final_df = assign_agents(df, agent_count)

        st.success("✅ Assignment Completed!")
        st.dataframe(final_df)

        # Download
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            final_df.to_excel(writer, sheet_name='Assigned Deliveries', index=False)
        output.seek(0)

        st.download_button(
            label="📄 Download Assigned Deliveries",
            data=output,
            file_name="Smart_Assigned_Deliveries.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# Footer
st.markdown("""
---
<div style='text-align: center; padding: 10px; font-size: 14px;'>
<b>Namaskar Distribution Solutions Pvt Ltd</b> <br>
Created by <b>Siddhi Patade</b> | © 2025 Unified Assignment System
</div>
""", unsafe_allow_html=True)