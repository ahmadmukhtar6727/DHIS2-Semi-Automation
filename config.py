import os

DHIS2_URL = "https://datastore.gghnigeria.org/dhis-web-dashboard/index.html#/" 

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FACILITIES_FILE = os.path.join(BASE_DIR, "data", "allowed_facilities.txt")

def load_allowed_facilities():
    """Reads approved facilities from the text file."""
    if not os.path.exists(FACILITIES_FILE):
        return []
    with open(FACILITIES_FILE, "r") as file:
        
        return [line.strip() for line in file if line.strip()]