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

# Updated assign_agents function
def assign_agents(df, agent_count, rolls_per_agent=200):
    # Make a copy to avoid modifying the original
    df_sorted = df.copy()
    
    # Calculate weight if not present
    if 'Weight' not in df_sorted.columns:
        df_sorted['Weight'] = df_sorted['Roll Qty'] * 45 / 1000
    
    # Initialize assignment columns
    df_sorted['Agent'] = None
    df_sorted['Day'] = None
    df_sorted['Remark'] = None
    
    # Process cluster by cluster
    for cluster_id in sorted(df_sorted['Cluster'].unique()):
        cluster_df = df_sorted[df_sorted['Cluster'] == cluster_id].copy()
        
        # Sort by latitude and longitude within each cluster (for nearest address)
        cluster_df = cluster_df.sort_values(['Latitude', 'Longitude'])
        
        # Initialize tracking variables
        current_day = 1
        agents_data = {i+1: {'current_weight': 0, 'vehicle_day': None} for i in range(agent_count)}
        available_agents = list(range(1, agent_count + 1))
        
        # Process each delivery in the cluster
        for idx, row in cluster_df.iterrows():
            weight = row['Weight']
            roll_qty = row['Roll Qty']
            
            # Determine if this delivery needs a vehicle
            needs_vehicle = weight >= 3.000
            
            # Find the best agent for this delivery
            assigned_agent = None
            
            # First priority: agents who already have a vehicle for the current day
            if needs_vehicle:
                for agent_id in available_agents:
                    if agents_data[agent_id]['vehicle_day'] == current_day:
                        if agents_data[agent_id]['current_weight'] + weight <= rolls_per_agent:
                            assigned_agent = agent_id
                            break
            
            # Second priority: any available agent
            if assigned_agent is None:
                for agent_id in available_agents:
                    if agents_data[agent_id]['current_weight'] + weight <= rolls_per_agent:
                        assigned_agent = agent_id
                        break
            
            # If no agent available, move to next day
            if assigned_agent is None:
                current_day += 1
                # Reset all agents' data for the new day
                for agent_id in range(1, agent_count + 1):
                    agents_data[agent_id]['current_weight'] = 0
                    if agents_data[agent_id]['vehicle_day'] is not None and agents_data[agent_id]['vehicle_day'] < current_day:
                        agents_data[agent_id]['vehicle_day'] = None
                
                # Try again with the first agent
                assigned_agent = 1
            
            # Update the assignment
            df_sorted.at[idx, 'Agent'] = f'Agent {assigned_agent}'
            df_sorted.at[idx, 'Day'] = current_day
            
            # Update agent's data
            agents_data[assigned_agent]['current_weight'] += weight
            
            # Update vehicle availability
            if needs_vehicle:
                df_sorted.at[idx, 'Remark'] = 'Vehicle'
                agents_data[assigned_agent]['vehicle_day'] = current_day
                # Vehicle is available for the next day too
                if agents_data[assigned_agent]['vehicle_day'] is None or agents_data[assigned_agent]['vehicle_day'] < current_day + 1:
                    agents_data[assigned_agent]['vehicle_day'] = current_day + 1
            else:
                df_sorted.at[idx, 'Remark'] = 'Normal'
            
            # Update available agents list (who can take more packages today)
            available_agents = [a for a in range(1, agent_count + 1) 
                               if agents_data[a]['current_weight'] < rolls_per_agent]
            
            # If no agents available, move to next day
            if not available_agents:
                current_day += 1
                # Reset all agents' data for the new day
                for agent_id in range(1, agent_count + 1):
                    agents_data[agent_id]['current_weight'] = 0
                    if agents_data[agent_id]['vehicle_day'] is not None and agents_data[agent_id]['vehicle_day'] < current_day:
                        agents_data[agent_id]['vehicle_day'] = None
                available_agents = list(range(1, agent_count + 1))
    
    return df_sorted

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
        final_df = assign_agents(df, agent_count)

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