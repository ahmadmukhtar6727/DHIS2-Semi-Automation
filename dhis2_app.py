import os
import sys
import time
import hashlib
import datetime
import urllib.request
import urllib.error
import traceback
import tkinter as tk
from tkinter import ttk, messagebox
import threading

def get_base_path():
    """Returns the correct directory path whether running as script or compiled .exe"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(".")

BASE_DIR = get_base_path()
os.chdir(BASE_DIR)

SECRET_SALT = "AhmadMukhtarSecureDHIS2Key#V2_2026"
GITHUB_LICENSE_URL = "https://raw.githubusercontent.com/ahmadmukhtar6727/DHIS2-Semi-Automation/main/data/allowed_facilities.txt"

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService

try:
    from webdriver_manager.microsoft import EdgeChromiumDriverManager
except ImportError:
    EdgeChromiumDriverManager = None

import config

FACILITY_USER_MAP = {}

def verify_subscription_license(facility_name, expiry_date_str, username, provided_key):
    try:
        exp_str = expiry_date_str.strip()
        p_key = provided_key.strip()
        
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
            
            if license_data.count("|") == 2:
                expiry_date_str, assigned_username, activation_key = license_data.split("|", 2)
                
                status = verify_subscription_license(facility_name, expiry_date_str, assigned_username, activation_key)
                
                if status == "ACTIVE":
                    valid_facilities.append(facility_name)
                    FACILITY_USER_MAP[facility_name] = assigned_username.strip()
                elif status == "EXPIRED":
                    print(f"🛑 Subscription EXPIRED on server for: {facility_name}")
                else:
                    print(f"⚠️ Security Tamper Alert detected for entry: {facility_name}")
                    
    return valid_facilities


def run_zero_filling_pipeline(target_facility, username, password, status_label, upload_btn):
    driver = None
    try:
        root.after(0, lambda: status_label.config(text="Checking facility credentials...", foreground="#0056b3"))
        allowed_facilities = local_load_facilities()
        
        if not allowed_facilities or target_facility not in allowed_facilities:
            root.after(0, lambda: status_label.config(text="❌ Error: License Denied.", foreground="red"))
            root.after(0, lambda: messagebox.showerror("License Error", "Facility does not possess an active subscription or valid activation details."))
            return
        
        secure_assigned_user = FACILITY_USER_MAP.get(target_facility, "")
        if username != secure_assigned_user:
            root.after(0, lambda: status_label.config(text="❌ Error: Username Altered.", foreground="red"))
            root.after(0, lambda: messagebox.showerror("Security Enforcement", "The username for this facility has been altered. Execution terminated."))
            return

        root.after(0, lambda: status_label.config(text="⚡ Launching Microsoft Edge...", foreground="#0056b3"))
        
        options = EdgeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")

        edge_paths = [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            os.path.expanduser(r"~\AppData\Local\Microsoft\Edge\Application\msedge.exe")
        ]
        for path in edge_paths:
            if os.path.exists(path):
                options.binary_location = path
                break

        try:
            service = EdgeService()
            driver = webdriver.Edge(service=service, options=options)
        except Exception as primary_err:
            try:
                if EdgeChromiumDriverManager:
                    driver_path = EdgeChromiumDriverManager(latest_release_url="https://msedgedriver.azureedge.net/LATEST_STABLE").install()
                    service = EdgeService(executable_path=driver_path)
                    driver = webdriver.Edge(service=service, options=options)
                else:
                    raise primary_err
            except Exception as fallback_err:
                raise Exception(
                    f"Unable to launch Microsoft Edge.\n\n"
                    f"Please ensure Microsoft Edge is installed and updated on this PC.\n"
                    f"Details:\nNative: {primary_err}\nFallback: {fallback_err}"
                )

        wait = WebDriverWait(driver, 20)

        root.after(0, lambda: status_label.config(text="🔐 Processing DHIS2 login...", foreground="#0056b3"))
        driver.get(config.DHIS2_URL)
        
        wait.until(EC.presence_of_element_located((By.ID, "j_username"))).send_keys(username)
        driver.find_element(By.ID, "j_password").send_keys(password)
        driver.find_element(By.ID, "submit").click()
        
        root.after(0, lambda: status_label.config(text="👋 Awaiting staff setup in browser...", foreground="#e67e22"))
        
        handoff_message = (
            f"Please switch to the opened Edge browser window now and:\n\n"
            f"1. Navigate to Data Entry App.\n"
            f"2. Select Org Unit: '{target_facility}'\n"
            f"3. Select Data Set, Period, and load the form completely.\n\n"
            f"⚠️ IMPORTANT: Make sure the form table with input boxes is fully loaded on screen before clicking OK below!"
        )
        messagebox.showinfo("Staff Action Required", handoff_message)

        root.after(0, lambda: status_label.config(text="🔍 Verifying target facility in DHIS2 UI...", foreground="#0056b3"))
        
        verify_org_script = """
        function getActiveOrgUnit() {
            var selectors = [
                "[data-test='org-unit-tree-node']",
                "[class*='orgUnit']", 
                "[class*='OrgUnit']",
                "#selectedOrgUnitName",
                "#selectedOrgUnit",
                ".selected-org-unit",
                ".org-unit-title",
                "header [class*='title']"
            ];
            
            for (var i = 0; i < selectors.length; i++) {
                var elements = document.querySelectorAll(selectors[i]);
                for (var j = 0; j < elements.length; j++) {
                    var text = elements[j].innerText || elements[j].textContent;
                    if (text && text.trim().length > 0) {
                        if (elements[j].className && (
                            elements[j].className.includes('selected') || 
                            elements[j].className.includes('active')
                        )) {
                            return text.trim();
                        }
                    }
                }
            }

            var activeNodes = document.querySelectorAll(".tree-node-selected, a.selected, li.selected > a, [class*='selected']");
            var foundTexts = [];
            activeNodes.forEach(function(node) {
                if (node.innerText && node.innerText.trim()) {
                    foundTexts.push(node.innerText.trim());
                }
            });
            if (foundTexts.length > 0) {
                return foundTexts.join(" ");
            }

            if (typeof selection !== 'undefined' && selection.getSelected) {
                var selectedUnits = selection.getSelected();
                if (selectedUnits && selectedUnits.length > 0) {
                    return selectedUnits[0];
                }
            }
            
            var topHeader = document.querySelector("#header, header, top-bar");
            return topHeader ? topHeader.innerText : document.body.innerText;
        }
        return getActiveOrgUnit();
        """
        current_ui_org = driver.execute_script(verify_org_script)
        
        if current_ui_org and target_facility.strip().lower() not in current_ui_org.strip().lower():
            root.after(0, lambda: status_label.config(text="❌ Error: Facility Mismatch.", foreground="red"))
            root.after(0, lambda: messagebox.showerror(
                "Security & Facility Enforcement", 
                f"Unauthorized Facility Target!\n\n"
                f"Selected Subscribed Facility: {target_facility}\n"
                f"Detected Active in Browser: {current_ui_org[:50]}...\n\n"
                f"Execution stopped. You can only run automation on the facility matching your active subscription."
            ))
            return

        root.after(0, lambda: status_label.config(text="🚀 Injecting 50-by-50 zero-fill batching...", foreground="#0056b3"))

        js_batched_script = """
        var callback = arguments[arguments.length - 1];
        var fields = document.querySelectorAll("input.entryfield, input[id*='dataelement'], input[id*='entry'], input[type='text'], input[type='number']");
        
        var filledCount = 0;
        var index = 0;
        var batchSize = 50;

        function processBatch() {
            var limit = Math.min(index + batchSize, fields.length);
            for (; index < limit; index++) {
                var field = fields[index];
                if (field.offsetWidth > 0 && field.offsetHeight > 0 && !field.disabled && !field.readOnly) {
                    if (field.value.trim() === "") {
                        field.value = "0";
                        field.dispatchEvent(new Event('input', { bubbles: true }));
                        field.dispatchEvent(new Event('change', { bubbles: true }));
                        field.dispatchEvent(new Event('blur', { bubbles: true }));
                        filledCount++;
                    }
                }
            }
            
            if (index < fields.length) {
                setTimeout(processBatch, 150);
            } else {
                callback(filledCount);
            }
        }
        processBatch();
        """
        
        driver.set_script_timeout(300)
        zero_count = driver.execute_async_script(js_batched_script)
        
        root.after(0, lambda: status_label.config(text=f"✅ Finished! Filled {zero_count} fields.", foreground="green"))
        
        # Event flag to synchronize UI click with the background thread
        completion_event = threading.Event()

        def show_completion_and_signal():
            messagebox.showinfo("Process Complete", f"Successfully batched and zero-filled {zero_count} empty input cells!\n\nClick OK to close the browser.")
            completion_event.set()

        root.after(0, show_completion_and_signal)
        
        # Background thread pauses here until the user clicks OK on the messagebox
        completion_event.wait()

    except Exception as e:
        full_error = traceback.format_exc()
        print(f"FULL EXCEPTION:\n{full_error}")
        root.after(0, lambda: status_label.config(text="❌ Error occurred during runtime.", foreground="red"))
        root.after(0, lambda err=full_error: messagebox.showerror("Execution Error", f"An error occurred within the automation loop:\n\n{err}"))
    finally:
        # Browser only closes once completion_event.wait() unblocks
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
        root.after(0, lambda: upload_btn.config(state="normal"))


def on_facility_select(event):
    selected_facility = facility_entry.get()
    assigned_user = FACILITY_USER_MAP.get(selected_facility, "")
    
    username_entry.config(state="normal")
    username_entry.delete(0, tk.END)
    username_entry.insert(0, assigned_user)
    username_entry.config(state="readonly")

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

ttk.Label(frame, text="Select Activated Facility / Org Unit Name:").pack(anchor="w", pady=(0, 2))
facility_options = local_load_facilities()

facility_entry = ttk.Combobox(frame, values=facility_options, state="readonly", width=37)
facility_entry.pack(fill="x", pady=(0, 12))
facility_entry.bind("<<ComboboxSelected>>", on_facility_select)

status_frame = ttk.Frame(frame, padding=5)
status_frame.pack(fill="x", pady=(0, 12))

ttk.Label(frame, text="DHIS2 Automated Username (Locked):").pack(anchor="w", pady=(0, 2))
username_entry = ttk.Entry(frame, width=40, font=("Segoe UI", 10, "bold"))
username_entry.pack(fill="x", pady=(0, 12))

if facility_options:
    facility_entry.current(0)
    sub_status_lbl = tk.Label(status_frame, text="🟢 Status: Subscribed & Active", font=("Segoe UI", 10, "bold"), fg="green", bg="#f4f6f9")
    sub_status_lbl.pack(anchor="w")
    on_facility_select(None)
else:
    facility_entry.set("No active facilities registered")
    sub_status_lbl = tk.Label(status_frame, text="🔴 Status: Subscription Expired / Unpaid", font=("Segoe UI", 10, "bold"), fg="red", bg="#f4f6f9")
    sub_status_lbl.pack(anchor="w")
    username_entry.insert(0, "No Active Subscription")
    username_entry.config(state="readonly")

ttk.Label(frame, text="Enter DHIS2 Account Password:").pack(anchor="w", pady=(0, 2))
password_entry = ttk.Entry(frame, show="*", width=40)
password_entry.pack(fill="x", pady=(0, 20))

style.configure("Action.TButton", font=("Segoe UI", 11, "bold"), foreground="white", background="#17b978")
style.map("Action.TButton", background=[("disabled", "#bdc3c7"), ("active", "#119961")])
upload_btn = ttk.Button(frame, text="🚀 Run Zero-Filling Automation", style="Action.TButton", command=start_pipeline_thread)
upload_btn.pack(fill="x", ipady=5)

payment_frame = tk.LabelFrame(frame, text=" Monthly Subscription Renewal ", font=("Segoe UI", 9, "bold"), bg="#f4f6f9", fg="#1e3d59", padx=10, pady=10)
payment_frame.pack(fill="x", pady=(20, 0))

payment_info = (
    "To renew or activate a facility subscription, please transfer "
    "your monthly fee of 2,000 NGN for 1-month access to:\n\n"
    "🏦 Bank: Moniepoint\n"
    "🔢 Account Number: 8167270427\n"
    "👤 Name: Ahmad Mukhtar\n\n"
    "After payment, provide your Facility Name & DHIS2 Username to the developer via WhatsApp."
)
tk.Label(payment_frame, text=payment_info, font=("Segoe UI", 9), justify="left", bg="#f4f6f9", fg="#333333", wraplength=370).pack(anchor="w")

status_label = ttk.Label(frame, text="System Ready", font=("Segoe UI", 9, "italic"), foreground="gray")
status_label.pack(pady=(15, 0))

root.mainloop()