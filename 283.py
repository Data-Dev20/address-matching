import streamlit as st
import pandas as pd
import numpy as np
import requests
import time
from sklearn.cluster import KMeans
import plotly.express as px
from io import BytesIO

# Set page configuration
st.set_page_config(page_title="Courier Clustering & Assignment", layout="wide")

# Your Geoapify API Key
GEOAPIFY_API_KEY = "1dce308a2d0d41c4a4ed07709b5a0552"

# Preprocessing function to clean and expand address shortcuts
def preprocess_address(address):
    mapping = {
        ' rd ': ' road ',
        ' marg ': ' road ',
        ' ngr ': ' nagar ',
        ' nr ': ' near ',
        ' opp ': ' opposite ',
        ' bldg ': ' building ',
        ' soc ': ' society ',
        ' apt ': ' apartment '
    }
    address = str(address).lower()
    address = ' ' + address + ' '
    for short, full in mapping.items():
        address = address.replace(short, full)
    address = address.replace(',', ' ').replace('.', ' ')
    address = ' '.join(address.split())
    return address

# Geocode function
def geocode_address(full_address):
    try:
        url = f"https://api.geoapify.com/v1/geocode/search?text={full_address}&apiKey={GEOAPIFY_API_KEY}"
        res = requests.get(url).json()
        coords = res['features'][0]['geometry']['coordinates']
        return coords[1], coords[0]
    except:
        return None, None

# Assign agents day-wise

def assign_agents(df, agent_count, rolls_per_agent=200):
    assignments = []
    agent_id = 1
    day = 1
    current_total_weight = 0
    vehicle_available_until = None
    
    for idx, row in df.iterrows():
        qty = row['Roll Qty']
        weight = row['Weight']
        
        # Check if we need to move to next agent/day
        if current_total_weight + weight > rolls_per_agent:
            # Move to next agent
            agent_id += 1
            
            # If we've used all agents for the day, reset to agent 1 and increment day
            if agent_id > agent_count:
                agent_id = 1
                day += 1
                vehicle_available_until = None
            
            # Reset the weight for the new agent
            current_total_weight = 0
        
        # Handle vehicle logic
        if weight >= 3.000:
            remark = 'Vehicle'
            vehicle_available_until = day + 1
        else:
            remark = 'Normal'
        
        # Add weight to current agent's total
        current_total_weight += weight
        
        # Append assignment details
        assignments.append({
            'Agent': f'Agent {agent_id}',
            'Day': day,
            'Remark': remark
        })
    
    # Create assignment dataframe and combine with original
    assignment_df = pd.DataFrame(assignments)
    return pd.concat([df.reset_index(drop=True), assignment_df], axis=1)

# Streamlit App
st.title("📦 Courier Address Clustering and Agent Assignment")

uploaded_file = st.file_uploader("Upload your Excel/CSV file", type=["xlsx", "csv"])

if uploaded_file:
    agent_count = st.number_input("Enter number of available agents", min_value=1, value=5)

    if st.button("Start Processing"):
        ext = uploaded_file.name.split(".")[-1].lower()
        if ext == "csv":
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.success("File uploaded successfully!")

        st.subheader("🧹 Preprocessing Addresses")
        df['Address'] = df['Address'].astype(str).apply(preprocess_address)
        df['City'] = df['City'].astype(str).str.lower()
        df['Pincode'] = df['Pincode'].astype(str)

        if 'Weight' not in df.columns:
            df['Weight'] = df['Roll Qty'] * 45 / 1000
        else:
            df['Weight'] = pd.to_numeric(df['Weight'], errors='coerce').fillna(0)

        st.subheader("🌍 Geocoding Addresses")
        latitudes, longitudes = [], []
        with st.spinner("Geocoding addresses..."):
            for i, row in df.iterrows():
                full_address = f"{row['Address']}, {row['City']}, {row['Pincode']}, India"
                lat, lon = geocode_address(full_address)
                latitudes.append(lat)
                longitudes.append(lon)
                time.sleep(0.2)

        df['Latitude'] = latitudes
        df['Longitude'] = longitudes
        df = df.dropna(subset=['Latitude', 'Longitude'])

        st.subheader("📌 Clustering Addresses")
        cluster_count = st.number_input("Number of Clusters", min_value=1, value=5)

        kmeans = KMeans(n_clusters=cluster_count, random_state=42, n_init=10)
        df['Cluster'] = kmeans.fit_predict(df[['Latitude', 'Longitude']])

        st.subheader("👥 Assign Deliveries to Agents")
        df_sorted = df.sort_values(['Cluster', 'Latitude', 'Longitude'])
        final_df = assign_agents(df_sorted, agent_count)

        st.success("✅ Assignment Completed!")
        st.dataframe(final_df)

        st.subheader("🗺️ Cluster Map Visualization")
        fig = px.scatter_map(
            final_df,
            lat="Latitude",
            lon="Longitude",
            color="Cluster",
            hover_name="Address",
            hover_data=["Pincode", "Roll Qty", "Weight", "Agent", "Day", "Remark"],
            zoom=10,
            height=600
        )
        fig.update_layout(mapbox_style="open-street-map")
        st.plotly_chart(fig)

        st.subheader("📥 Download Final Assigned File")
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            final_df.to_excel(writer, index=False)
        output.seek(0)

        st.download_button(
            label="Download Assignment Excel",
            data=output,
            file_name="Assigned_Courier_Data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    if st.button("🔄 Refresh App"):
        st.experimental_rerun()

# Footer
st.markdown("---")
st.markdown("<center>Created by Namaskar Distribution Solutions Pvt Ltd | 2025</center>", unsafe_allow_html=True)
