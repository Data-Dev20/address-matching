import pandas as pd
import re
from fuzzywuzzy import process
from sklearn.feature_extraction.text import TfidfVectorizer

# Load dataset
df = pd.read_excel('D:/data for address/masterdata2025.xlsx')

# Preprocess Address Column
def clean_address(address):
    address = str(address).strip()
    address = re.sub(r'[^a-zA-Z0-9\s]', '', address)  # Remove special characters
    address = re.sub(r'\s+', ' ', address)  # Normalize spaces
    common_replacements = {
        'rd': 'road', 'st': 'street', 'ave': 'avenue', 'blvd': 'boulevard',
        'svrd': 'sv road', 'mg rd': 'mg road', 'jdbc': 'junction'
    }
    for key, val in common_replacements.items():
        address = re.sub(fr'\b{key}\b', val, address, flags=re.IGNORECASE)
    return address

df['Address'] = df['Address'].apply(clean_address)

# Extract Keywords including city and pincode
def extract_keywords(addresses, cities, pincodes):
    vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
    vectorizer.fit_transform(addresses)
    address_keywords = set(vectorizer.get_feature_names_out())

    # Combine with city names and pincodes
    all_keywords = address_keywords.union(set(cities)).union(set(pincodes))
    return sorted(all_keywords)

# Extract distinct cities and pincodes
cities = df['R_City'].astype(str).unique()
pincodes = df['Pincode'].astype(str).unique()

keywords = extract_keywords(df['Address'], cities, pincodes)

# Save extracted keywords
keywords_df = pd.DataFrame(keywords, columns=['Keyword'])
keywords_df.to_csv('keywords.csv', index=False)

# Improved Search Function
def search_addresses(df, query, threshold=90):
    query = query.strip()
    
    # **1. Try Exact Match First**
    exact_matches = df[df['Address'].str.contains(re.escape(query), regex=True, case=False, na=False)]
    if not exact_matches.empty:
        return exact_matches

    # **2. Use Fuzzy Matching for Partial Matches**
    fuzzy_matches = []
    for index, address in df['Address'].items():
        match_score = process.extract(query, [address], limit=1)  # Get top match
        if match_score and match_score[0][1] >= threshold:
            fuzzy_matches.append(index)
    
    return df.loc[fuzzy_matches] if fuzzy_matches else pd.DataFrame(columns=df.columns)  # Ensure DataFrame output

# Example input query
query = input("Enter a keyword to search for related addresses: ")
result = search_addresses(df, query)

# Save result
result.to_csv('filtered_addresses.csv', index=False)

print(f"Filtered addresses saved to filtered_addresses.csv - Total Matches: {len(result)}")

# Display top 10 matches
print(result.head(10))
