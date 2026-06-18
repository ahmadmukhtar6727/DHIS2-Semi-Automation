import os
import sys
import time
import hashlib   # 🔐 Added for secure cryptographic key verification
import datetime  # 📅 Added to handle subscription expiration checks
import urllib.request  # 🌐 Added to fetch subscription keys online from GitHub
import urllib.error

# =========================================================================
# 🔥 DIRECT PATH & SECURITY CONFIGURATION
# =========================================================================
def get_base_path():
    """Returns the correct directory path whether running as script or compiled .exe"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(".")

# Force the app to work where the executable is launched
BASE_DIR = get_base_path()
os.chdir(BASE_DIR)

# 🔑 Change this master passphrase to something unique to you!
# Keep it confidential so users cannot generate their own keys.
SECRET_SALT = "AhmadMukhtarSecureDHIS2Key#2026"

# 🔗 Your exact live GitHub RAW configuration link
GITHUB_LICENSE_URL = "https://raw.githubusercontent.com/ahmadmukhtar6727/DHIS2-Semi-Automation/main/data/allowed_facilities.txt"
# =========================================================================

import tkinter as tk
from tkinter import ttk, messagebox
import threading

# Selenium Dependencies
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import config

def verify_subscription_license(facility_name, expiry_date_str, provided_key):
    """Verifies if the activation key matches the facility name and expiration date, 
    and checks if the subscription is still active."""
    try:
        # 1. Recalculate the cryptographic signature to ensure it hasn't been tampered with
        raw_string = f"{facility_name.strip()}{expiry_date_str.strip()}{SECRET_SALT}"
        expected_key = hashlib.sha256(raw_string.encode('utf-8')).hexdigest()[:16]
        
        if expected_key != provided_key.strip():
            return "INVALID_KEY"
            
        # 2. Parse the expiration date (Expected format: YYYY-MM-DD)
        expiry_date = datetime.datetime.strptime(expiry_date_str.strip(), "%Y-%m-%d").date()
        current_date = datetime.date.today()
        
        # 3. Check if the subscription has expired
        if current_date > expiry_date:
            return "EXPIRED"
            
        return "ACTIVE"
    except Exception:
        return "INVALID_FORMAT"

def local_load_facilities():
    """Fetches the latest active subscriptions directly from GitHub, with an offline local fallback."""
    local_path = os.path.join(BASE_DIR, "data", "allowed_facilities.txt")
    lines = []
    
    # 1. Try to fetch the latest subscription updates live from your GitHub repository
    try:
        print("🌐 Syncing subscription licenses from GitHub status endpoints...")
        req = urllib.request.Request(
            GITHUB_LICENSE_URL, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req, timeout=7) as response:
            content = response.read().decode('utf-8')
            lines = content.splitlines()
            
        # Update local backup cache in case they run it offline next time
        try:
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, "w", encoding="utf-8") as backup_file:
                backup_file.write(content)
        except Exception:
            pass
            
    # 2. Fallback to local offline cache file if there is no internet connection available
    except Exception:
        print("⚠️ Offline or unable to connect to GitHub sync. Using local cache data.")
        if os.path.exists(local_path):
            with open(local_path, "r", encoding="utf-8") as file:
                lines = file.readlines()
        else:
            return []
            
    valid_facilities = []
    is_facility_section = False
    
    # 3. Process and cryptographically verify the downloaded licenses
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        
        if line.upper() == "[FACILITIES]":
            is_facility_section = True
            continue
            
        if is_facility_section and "=" in line:
            parts = line.split("=", 1)
            facility_name = parts[0].strip()
            license_data = parts[1].strip()
            
            if "|" in license_data:
                expiry_date_str, activation_key = license_data.split("|", 1)
                
                status = verify_subscription_license(facility_name, expiry_date_str, activation_key)
                
                if status == "ACTIVE":
                    valid_facilities.append(facility_name)
                elif status == "EXPIRED":
                    print(f"🛑 Subscription EXPIRED on server for: {facility_name}")
                else:
                    print(f"⚠️ Security Tamper Alert detected for entry: {facility_name}")
                    
    return valid_facilities

# --- CORE AUTOMATION ENGINE ---
def run_zero_filling_pipeline(target_facility, username, password, status_label, upload_btn):
    driver = None
    try:
        # 1. Enforce Facility Permission Check (Using the secure signature verification method)
        status_label.config(text="Checking facility credentials...", foreground="#0056b3")
        allowed_facilities = local_load_facilities()
        
        if not allowed_facilities:
            status_label.config(text="❌ Error: No validated facilities found.", foreground="red")
            messagebox.showerror("Error", "No validated or active facility subscriptions found. Please connect to the internet or renew your access.")
            return

        if target_facility not in allowed_facilities:
            status_label.config(text="❌ Error: License Denied.", foreground="red")
            messagebox.showerror("License Error", f"'{target_facility}' does not possess an active subscription or valid activation signature details.")
            return
        
        # 2. Launch Microsoft Edge natively
        status_label.config(text="⚡ Launching Microsoft Edge...", foreground="#0056b3")
        options = webdriver.EdgeOptions()
        options.add_argument("--start-maximized")
        
        driver = webdriver.Edge(options=options) 
        wait = WebDriverWait(driver, 20)

        # 3. Handle Login Flow
        status_label.config(text="🔐 Processing DHIS2 login...", foreground="#0056b3")
        driver.get(config.DHIS2_URL)
        
        wait.until(EC.presence_of_element_located((By.ID, "j_username"))).send_keys(username)
        driver.find_element(By.ID, "j_password").send_keys(password)
        driver.find_element(By.ID, "submit").click()
        
        # 4. Graphical Staff Handoff
        status_label.config(text="👋 Awaiting staff setup in browser...", foreground="#e67e22")
        
        handoff_message = (
            f"Please switch to the opened Edge window and:\n\n"
            f"1. Open your Data Entry app.\n"
            f"2. Select the specific Org Unit: '{target_facility}'\n"
            f"3. Set your Dataset, Period, and Form options.\n"
            f"4. Position your cursor inside the FIRST input cell.\n\n"
            f"Once the form is completely loaded, click OK below to execute zero-filling."
        )
        messagebox.showinfo("Staff Handoff Actions", handoff_message)

        # 5. High-Speed Bulk JavaScript Zero-Filling Engine
        status_label.config(text="🚀 Injecting script and executing zero-fill...", foreground="#0056b3")
        
        js_script = """
        var fields = document.querySelectorAll("input.entryfield, input[id*='dataelement']");
        if (fields.length === 0) {
            fields = document.querySelectorAll("input[type='text'], input[type='number']");
        }
        
        var filledCount = 0;
        fields.forEach(function(field) {
            if (field.offsetWidth > 0 && field.offsetHeight > 0 && !field.disabled) {
                if (field.value.trim() === "") {
                    field.value = "0";
                    
                    var changeEvent = new Event('change', { bubbles: true });
                    var blurEvent = new Event('blur', { bubbles: true });
                    field.dispatchEvent(changeEvent);
                    field.dispatchEvent(blurEvent);
                    
                    filledCount++;
                }
            }
        });
        return filledCount;
        """
        
        zero_count = driver.execute_script(js_script)
        status_label.config(text=f"Syncing {zero_count} zero-filled records to endpoints...", foreground="#0056b3")
        time.sleep(3) 
        
        # 6. Mark Dataset Complete Sequence
        try:
            complete_btn = driver.find_element(By.CSS_SELECTOR, "input[id='completeBtn'], button[id='completeBtn'], .complete-button-class")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", complete_btn)
            
            trigger_complete = messagebox.askyesno("Form Complete Detected", "Form 'Complete' button detected.\nWould you like to trigger execution automatically?")
            if trigger_complete:
                complete_btn.click()
                status_label.config(text="✅ Process finished. Form marked Complete.", foreground="green")
            else:
                status_label.config(text="✅ Process finished. Form completion bypassed.", foreground="green")
                
        except Exception:
            status_label.config(text="✅ Process finished. (Complete button manual override)", foreground="green")
            messagebox.showinfo("Process Complete", f"Successfully filled {zero_count} empty fields!\nCould not hook the 'Complete' button, please finalize manually if required.")

        messagebox.showinfo("Session Finished", "The process sequence has completed successfully.\nClicking OK will close the automated browser safely.")

    except Exception as e:
        status_label.config(text="❌ Error occurred during runtime.", foreground="red")
        messagebox.showerror("Execution Error", f"Something went wrong within the browser automated loop:\n{str(e)}")
        
    finally:
        if driver:
            status_label.config(text="System Ready", foreground="gray")
            driver.quit()
        upload_btn.config(state="normal")


# --- ENGINE CONTROL THREADING ---
def start_pipeline_thread():
    facility = facility_entry.get().strip()
    username = username_entry.get().strip()
    password = password_entry.get().strip()
    
    if not facility or not username or not password or facility == "No active facilities registered":
        messagebox.showwarning("Missing or Invalid Fields", "Please make sure a valid, registered Facility, Username, and Password are provided.")
        return
    
    upload_btn.config(state="disabled")
    
    threading.Thread(
        target=run_zero_filling_pipeline, 
        args=(facility, username, password, status_label, upload_btn), 
        daemon=True
    ).start()


# --- MODERN GUI APP LAYOUT ---
root = tk.Tk()
root.title("DHIS2 Utility Dashboard")
root.geometry("450x620") # 📐 Enlarged height to 620px so everything is fully visible
root.configure(bg="#f4f6f9")
root.resizable(False, False)

style = ttk.Style()
style.theme_use('clam')
style.configure("TLabel", background="#f4f6f9", font=("Segoe UI", 10))
style.configure("TEntry", font=("Segoe UI", 10))
style.configure("TCombobox", font=("Segoe UI", 10))

header = ttk.Label(root, text="DHIS2 Zero-Filling System", font=("Segoe UI", 14, "bold"), background="#1e3d59", foreground="white", padding=15, anchor="center")
header.pack(fill="x", pady=(0, 15))

frame = ttk.Frame(root, padding=20)
frame.pack(fill="both", expand=True)

# 🔄 Secure Dropdown UI Menu Component
ttk.Label(frame, text="Select Activated Facility / Org Unit Name:").pack(anchor="w", pady=(0, 2))
facility_options = local_load_facilities()

facility_entry = ttk.Combobox(frame, values=facility_options, state="readonly", width=37)
facility_entry.pack(fill="x", pady=(0, 12))

# 🏷️ Subscription Status Indicator Notice
status_frame = ttk.Frame(frame, padding=5)
status_frame.pack(fill="x", pady=(0, 12))

if facility_options:
    facility_entry.current(0)
    sub_status_lbl = tk.Label(status_frame, text="🟢 Status: Subscribed & Active", font=("Segoe UI", 10, "bold"), fg="green", bg="#f4f6f9")
    sub_status_lbl.pack(anchor="w")
else:
    facility_entry.set("No active facilities registered")
    sub_status_lbl = tk.Label(status_frame, text="🔴 Status: Subscription Expired / Unpaid", font=("Segoe UI", 10, "bold"), fg="red", bg="#f4f6f9")
    sub_status_lbl.pack(anchor="w")

# Username Box
ttk.Label(frame, text="DHIS2 Account Username:").pack(anchor="w", pady=(0, 2))
username_entry = ttk.Entry(frame, width=40)
username_entry.insert(0, "kahmad") 
username_entry.pack(fill="x", pady=(0, 12))

# Password Box
ttk.Label(frame, text="DHIS2 Account Password:").pack(anchor="w", pady=(0, 2))
password_entry = ttk.Entry(frame, show="*", width=40)
password_entry.pack(fill="x", pady=(0, 20))

# Run Button
style.configure("Action.TButton", font=("Segoe UI", 11, "bold"), foreground="white", background="#17b978")
style.map("Action.TButton", background=[("disabled", "#bdc3c7"), ("active", "#119961")])
upload_btn = ttk.Button(frame, text="🚀 Run Zero-Filling Automation", style="Action.TButton", command=start_pipeline_thread)
upload_btn.pack(fill="x", ipady=5)

# --- 💳 PAYMENT & SUBSCRIPTION PORTAL SECTION ---
payment_frame = tk.LabelFrame(frame, text=" Monthly Subscription Renewal ", font=("Segoe UI", 9, "bold"), bg="#f4f6f9", fg="#1e3d59", padx=10, pady=10)
payment_frame.pack(fill="x", pady=(20, 0))

# 💰 Clear instructions displaying the 1,500 monthly fee
payment_info = (
    "To renew or activate a facility subscription, please transfer "
    "your monthly fee of 1,500 NGN for 1-month access to:\n\n"
    "🏦 Bank: Palmpay\n"
    "🔢 Account Number: 8167270427\n"
    "👤 Name: Ahmad Mukhtar\n\n"
    "After payment, send your Facility Name to the developer WhatsApp (08167270427) "
    "to receive your new 30-day activation key token."
)

# 🛠️ Added wraplength=370 so text cleanly auto-wraps inside the window borders
tk.Label(payment_frame, text=payment_info, font=("Segoe UI", 9), justify="left", bg="#f4f6f9", fg="#333333", wraplength=370).pack(anchor="w")

status_label = ttk.Label(frame, text="System Ready", font=("Segoe UI", 9, "italic"), foreground="gray")
status_label.pack(pady=(15, 0))

root.mainloop()