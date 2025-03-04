import streamlit as st
import pandas as pd
import re
from fuzzywuzzy import process
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

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

# Address Search using Fuzzy Matching + TF-IDF + Cosine Similarity
def search_addresses(df, query, pincodes, fuzzy_threshold=60, cosine_threshold=0.1):
    """Searches addresses using Fuzzy Matching first, then TF-IDF + Cosine Similarity, and filters by pin codes."""
    query = query.strip().lower()

    # **1️⃣ Apply Fuzzy Matching First**
    fuzzy_matches = process.extractBests(query, df['Address'], score_cutoff=fuzzy_threshold)
    fuzzy_indices = [df.index[df['Address'] == match[0]][0] for match in fuzzy_matches]
    
    # If no fuzzy matches found, return empty
    if not fuzzy_indices:
        return pd.DataFrame(columns=df.columns)

    # Filter DataFrame to only fuzzy-matched addresses
    filtered_df = df.loc[fuzzy_indices]

    # **2️⃣ Apply TF-IDF Vectorization**
    addresses = filtered_df['Address'].tolist() + [query]  # Add query as last item
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(addresses)

    # **3️⃣ Compute Cosine Similarity**
    similarity_scores = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])[0]  # Compare query with filtered addresses

    # Keep only matches above the Cosine Similarity threshold
    relevant_indices = [fuzzy_indices[i] for i in range(len(similarity_scores)) if similarity_scores[i] > cosine_threshold]

    # **4️⃣ Apply Pincode Filtering**
    if pincodes:
        relevant_indices = [idx for idx in relevant_indices if str(df.loc[idx, 'Pincode']) in pincodes]

    return df.loc[relevant_indices]

# Streamlit UI
st.title("🔍 Advanced Address Filtering System")

# File Upload
uploaded_file = st.file_uploader("📂 Upload Excel File", type=['xlsx'])
if uploaded_file:
    df = load_data(uploaded_file)
    df['Address'] = df['Address'].apply(clean_address)  # Clean addresses before processing

    # User Input
    query = st.text_input("✍️ Enter Keywords (comma-separated):")
    pincode_input = st.text_input("📍 Enter up to 2 Pincodes (comma-separated):")
    fuzzy_threshold = st.slider("🔧 Fuzzy Match Threshold", 50, 100, 60)
    cosine_threshold = st.slider("🔧 Cosine Similarity Threshold", 0.01, 1.0, 0.1)

    if st.button("🔎 Search"):
        pincodes = [p.strip() for p in pincode_input.split(",") if p.strip().isdigit()][:2]  # Allow max 2 pincodes
        result = search_addresses(df, query, pincodes, fuzzy_threshold, cosine_threshold)
        match_count = len(result)

        if match_count > 0:
            st.success(f"✅ {match_count} related addresses found!")
            st.dataframe(result)
            # Download CSV
            csv = result.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Results", csv, "filtered_addresses.csv", "text/csv")
        else:
            st.warning(f"❌ No results found for '{query}' with Pincode(s): {', '.join(pincodes)}.")
