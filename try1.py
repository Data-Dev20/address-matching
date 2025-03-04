import streamlit as st
import pandas as pd
import re
from fuzzywuzzy import fuzz

# Load dataset
@st.cache_data
def load_data(file_path):
    return pd.read_excel(file_path)

# Preprocess Address Column
def clean_address(address):
    """Cleans the address by removing special characters and normalizing spaces."""
    address = str(address).strip().lower()
    address = re.sub(r'[^a-zA-Z0-9\s,]', '', address)  # Keep only alphanumeric & comma
    address = re.sub(r'\s+', ' ', address)  # Normalize spaces

    # Common abbreviations replacement
    common_replacements = {
        'rd': 'road', 'st': 'street', 'ave': 'avenue', 'blvd': 'boulevard',
        'svrd': 'sv road', 'mg rd': 'mg road', 'jdbc': 'junction'
    }
    for key, val in common_replacements.items():
        address = re.sub(fr'\b{key}\b', val, address, flags=re.IGNORECASE)

    return address

# **Search Function (Exact + Fuzzy)**
def search_addresses(df, query):
    """Searches addresses using exact and fuzzy matching based on the query keywords."""
    query = query.strip().lower()
    query_words = [word.strip() for word in query.split(",")]  # Split input into keywords

    # **1. Exact Match Filtering**
    exact_match_condition = df['Address'].apply(lambda addr: 
        all(re.search(fr'\b{re.escape(word)}\b', addr, re.IGNORECASE) for word in query_words)
    )
    exact_matches = df[exact_match_condition]

    # **2. Fuzzy Matching (For Similar Words)**
    fuzzy_matches = []
    for index, address in df['Address'].items():
        for word in query_words:
            if fuzz.partial_ratio(word, address) >= 70:  # Auto-set fuzzy match threshold (no user input needed)
                fuzzy_matches.append(index)
                break  # Stop checking other words once a match is found

    fuzzy_results = df.loc[fuzzy_matches] if fuzzy_matches else pd.DataFrame(columns=df.columns)

    # **3. Combine Results & Remove Duplicates**
    combined_results = pd.concat([exact_matches, fuzzy_results]).drop_duplicates()

    return combined_results  # Only relevant addresses

# **Streamlit UI**
st.title("🔍 Address Filtering System")

# File Upload
uploaded_file = st.file_uploader("📂 Upload Excel File", type=['xlsx'])
if uploaded_file:
    df = load_data(uploaded_file)
    df['Address'] = df['Address'].apply(clean_address)  # Clean addresses before processing

    # User Input
    query = st.text_input("✍️ Enter Keywords (comma-separated):")
    
    if st.button("🔎 Search"):
        result = search_addresses(df, query)
        match_count = len(result)

        if match_count > 0:
            st.success(f"✅ {match_count} related addresses found!")
            st.dataframe(result)
            # Download CSV
            csv = result.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Results", csv, "filtered_addresses.csv", "text/csv")
        else:
            st.warning(f"❌ No results found for '{query}'. Try using different keywords.")
