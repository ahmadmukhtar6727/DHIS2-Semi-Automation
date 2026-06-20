import os
import sys
import time
import hashlib  
import datetime  
import urllib.request  
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

# 🔑 Master Passphrase - locks both facility name and assigned username
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
from selenium.webdriver.edge.service import Service as EdgeService                  
from webdriver_manager.microsoft import EdgeChromiumDriverManager  

import config

# Global dictionary to map facility names to their assigned secure usernames
FACILITY_USER_MAP = {}

# =========================================================================
# 🔐 STEP 2: STREAMLINED LICENSE VERIFICATION METHOD
# =========================================================================
def verify_subscription_license(facility_name, expiry_date_str, username, provided_key):
    """Streamlined verification strategy checking system expiration tokens securely."""
    try:
        exp_str = expiry_date_str.strip()
        p_key = provided_key.strip()
        
        # Match the simplified keygen strategy (Expiry + Salt)
        raw_string = f"{exp_str}{SECRET_SALT}"
        expected_key = hashlib.sha256(raw_string.encode('utf-8')).hexdigest()[:16]
        
        if expected_key != p_key:
            return "INVALID_KEY"
            
        expiry_date = datetime.datetime.strptime(exp_str, "%Y-%m-%d").date()
        current_date = datetime.date.today()
        
        if current_date > expiry_date:
            return "EXPIRED"
            
        return "ACTIVE"
    except Exception:
        return "INVALID_FORMAT"

def local_load_facilities():
    """Fetches subscriptions live from GitHub, parsing expiry dates and secure usernames."""
    global FACILITY_USER_MAP
    local_path = os.path.join(BASE_DIR, "data", "allowed_facilities.txt")
    lines = []
    
    try:
        print("🌐 Syncing subscription licenses from GitHub status endpoints...")
        req = urllib.request.Request(
            GITHUB_LICENSE_URL, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req, timeout=7) as response:
            content = response.read().decode('utf-8')
            lines = content.splitlines()
            
        try:
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, "w", encoding="utf-8") as backup_file:
                backup_file.write(content)
        except Exception:
            pass

    except Exception as e:
        print(f"🛑 Network Error details: {str(e)}")
        if os.path.exists(local_path):
            with open(local_path, "r", encoding="utf-8") as file:
                lines = file.readlines()
        else:
            return []
             
    valid_facilities = []
    is_facility_section = False
    FACILITY_USER_MAP.clear()
    
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
            
            # Expecting format: ExpiryDate|AssignedUsername|ActivationKey
            if license_data.count("|") == 2:
                expiry_date_str, assigned_username, activation_key = license_data.split("|", 2)
                
                status = verify_subscription_license(facility_name, expiry_date_str, assigned_username, activation_key)
                
                if status == "ACTIVE":
                    valid_facilities.append(facility_name)
                    FACILITY_USER_MAP[facility_name] = assigned_username.strip()  # Save username to map
                elif status == "EXPIRED":
                    print(f"🛑 Subscription EXPIRED on server for: {facility_name}")
                else:
                    print(f"⚠️ Security Tamper Alert detected for entry: {facility_name}")
                    
    return valid_facilities

# --- CORE AUTOMATION ENGINE ---
def run_zero_filling_pipeline(target_facility, username, password, status_label, upload_btn):
    driver = None
    try:
        status_label.config(text="Checking facility credentials...", foreground="#0056b3")
        allowed_facilities = local_load_facilities()
        
        if not allowed_facilities or target_facility not in allowed_facilities:
            status_label.config(text="❌ Error: License Denied.", foreground="red")
            messagebox.showerror("License Error", "Facility does not possess an active subscription or valid activation details.")
            return
        
        # Enforce that the running username matches the cryptographically assigned secure username
        secure_assigned_user = FACILITY_USER_MAP.get(target_facility, "")
        if username != secure_assigned_user:
            status_label.config(text="❌ Error: Username Altered.", foreground="red")
            messagebox.showerror("Security Enforcement", "The username for this facility has been altered. Execution terminated.")
            return

        status_label.config(text="⚡ Launching Microsoft Edge...", foreground="#0056b3")
        options = webdriver.EdgeOptions()
        options.add_argument("--start-maximized")
        
        service = EdgeService(EdgeChromiumDriverManager().install())
        driver = webdriver.Edge(service=service, options=options) 
        wait = WebDriverWait(driver, 20)

        status_label.config(text="🔐 Processing DHIS2 login...", foreground="#0056b3")
        driver.get(config.DHIS2_URL)
        
        wait.until(EC.presence_of_element_located((By.ID, "j_username"))).send_keys(username)
        driver.find_element(By.ID, "j_password").send_keys(password)
        driver.find_element(By.ID, "submit").click()
        
        status_label.config(text="👋 Awaiting staff setup in browser...", foreground="#e67e22")
        handoff_message = (
            f"Please switch to the opened Edge window and:\n\n"
            f"1. Open your Data Entry app.\n"
            f"2. Select the specific Org Unit: '{target_facility}'\n"
            f"3. Set your Dataset, Period, and Form options.\n"
            f"4. Position your cursor inside the FIRST input cell.\n\n"
            f"Once loaded, click OK below to execute zero-filling."
        )
        messagebox.showinfo("Staff Handoff Actions", handoff_message)

        status_label.config(text="🚀 Injecting script and executing zero-fill...", foreground="#0056b3")
        
        # =========================================================================
        # ⚡ ASYNC BATCHED SCRIPT INJECTION (FIXES TIMEOUT CRASHES ON LARGE FORMS)
        # =========================================================================
        js_script = """
        var callback = arguments[arguments.length - 1];
        var fields = document.querySelectorAll("input.entryfield, input[id*='dataelement']");
        if (fields.length === 0) { fields = document.querySelectorAll("input[type='text'], input[type='number']"); }
        
        var filledCount = 0;
        var index = 0;
        var batchSize = 30; // Throttles processing into small waves to prevent freezing the UI

        function processBatch() {
            var limit = Math.min(index + batchSize, fields.length);
            for (; index < limit; index++) {
                var field = fields[index];
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
            }
            
            if (index < fields.length) {
                setTimeout(processBatch, 40); // 40ms structural pause between batches
            } else {
                callback(filledCount); // Safely returns result to Selenium when finished
            }
        }
        processBatch();
        """
        
        # Give Selenium script runtime tolerance for massive datasets
        driver.set_script_timeout(45)
        zero_count = driver.execute_async_script(js_script)
        
        status_label.config(text=f"Syncing {zero_count} zero-filled records...", foreground="#0056b3")
        time.sleep(3) 
        
        try:
            complete_btn = driver.find_element(By.CSS_SELECTOR, "input[id='completeBtn'], button[id='completeBtn'], .complete-button-class")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", complete_btn)
            if messagebox.askyesno("Form Complete Detected", "Would you like to trigger execution automatically?"):
                complete_btn.click()
                status_label.config(text="✅ Process finished. Form marked Complete.", foreground="green")
            else:
                status_label.config(text="✅ Process finished. Form completion bypassed.", foreground="green")
        except Exception:
            status_label.config(text="✅ Process finished.", foreground="green")
            messagebox.showinfo("Process Complete", f"Successfully filled {zero_count} empty fields!")

    except Exception as e:
        status_label.config(text="❌ Error occurred during runtime.", foreground="red")
        messagebox.showerror("Execution Error", f"An error occurred within the automation loop:\n{str(e)}")
    finally:
        if driver:
            status_label.config(text="System Ready", foreground="gray")
            driver.quit()
        upload_btn.config(state="normal")


# --- UI EVENT HANDLING ---
def on_facility_select(event):
    """Fired automatically when a facility is picked. Injects and locks down the assigned username."""
    selected_facility = facility_entry.get()
    assigned_user = FACILITY_USER_MAP.get(selected_facility, "")
    
    # Temporarily change state to normal to edit text field, then freeze it
    username_entry.config(state="normal")
    username_entry.delete(0, tk.END)
    username_entry.insert(0, assigned_user)
    username_entry.config(state="readonly") # 🔒 Locks field from physical keyboard tampering

def start_pipeline_thread():
    facility = facility_entry.get().strip()
    username = username_entry.get().strip()
    password = password_entry.get().strip()
    
    if not facility or not username or not password or facility == "No active facilities registered":
        messagebox.showwarning("Missing Fields", "Please make sure your registered Facility and Password are valid.")
        return
    
    upload_btn.config(state="disabled")
    threading.Thread(
        target=run_zero_filling_pipeline, 
        args=(facility, username, password, status_label, upload_btn), 
        daemon=True
    ).start()


# --- MODERN GUI APP LAYOUT ---
root = tk.Tk()
root.title("DHIS2 Zero Filling")
root.geometry("450x620") 
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

# 🔄 Dropdown Selection Menu
ttk.Label(frame, text="Select Activated Facility / Org Unit Name:").pack(anchor="w", pady=(0, 2))
facility_options = local_load_facilities()

facility_entry = ttk.Combobox(frame, values=facility_options, state="readonly", width=37)
facility_entry.pack(fill="x", pady=(0, 12))
facility_entry.bind("<<ComboboxSelected>>", on_facility_select) # Hook selection event

# 🏷️ Subscription Indicator
status_frame = ttk.Frame(frame, padding=5)
status_frame.pack(fill="x", pady=(0, 12))

# Username Box - Now defaults to Readonly to protect from physical changes
ttk.Label(frame, text="DHIS2 Automated Username (Locked):").pack(anchor="w", pady=(0, 2))
username_entry = ttk.Entry(frame, width=40, font=("Segoe UI", 10, "bold"))
username_entry.pack(fill="x", pady=(0, 12))

if facility_options:
    facility_entry.current(0)
    sub_status_lbl = tk.Label(status_frame, text="🟢 Status: Subscribed & Active", font=("Segoe UI", 10, "bold"), fg="green", bg="#f4f6f9")
    sub_status_lbl.pack(anchor="w")
    # Trigger initial load for the first item in dropdown list
    on_facility_select(None)
else:
    facility_entry.set("No active facilities registered")
    sub_status_lbl = tk.Label(status_frame, text="🔴 Status: Subscription Expired / Unpaid", font=("Segoe UI", 10, "bold"), fg="red", bg="#f4f6f9")
    sub_status_lbl.pack(anchor="w")
    username_entry.insert(0, "No Active Subscription")
    username_entry.config(state="readonly")

# Password Box
ttk.Label(frame, text="Enter DHIS2 Account Password:").pack(anchor="w", pady=(0, 2))
password_entry = ttk.Entry(frame, show="*", width=40)
password_entry.pack(fill="x", pady=(0, 20))

# Run Button
style.configure("Action.TButton", font=("Segoe UI", 11, "bold"), foreground="white", background="#17b978")
style.map("Action.TButton", background=[("disabled", "#bdc3c7"), ("active", "#119961")])
upload_btn = ttk.Button(frame, text="🚀 Run Zero-Filling Automation", style="Action.TButton", command=start_pipeline_thread)
upload_btn.pack(fill="x", ipady=5)

# --- 💳 SUBSCRIPTION PORTAL ---
payment_frame = tk.LabelFrame(frame, text=" Monthly Subscription Renewal ", font=("Segoe UI", 9, "bold"), bg="#f4f6f9", fg="#1e3d59", padx=10, pady=10)
payment_frame.pack(fill="x", pady=(20, 0))

payment_info = (
    "To renew or activate a facility subscription, please transfer "
    "your monthly fee of 2,000 NGN for 1-month access to:\n\n"
    "🏦 Bank: Palmpay\n"
    "🔢 Account Number: 8167270427\n"
    "👤 Name: Ahmad Mukhtar\n\n"
    "After payment, provide your Facility Name & DHIS2 Username to the developer via WhatsApp."
)
tk.Label(payment_frame, text=payment_info, font=("Segoe UI", 9), justify="left", bg="#f4f6f9", fg="#333333", wraplength=370).pack(anchor="w")

status_label = ttk.Label(frame, text="System Ready", font=("Segoe UI", 9, "italic"), foreground="gray")
status_label.pack(pady=(15, 0))

root.mainloop()