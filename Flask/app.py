import streamlit as st
import requests
import pandas as pd

st.title("📍 Address Filtering & Clustering System")

# File Upload
uploaded_file = st.file_uploader("📂 Upload Excel File", type=['xlsx'])
if uploaded_file:
    df = pd.read_excel(uploaded_file)

    for _, row in df.iterrows():
        payload = {"address": row["Address"], "pincode": str(row["Pincode"])}
        requests.post("http://127.0.0.1:5001/store_address", json=payload)


    st.success("✅ Data Uploaded & Stored in Database!")

# User Input
query = st.text_input("🔍 Search Address:")
pincode_input = st.text_input("📍 Enter Pincode:")

if st.button("🔎 Search"):
    response = requests.get(f"http://127.0.0.1:5000/search_address?query={query}&pincode={pincode_input}")
    
    if response.status_code == 200:
        results = response.json()
        if results:
            st.dataframe(pd.DataFrame(results))
        else:
            st.warning("❌ No Matching Address Found.")
