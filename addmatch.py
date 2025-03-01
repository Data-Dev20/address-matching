import pandas as pd
from rapidfuzz import fuzz, process

# Load the CSV file
df = pd.read_csv("D:/data for address/master.csv")  # Ensure it has a column 'Address'

# **Step 1: Extract Unique Words from Addresses**
def extract_unique_keywords(df):
    """
    Extract unique words from the address column to create a keyword set.
    """
    unique_words = set()
    for address in df["Address"]:
        words = str(address).lower().split()  # Split words in lowercase
        unique_words.update(words)
    return unique_words

# **Step 2: Find Matching Addresses**
def find_matching_addresses(search_term, df, threshold=70):
  
    matches = []

    for address in df["Address"]:
        similarity = fuzz.partial_ratio(search_term.lower(), str(address).lower())
        if similarity >= threshold:
            matches.append(address)

    return pd.DataFrame(matches, columns=["Matched Address"])

# **Step 3: Generate Keyword List Dynamically**
keyword_list = extract_unique_keywords(df)
print("Extracted Keywords:", keyword_list)

# **Step 4: Search for Related Addresses Dynamically**
search_keyword = input("Enter search keyword: ")  # User-defined input
matched_df = find_matching_addresses(search_keyword, df)

# **Step 5: Save matched addresses to CSV**
matched_df.to_csv("matched_addresses.csv", index=False)
print(f"Matched addresses saved to 'matched_addresses.csv'")
