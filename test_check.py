import os
import hashlib

BASE_DIR = os.path.abspath(".")
SECRET_SALT = "AhmadMukhtarSecureDHIS2Key#2026" # 🌟 Put your exact salt here!

target_path = os.path.join(BASE_DIR, "data", "allowed_facilities.txt")

print(f"1. Looking for file at: {target_path}")
if not os.path.exists(target_path):
    print("❌ ERROR: The file does not exist at this path! Check your folder layout.")
else:
    print("✅ FILE FOUND! Reading contents...\n")
    with open(target_path, "r", encoding="utf-8") as file:
        is_facility_section = False
        line_num = 0
        for line in file:
            line_num += 1
            raw_line = line.strip()
            if not raw_line or raw_line.startswith("#"):
                continue
            
            print(f"Line {line_num}: '{raw_line}'")
            if raw_line.upper() == "[FACILITIES]":
                is_facility_section = True
                print(" -> Recognized [FACILITIES] section header.")
                continue
                
            if is_facility_section and "=" in raw_line:
                parts = raw_line.split("=", 1)
                fac_name = parts[0].strip()
                prov_key = parts[1].strip()
                
                # Calculate what key the app expects
                raw_str = f"{fac_name}{SECRET_SALT}"
                expected = hashlib.sha256(raw_str.encode('utf-8')).hexdigest()[:16]
                
                print(f" -> Facility Name Parsed: '{fac_name}'")
                print(f" -> Provided Key in file: '{prov_key}'")
                print(f" -> Expected Key by App:  '{expected}'")
                
                if expected == prov_key:
                    print(" 🎉 SUCCESS: Key matches perfectly!")
                else:
                    print(" ❌ MISMATCH: The keys do not match. Check your salt or generated key.")