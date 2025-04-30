# 🔄 Enhanced Streamlit App with Accurate Cluster Naming via Fuzzy/TF-IDF Matching

import streamlit as st
import pandas as pd
import numpy as np
import requests
import time
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from fuzzywuzzy import fuzz
from sklearn.cluster import KMeans
from io import BytesIO
from datetime import datetime, timedelta

# ------------------ CONFIG ------------------
st.set_page_config(page_title="Smart Delivery Assignment System", page_icon="namalogo.webp", layout="wide")
GEOAPIFY_API_KEY = "1dce308a2d0d41c4a4ed07709b5a0552"
DEFAULT_ROLL_WEIGHT = 46
ST_WEIGHT_LIMIT_KG = 3.0

# ------------------ HEADER ------------------
col1, col2 = st.columns([0.09, 0.9])
with col1:
    st.image("namalogo.webp", width=70)
with col2:
    st.markdown("<h1 style='font-size: 32px; color: #0047AB;'>Namaskar Distribution Solutions Pvt Ltd</h1>", unsafe_allow_html=True)

# ------------------ TEXT CLEANING ------------------
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

# ------------------ GEOCODING ------------------
def geocode_address(full_address):
    try:
        url = f"https://api.geoapify.com/v1/geocode/search?text={full_address}&apiKey={GEOAPIFY_API_KEY}"
        res = requests.get(url).json()
        coords = res['features'][0]['geometry']['coordinates']
        return coords[1], coords[0]
    except:
        return None, None

# ------------------ CLUSTER MATCHING ------------------
def match_cluster(address, pincode, cluster_dict, vectorizer, tfidf_matrix, cluster_names):
    address = preprocess_address(address)
    address_tokens = set(address.split())
    best_match, best_score = None, 0
    
    filtered = {k: v for k, v in cluster_dict.items() if str(v['pincode']) == str(pincode)}
    if not filtered:
        return "Unmatched"

    address_vec = vectorizer.transform([address])
    scores = cosine_similarity(address_vec, tfidf_matrix)[0]
    tfidf_best_idx = scores.argmax()
    tfidf_score = scores[tfidf_best_idx]
    tfidf_match = cluster_names[tfidf_best_idx] if tfidf_score > 0.35 else None

    for cluster, data in filtered.items():
        for area in data['areas']:
            area_clean = preprocess_address(area)
            if set(area_clean.split()) & address_tokens:
                return cluster
            score = fuzz.token_set_ratio(address, area_clean)
            if score > best_score:
                best_score = score
                best_match = cluster

    if best_score > 60:
        return best_match
    elif tfidf_match:
        return tfidf_match
    else:
        return "Unmatched"

# ------------------ AGENT ASSIGNMENT ------------------
def assign_agents(df, agent_count, max_wt=25):
    df_sorted = df.copy()
    df_sorted['Agent'], df_sorted['Day'], df_sorted['Remark'] = None, None, None
    normal_day, vehicle_day = 1, 1
    agent_wt = {i+1: 0 for i in range(agent_count)}

    for cluster in df_sorted['Cluster'].unique():
        cluster_df = df_sorted[df_sorted['Cluster'] == cluster]
        for idx, row in cluster_df.iterrows():
            wt = row['Weight']
            if wt >= ST_WEIGHT_LIMIT_KG:
                df_sorted.at[idx, 'Remark'] = 'Vehicle'
                df_sorted.at[idx, 'Agent'] = 'Vehicle Required'
                df_sorted.at[idx, 'Day'] = f"V{vehicle_day}"
            else:
                for agent in agent_wt:
                    if agent_wt[agent] + wt <= max_wt:
                        agent_wt[agent] += wt
                        df_sorted.at[idx, 'Agent'] = f"Agent {agent}"
                        df_sorted.at[idx, 'Remark'] = 'Normal'
                        df_sorted.at[idx, 'Day'] = f"N{normal_day}"
                        break
                else:
                    normal_day += 1
                    agent_wt = {i+1: 0 for i in range(agent_count)}
                    agent_wt[1] = wt
                    df_sorted.at[idx, 'Agent'] = 'Agent 1'
                    df_sorted.at[idx, 'Remark'] = 'Normal'
                    df_sorted.at[idx, 'Day'] = f"N{normal_day}"
    return df_sorted

# ------------------ STREAMLIT UI ------------------
st.title("📦 Clustered Agent Assignment with Area Accuracy")

col1, col2 = st.columns(2)
with col1:
    delivery_file = st.file_uploader("📂 Upload Delivery Data", type=["csv", "xlsx"], key='data')
with col2:
    cluster_file = st.file_uploader("📂 Upload Cluster Master File", type=["csv", "xlsx"], key='master')

if delivery_file and cluster_file:
    df = pd.read_excel(delivery_file) if delivery_file.name.endswith("xlsx") else pd.read_csv(delivery_file)
    master_df = pd.read_excel(cluster_file) if cluster_file.name.endswith("xlsx") else pd.read_csv(cluster_file)
    
    cluster_dict = {}
    for _, row in master_df.iterrows():
        name = str(row['Keyword']).split(":")[0].strip() if pd.notna(row['Keyword']) else "Unknown"
        pincode = str(row['pincode']).strip()
        sub_areas = str(row['Keyword']).split("[")[-1].replace("]", "").replace(";", ",").split(",") if pd.notna(row['Keyword']) else []
        cluster_dict[name] = {"areas": [preprocess_address(a) for a in sub_areas], "pincode": pincode}

    df['Address'] = df['Address'].astype(str).apply(preprocess_address)
    df['City'] = df['City'].astype(str).str.lower()
    df['Pincode'] = df['Pincode'].astype(str)
    df['Weight'] = df.get('Weight', df['Roll Qty'] * DEFAULT_ROLL_WEIGHT / 1000)

    latitudes, longitudes = [], []
    for _, row in df.iterrows():
        full = f"{row['Address']}, {row['City']}, {row['Pincode']}, India"
        lat, lon = geocode_address(full)
        latitudes.append(lat)
        longitudes.append(lon)
        time.sleep(0.1)

    df['Latitude'] = latitudes
    df['Longitude'] = longitudes
    df = df.dropna(subset=['Latitude', 'Longitude'])

    cluster_names = list(cluster_dict.keys())
    corpus = [" ".join(v['areas']) for v in cluster_dict.values()]
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(corpus)

    df['Cluster'] = df.apply(lambda row: match_cluster(row['Address'], row['Pincode'], cluster_dict, vectorizer, tfidf_matrix, cluster_names), axis=1)
    df = assign_agents(df, agent_count=st.number_input("Agents", 1, 50, 5))

    st.success("✅ Assignment Completed with Accurate Clusters!")
    st.dataframe(df)

    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Assigned Deliveries', index=False)
    output.seek(0)

    st.download_button("📥 Download Results", output, file_name="Final_Assigned_Deliveries.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ------------------ FOOTER ------------------
st.markdown("""
---
<div style='text-align: center; padding: 10px; font-size: 14px;'>
<b>Namaskar Distribution Solutions Pvt Ltd</b> <br>
Created by <b>Siddhi Patade</b> | © 2025 Address Assignment System
</div>
""", unsafe_allow_html=True)
