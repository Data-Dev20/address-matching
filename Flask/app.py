from flask import Flask, request, jsonify
import pandas as pd
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from fuzzywuzzy import fuzz
from geopy.distance import geodesic
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

# Global variable for uploaded dataframe
df = None

@app.route("/")
def home():
    return "Flask server is running!"

# Address Cleaning Function
def clean_address(address):
    address = str(address).strip().lower()
    address = re.sub(r'[^a-zA-Z0-9\s,]', '', address)
    address = re.sub(r'\s+', ' ', address)

    common_replacements = {
        'rd': 'road', 'st': 'street', 'ave': 'avenue',
        'svrd': 'sv road', 'mg rd': 'mg road'
    }
    for key, val in common_replacements.items():
        address = re.sub(fr'\b{key}\b', val, address, flags=re.IGNORECASE)

    return address

# Fuzzy Matching
def fuzzy_match(query, addresses):
    scores = [(idx, fuzz.partial_ratio(query, addr)) for idx, addr in enumerate(addresses)]
    return [idx for idx, score in sorted(scores, key=lambda x: x[1], reverse=True) if score > 50]

# Address Search Function
def search_addresses(df, query, pincodes, lat=None, lon=None, radius_km=10):
    query = query.strip().lower()
    df["Cleaned_Address"] = df["Address"].apply(clean_address)

    # Fuzzy matching
    fuzzy_indices = fuzzy_match(query, df["Cleaned_Address"])
    if not fuzzy_indices:
        return pd.DataFrame()

    # Filter dataframe with fuzzy match results
    filtered_df = df.iloc[fuzzy_indices].copy()

    # Apply TF-IDF + Cosine Similarity
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(filtered_df["Cleaned_Address"].tolist() + [query])
    similarity_scores = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])[0]
    
    sorted_indices = similarity_scores.argsort()[::-1]
    relevant_indices = [fuzzy_indices[idx] for idx in sorted_indices if similarity_scores[idx] > 0.1]

    # Filter by Pincode
    if pincodes:
        relevant_indices = [idx for idx in relevant_indices if str(df.iloc[idx]["Pincode"]) in pincodes]

    # Filter by Geolocation Distance
    if lat and lon and "Latitude" in df.columns and "Longitude" in df.columns:
        df["Distance"] = df.apply(lambda row: geodesic((lat, lon), (row["Latitude"], row["Longitude"])).km, axis=1)
        df = df[df["Distance"] <= radius_km]

    return df.iloc[relevant_indices]

# Upload File API
@app.route('/upload', methods=['POST'])
def upload_file():
    global df  # Use the global dataframe variable

    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    file_type = file.filename.split('.')[-1]

    try:
        if file_type == "csv":
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)

        df["Address"] = df["Address"].apply(clean_address)
        return jsonify({"message": "File uploaded successfully!", "rows": len(df)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Search API
@app.route('/search', methods=['POST'])
def search():
    global df  # Use the global dataframe variable

    if df is None:
        return jsonify({"error": "No file uploaded yet!"}), 400

    data = request.json
    query = data.get('query', '')
    pincodes = data.get('pincodes', [])
    lat = data.get('lat')
    lon = data.get('lon')
    radius_km = data.get('radius_km', 10)

    result = search_addresses(df, query, pincodes, lat, lon, radius_km)
    return jsonify(result.to_dict(orient="records"))

# Run Flask Server
if __name__ == '__main__':
    app.run(debug=True)
