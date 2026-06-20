import hashlib
import datetime

def generate_facility_license():
    print("==========================================================")
    print("🔐 DEPLOYMENT KEY GENERATOR SYSTEM (STREAMLINED)")
    print("==========================================================")
    
    SECRET_SALT = "AhmadMukhtarSecureDHIS2Key#2026"
    
    # 1. Collect Facility Name
    facility_name = input("📌 Enter Facility Name (e.g., Bichi General Hospital): ").strip()
    if not facility_name:
        print("❌ Error: Facility name cannot be empty.")
        return

    # 2. Collect DHIS2 Username
    username = input("👤 Enter DHIS2 Username to lock down (e.g., Kahmad): ").strip()
    if not username:
        print("❌ Error: Username cannot be empty.")
        return
        
    # 3. Collect Expiration Date
    print("\n💡 Enter Expiration Date parameters:")
    try:
        year = int(input("   Enter Year (e.g., 2026): ").strip())
        month = int(input("   Enter Month (1-12): ").strip())
        day = int(input("   Enter Day (1-31): ").strip())
        
        expiry_date = datetime.date(year, month, day)
        expiry_date_str = expiry_date.strftime("%Y-%m-%d")
    except ValueError:
        print("❌ Error: Invalid numerical date parameters.")
        return

    # 🔐 Streamlined Calculation Strategy: Hash the expiry string + salt
    raw_string = f"{expiry_date_str}{SECRET_SALT}"
    activation_key = hashlib.sha256(raw_string.encode('utf-8')).hexdigest()[:16]
    
    github_line = f"{facility_name} = {expiry_date_str}|{username}|{activation_key}"
    
    print("\n" + "="*58)
    print("🎉 SECURE TOKEN GENERATED SUCCESSFULLY!")
    print("==========================================================")
    print(f"🏢 Facility:  {facility_name}")
    print(f"🔒 Locked To:  {username}")
    print(f"📅 Expires On: {expiry_date_str}")
    print(f"🔑 Key Token:  {activation_key}")
    print("-"*58)
    print("📋 COPY AND PASTE THIS LINE DIRECTLY INTO GitHub (allowed_facilities.txt):")
    print("-"*58)
    print(github_line)
    print("==========================================================\n")

if __name__ == "__main__":
    while True:
        generate_facility_license()
        another = input("Generate another key? (yes/no): ").strip().lower()
        if another not in ['yes', 'y']:
            print("Goodbye!")
            break