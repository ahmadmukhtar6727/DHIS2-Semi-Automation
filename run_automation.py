import time
import getpass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import config

def main():
    print("=============================================")
    print("      DHIS2 ZERO-FILLING UTILITY SYSTEM      ")
    print("=============================================\n")
    
    # 1. Enforce Facility Permission Check
    allowed_facilities = config.load_allowed_facilities()
    
    if not allowed_facilities:
        print("[ERROR] No pre-approved facilities found in data/allowed_facilities.txt.")
        print("Please contact your system administrator to configure permissions.")
        return

    target_facility = input("Enter the EXACT Facility/Org Unit Name to process: ").strip()
    
    if target_facility not in allowed_facilities:
        print(f"\n[PERMISSION DENIED] '{target_facility}' is not an authorized facility.")
        print("You do not have permission to run automation for this location.")
        return
    
    print(f"[SUCCESS] Permission granted for: {target_facility}")
    
    # 2. Staff Login Credentials Input
    username = input("kahmad: ").strip()
    password = getpass.getpass(prompt="Enter your DHIS2 Password: ")

    print("\n[System] Launching Microsoft Edge via Native Selenium Manager...")
    options = webdriver.EdgeOptions()
    options.add_argument("--start-maximized")

    # Native implementation completely circumvents ChunkedEncodingError/10054 drops
    driver = webdriver.Edge(options=options) 
    wait = WebDriverWait(driver, 20)

    try:
        # 3. Handle Login
        driver.get(config.DHIS2_URL)
        print("[System] Loading login page...")
        
        wait.until(EC.presence_of_element_located((By.ID, "j_username"))).send_keys(username)
        driver.find_element(By.ID, "j_password").send_keys(password)
        driver.find_element(By.ID, "submit").click()
        
        # 4. Hand-off context to staff operator
        print("\n-----------------------------------------------------------")
        print("                     STAFF HANDOFF                         ")
        print("-----------------------------------------------------------")
        print("In the opened browser window, please:")
        print("  1. Open your Data Entry app.")
        print(f"  2. Select the specific Org Unit: '{target_facility}'")
        print("  3. Set your Dataset, Period, and Form options.")
        print("  4. Position your cursor inside the FIRST input cell.")
        print("-----------------------------------------------------------")
        
        input("\nOnce the form is completely loaded, return here and press [ENTER] to start zero-filling... ")

        # 5. High-Speed Bulk JavaScript Zero-Filling Engine
        print("\n[System] Preparing high-speed bulk data injection...")
        
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
                    
                    // Force state update loops within DHIS2 frameworks
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
        
        print("[System] Injecting script into page layout...")
        zero_count = driver.execute_script(js_script)
        
        print(f"\n[Done] Successfully filled {zero_count} empty fields instantly with zeros.")
        print("[System] Allowing DHIS2 database endpoints a brief moment to sync changes...")
        time.sleep(3) 
        
        # 6. Mark Dataset Complete Sequence
        print("\n[System] Checking for form Completion element...")
        try:
            complete_btn = driver.find_element(By.CSS_SELECTOR, "input[id='completeBtn'], button[id='completeBtn'], .complete-button-class")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", complete_btn)
            
            trigger_complete = input("Form 'Complete' button detected. Trigger execution automatically? (Y/N): ").strip().upper()
            if trigger_complete == 'Y':
                complete_btn.click()
                print("[System] Form marked as 'Completed' successfully.")
            else:
                print("[System] Bypassed completion click. You may finalize manually in the browser UI.")
        except Exception:
            print("[Note] Could not reliably hook the 'Complete' button via default selectors.")
            print("Please glance over the page and click 'Complete' manually if required.")

        input("\nProcess sequence finished. Press [ENTER] in this terminal to shut down the session safely...")

    finally:
        print("[System] Terminating browser instance.")
        driver.quit()

if __name__ == "__main__":
    main()