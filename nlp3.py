import re
import pandas as pd

# Dictionary for abbreviation expansion
ABBREVIATIONS = {
    "RD": "Road",
    "BLDG": "Building",
    "FLR": "Floor",
    "APT": "Apartment",
    "SCH": "School",
    "NGR": "Nagar",
    "EST": "Estate",
    "CTR": "Centre",
    "COL": "Colony"
}

def expand_abbreviations(text):
    """Replaces abbreviations with full words."""
    words = text.split()
    words = [ABBREVIATIONS.get(word, word) for word in words]
    return " ".join(words)

def fix_missing_spaces(text):
    """Inserts spaces between merged capitalized words like 'hospitalLokhandwala' -> 'hospital Lokhandwala'."""
    text = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', text)  # Add space between lowercase and uppercase letters
    text = re.sub(r'(?<=[A-Z])(?=[A-Z][a-z])', ' ', text)  # Add space between uppercase and lowercase sequences
    return text

def remove_duplicate_words(text):
    """Removes consecutive duplicate words."""
    words = text.split()
    new_words = []
    for word in words:
        if not new_words or new_words[-1].lower() != word.lower():
            new_words.append(word)
    return " ".join(new_words)

def normalize_spacing(text):
    """Fixes extra spaces and ensures space before pincodes."""
    text = re.sub(r'(\d{6})', r' \1', text)  # Ensure space before pincode
    text = re.sub(r'\s+', ' ', text).strip()  # Remove extra spaces
    return text

def preprocess_address(address):
    """Applies all preprocessing steps to clean the address."""
    address = address.upper()  # Convert to uppercase (standard format)
    address = fix_missing_spaces(address)
    address = expand_abbreviations(address)
    address = remove_duplicate_words(address)
    address = normalize_spacing(address)
    return address

# Load the CSV file
df = pd.read_csv("D:/data for address/master.csv")  # Ensure it has a column 'Address'

# Apply preprocessing
df["Cleaned Address"] = df["Address"].astype(str).apply(preprocess_address)

# Save cleaned addresses to a new CSV
df.to_csv("D:/data for address/cleaned_addresses.csv", index=False)

print("✅ Address preprocessing completed! Cleaned data saved as 'cleaned_addresses.csv'")
