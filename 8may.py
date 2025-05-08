import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import folium_static

# === CONFIG ===
GEOAPIFY_API_KEY = "6237e6cc370342cb96d6ae8b44539025"  # Replace with your Geoapify key

st.title("📍 MID-Based Route Planner using Geoapify")
st.markdown("Upload a file with `MID`, `Address`, and `Pincode` to geocode and plan delivery routes.")

# === UPLOAD FILE ===
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    required_cols = {"MID", "Address", "Pincode"}
    if not required_cols.issubset(df.columns):
        st.error(f"File must contain columns: {required_cols}")
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
            st.warning("Need at least two valid addresses for routing.")
        else:
            # === Get Route from Geoapify ===
            def get_route(df):
                latlons = [f"{row['Latitude']},{row['Longitude']}" for _, row in df.iterrows()]
                waypoints = "|".join(latlons)

                url = "https://api.geoapify.com/v1/routing"
                params = {
                    "waypoints": waypoints,
                    "mode": "drive",
                    "apiKey": GEOAPIFY_API_KEY
                }
                resp = requests.get(url, params=params)
                data = resp.json()

                if "features" in data:
                    props = data["features"][0]["properties"]
                    coords = data["features"][0]["geometry"]["coordinates"]
                    return props["distance"], props["time"], coords
                return None, None, None

            # Plan Route
            distance, time, route_coords = get_route(valid_df)

            # === Display Map ===
            st.subheader("🗺️ Route Map")
            route_map = folium.Map(location=[valid_df.iloc[0]["Latitude"], valid_df.iloc[0]["Longitude"]], zoom_start=12)

            # Mark points
            for idx, row in valid_df.iterrows():
                folium.Marker([row["Latitude"], row["Longitude"]], tooltip=f"MID: {row['MID']}").add_to(route_map)

            # Draw route
            if route_coords:
                polyline = [(lat, lon) for lon, lat in route_coords]
                folium.PolyLine(polyline, color="blue", weight=4).add_to(route_map)

                st.success(f"🛣️ Total Distance: {distance/1000:.2f} km | Estimated Time: {time/60:.2f} minutes")

            folium_static(route_map)
