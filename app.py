import pandas as pd
import re
import numpy as np
from fuzzywuzzy import fuzz
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import joblib

# Load reference clustering file
ref_file = "D:/data for address/add/cluster.xlsx"
df_ref = pd.read_excel(ref_file)

# Load address dataset
address_file = "D:/data for address/masterdata2025.xlsx"
df_new = pd.read_excel(address_file)

# AI Model for NLP Matching
sbert_model = SentenceTransformer("all-MiniLM-L6-v2")

# Preprocess cluster data
cluster_dict = {}
for _, row in df_ref.iterrows():
    keyword = str(row["Keyword"]).strip()
    pincode = str(row["pincode"]).strip()
    if ":" in keyword and "[" in keyword:
        cluster_name = keyword.split(":")[0].strip()
        sub_areas = keyword.split("[")[-1].replace("]", "").replace(";", ",").split(",")
        sub_areas = [area.strip().lower() for area in sub_areas]
        cluster_dict[cluster_name] = {"areas": sub_areas, "pincode": pincode}

# Prepare TF-IDF model
corpus = [" ".join(data["areas"]) for data in cluster_dict.values()]
vectorizer = TfidfVectorizer()
tfidf_matrix = vectorizer.fit_transform(corpus)
cluster_names = list(cluster_dict.keys())

# Generate embeddings for clusters
cluster_embeddings = sbert_model.encode(corpus, convert_to_tensor=True)

def clean_text(text):
    text = str(text).lower().strip()
    text = re.sub(r"[^a-zA-Z0-9\s,]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text

def match_cluster(address, pincode):
    address = clean_text(address)
    address_vector = vectorizer.transform([address])
    similarity_scores = cosine_similarity(address_vector, tfidf_matrix)[0]
    best_tfidf_idx = np.argmax(similarity_scores)
    best_tfidf_score = similarity_scores[best_tfidf_idx]
    best_cluster_tfidf = cluster_names[best_tfidf_idx] if best_tfidf_score > 0.4 else None
    
    # SBERT Embedding Match
    address_embedding = sbert_model.encode([address], convert_to_tensor=True)
    best_sbert_score = np.max(cosine_similarity(address_embedding, cluster_embeddings)[0])
    best_cluster_sbert = cluster_names[np.argmax(best_sbert_score)] if best_sbert_score > 0.5 else None
    
    # Fuzzy Matching
    best_fuzzy_score = 0
    best_fuzzy_match = None
    for cluster, data in cluster_dict.items():
        for area in data["areas"]:
            score = fuzz.token_set_ratio(address, area)
            if score > best_fuzzy_score:
                best_fuzzy_score = score
                best_fuzzy_match = cluster
    
    # Decision Logic
    if best_fuzzy_score > 65:
        return best_fuzzy_match
    elif best_cluster_sbert:
        return best_cluster_sbert
    elif best_cluster_tfidf:
        return best_cluster_tfidf
    else:
        return "Unmatched"

# Apply clustering to new addresses
df_new["Cluster"] = df_new.apply(lambda row: match_cluster(str(row["Address"]), str(row["Pincode"])), axis=1)

df_new.to_excel("clustered_addresses.xlsx", index=False)
print("✅ AI-based clustering completed. Results saved to 'clustered_addresses.xlsx'.")
