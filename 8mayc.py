import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import folium_static

# === CONFIG ===
GEOAPIFY_API_KEY = "6237e6cc370342cb96d6ae8b44539025"  # Replace with your key

st.set_page_config(page_title="MID Route Planner", layout="wide")
st.title("📍 MID-Based Route Planner")
st.markdown("Upload a Excel file with `MID`, `Address`, and `Pincode` to plan delivery routes using Geoapify.")

# === UPLOAD FILE ===
uploaded_file = st.file_uploader("Upload Execel File", type=["xlsx"])

if uploaded_file:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file, encoding='utf-8', errors='replace')
        elif uploaded_file.name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file)
        else:
            st.error("Unsupported file format.")
            st.stop()
    except Exception as e:
        st.error(f"Error reading file: {e}")
        st.stop()

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    expected_cols = {"MID", "Address", "Pincode"}
    if not expected_cols.issubset(df.columns):
        st.error(f"Execl must contain these columns: {expected_cols}")
    else:
        # Build full address for geocoding
        df["Full_Address"] = df["Address"].astype(str) + ", " + df["Pincode"].astype(str)

        # === Geocode Addresses ===
        def geocode_address(address):
            url = "https://api.geoapify.com/v1/geocode/search"
            params = {
                "text": address,
                "apiKey": GEOAPIFY_API_KEY,
                "format": "json"
            }
            try:
                resp = requests.get(url, params=params)
                data = resp.json()
                coords = data["features"][0]["geometry"]["coordinates"]
                return coords[1], coords[0]  # (lat, lon)
            except:
                return None, None

        with st.spinner("Geocoding addresses..."):
            df[["Latitude", "Longitude"]] = df["Full_Address"].apply(lambda x: pd.Series(geocode_address(x)))

        st.success("Geocoding completed.")
        st.dataframe(df)

        valid_df = df.dropna(subset=["Latitude", "Longitude"])
        if len(valid_df) < 2:
            st.warning("At least two valid addresses are needed to plan a route.")
        else:
            # === Route Planner ===
            def get_route(df):
                latlons = [f"{row['Latitude']},{row['Longitude']}" for _, row in df.iterrows()]
                waypoints = "|".join(latlons)
                url = "https://api.geoapify.com/v1/routing"
                params = {
                    "waypoints": waypoints,
                    "mode": "drive",
                    "apiKey": GEOAPIFY_API_KEY
                }
                response = requests.get(url, params=params)
                data = response.json()
                if "features" in data:
                    props = data["features"][0]["properties"]
                    coords = data["features"][0]["geometry"]["coordinates"]
                    return props["distance"], props["time"], coords
                return None, None, None

            distance, time, route_coords = get_route(valid_df)

            # === Show Map ===
            st.subheader("🗺️ Route Map")
            route_map = folium.Map(location=[valid_df.iloc[0]["Latitude"], valid_df.iloc[0]["Longitude"]], zoom_start=12)

            # Add markers
            for idx, row in valid_df.iterrows():
                folium.Marker([row["Latitude"], row["Longitude"]], tooltip=f"MID: {row['MID']}").add_to(route_map)

            # Draw the route
            if route_coords:
                polyline = [(lat, lon) for lon, lat in route_coords]
                folium.PolyLine(polyline, color="blue", weight=4).add_to(route_map)
                st.success(f"🚗 Distance: {distance/1000:.2f} km | ⏱ Time: {time/60:.2f} minutes")

            folium_static(route_map)

            st.download_button(
            label="Export File",
            data=output,
            file_name="data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
