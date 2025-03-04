import streamlit as st
import pandas as pd
import re
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

# Address Search using TF-IDF Similarity
def search_addresses(df, query, pincodes):
    """Searches addresses using TF-IDF similarity and filters by pin codes."""
    query = query.strip().lower()
    
    # Prepare address corpus
    addresses = df['Address'].tolist()
    addresses.append(query)  # Append query as last item for vectorization

    # TF-IDF Vectorization
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(addresses)

    # Compute Cosine Similarity
    similarity_scores = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])[0]  # Compare query with all addresses

    # Sort results by highest similarity
    sorted_indices = similarity_scores.argsort()[::-1]  # Descending order
    relevant_indices = [idx for idx in sorted_indices if similarity_scores[idx] > 0]  # Keep only relevant matches

    # Filter by Pincode
    if pincodes:
        relevant_indices = [idx for idx in relevant_indices if str(df.iloc[idx]['Pincode']) in pincodes]

    # Return only relevant addresses (keeping original data format)
    return df.iloc[relevant_indices]

# Streamlit UI
st.title("🔍 Address Filtering System")

# File Upload
uploaded_file = st.file_uploader("📂 Upload Excel File", type=['xlsx'])
if uploaded_file:
    df = load_data(uploaded_file)
    df['Address'] = df['Address'].apply(clean_address)  # Clean addresses before processing

    # User Input
    query = st.text_input("✍️ Enter Keywords (comma-separated):")
    pincode_input = st.text_input("📍 Enter up to 2 Pincodes (comma-separated):")

    if st.button("🔎 Search"):
        pincodes = [p.strip() for p in pincode_input.split(",") if p.strip().isdigit()][:2]  # Allow max 2 pincodes
        result = search_addresses(df, query, pincodes)
        match_count = len(result)

        if match_count > 0:
            st.success(f"✅ {match_count} related addresses found!")
            st.dataframe(result)
            # Download CSV
            csv = result.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Results", csv, "filtered_addresses.csv", "text/csv")
        else:
            st.warning(f"❌ No results found for '{query}' with Pincode(s): {', '.join(pincodes)}.")
