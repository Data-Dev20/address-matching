from flask import Flask, request, jsonify
import mysql.connector
import pandas as pd
import re
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer

app = Flask(__name__)

# Database connection
def db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="your_user",         # Change this
        password="your_password", # Change this
        database="address_db"
    )

# Address Cleaning
def clean_address(address):
    address = str(address).strip().lower()
    address = re.sub(r'[^a-zA-Z0-9\s,]', '', address)
    address = re.sub(r'\s+', ' ', address)
    return address

# Clustering Addresses
def cluster_addresses():
    conn = db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, address FROM addresses")
    data = cursor.fetchall()
    
    if len(data) < 3:
        return {"message": "Not enough data for clustering"}

    df = pd.DataFrame(data)
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(df["address"])
    
    kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
    df["cluster_id"] = kmeans.fit_predict(tfidf_matrix)
    
    for index, row in df.iterrows():
        cursor.execute("UPDATE addresses SET cluster_id = %s WHERE id = %s", (row["cluster_id"], row["id"]))
    conn.commit()
    return {"message": "Clustering completed!"}

# Store Address API
@app.route("/store_address", methods=["POST"])
def store_address():
    data = request.json
    conn = db_connection()
    cursor = conn.cursor()
    
    cursor.execute("INSERT INTO addresses (address, pincode) VALUES (%s, %s)", (data["address"], data["pincode"]))
    conn.commit()
    
    return jsonify({"message": "Address stored successfully!"})

# Search Address API
@app.route("/search_address", methods=["GET"])
def search_address():
    query = request.args.get("query")
    pincode = request.args.get("pincode")
    
    conn = db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM addresses WHERE address LIKE %s AND pincode = %s", ('%' + query + '%', pincode))
    result = cursor.fetchall()
    
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)
