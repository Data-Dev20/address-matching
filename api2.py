# 📦 Required Libraries
import streamlit as st
import pandas as pd
import requests
import io
from sklearn.cluster import KMeans
import time

# 🔑 Set your Geoapify API Key here
GEOAPIFY_API_KEY = "6237e6cc370342cb96d6ae8b44539025"


# 📍 Convert address+pincode to coordinates using Geoapify
def geocode_address(address):
    try:
        url = f"https://api.geoapify.com/v1/geocode/search?text={address}&apiKey={GEOAPIFY_API_KEY}"
        res = requests.get(url).json()
        coords = res["features"][0]["geometry"]["coordinates"]
        return coords[1], coords[0]  # lat, lon
    except:
        return None, None

# 📊 Streamlit App
st.title("📦 Courier Clustering & Agent Assignment (Area Wise)")
st.markdown("Upload your file and cluster delivery addresses by area, then assign them to agents.")

# 1. Upload file
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.success("File uploaded successfully!")

    # Clean addresses
    df['Address'] = df['Address'].astype(str).str.strip().str.lower()
    df['Pincode'] = df['Pincode'].astype(str).str.strip()

    # Combine Address + Pincode
    df['Full_Address'] = df['Address'] + ", " + df['Pincode']

    st.markdown("### 🧮 Set Clustering Rules")

    # Number of clusters input
    cluster_count = st.number_input("Number of Clusters (Areas)", value=5, min_value=1)

    # 2. Geocode unique addresses
    st.markdown("### 🌍 Geocoding Unique Addresses...")
    unique_addresses = df['Full_Address'].unique()
    address_coords = {}
    with st.spinner("Geocoding addresses..."):
        for address in unique_addresses:
            lat, lon = geocode_address(address)
            address_coords[address] = (lat, lon)
            time.sleep(0.2)  # avoid rate limits

    # Map coordinates back to dataframe
    df['Latitude'] = df['Full_Address'].map(lambda x: address_coords[x][0])
    df['Longitude'] = df['Full_Address'].map(lambda x: address_coords[x][1])

    # Drop entries where geocoding failed
    df = df.dropna(subset=['Latitude', 'Longitude'])

    # 3. Clustering based on Latitude and Longitude
    st.markdown("### 📌 Clustering Locations...")
    kmeans = KMeans(n_clusters=cluster_count, random_state=42, n_init='auto')
    df['Cluster'] = kmeans.fit_predict(df[['Latitude', 'Longitude']])

    # 4. Assign entire cluster to agents
    st.markdown("### 👥 Assigning Clusters to Agents...")
    clusters = sorted(df['Cluster'].unique())
    agent_assignments = {cluster: f'Agent {i+1}' for i, cluster in enumerate(clusters)}

    df['Agent'] = df['Cluster'].map(agent_assignments)

    # 5. Final result
    result_df = df[['Cnote No', 'Address', 'Pincode', 'R_City', 'Roll Count', 'Latitude', 'Longitude', 'Cluster', 'Agent']]
    st.dataframe(result_df)

    # 6. Download option
    st.markdown("### 📥 Download Agent Assignments")
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        result_df.to_excel(writer, index=False)
    output.seek(0)

    st.download_button(
        label="Download Excel",
        data=output,
        file_name="Agent_Cluster_Assignments.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
