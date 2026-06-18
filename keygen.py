import hashlib

SECRET_SALT = "AhmadMukhtarSecureDHIS2Key#2026" # Must match dhis2_app.py exactly

# 1. Input your client's details
facility_name = "Wudil General Hospital"
expiry_date = "2026-07-16"  # 📅 Set subscription end date format: YYYY-MM-DD

# 2. Calculate the secure activation token
raw_string = f"{facility_name}{expiry_date}{SECRET_SALT}"
activation_key = hashlib.sha256(raw_string.encode('utf-8')).hexdigest()[:16]

# 3. Output the exact line needed for deployment
print("--- COPY AND PASTE THIS LINE INTO ALLOWED_FACILITIES.TXT ---")
print(f"{facility_name} = {expiry_date}|{activation_key}")
print("------------------------------------------------------------")
input("Press ENTER to exit...")