


import time
import requests
import schedule
import asyncio
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from colorama import Fore, init
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# --- Configuration Section ---
# Initialize colorama for terminal colors
init(autoreset=True)

# --- Telegram Bot Information - Fill this section with your credentials ---
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN"
TELEGRAM_CHANNEL_ID = "@YOUR_CHANNEL_USERNAME"

# --- Main Bot (Silent Mode) ---

def get_one_license():
    """
    Automates the process of getting one Avast trial license.
    Returns the license key on success, or None on failure.
    """
    
    # Configure Chrome options for silent, headless execution
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--log-level=3")
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    driver = None
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        wait = WebDriverWait(driver, 45) # Increased wait time for more stability

        # Step 1: Get temporary email
        driver.get("https://temp-mail.org/")
        email_element = wait.until(EC.visibility_of_element_located((By.ID, "mail")))
        temp_email = email_element.get_attribute('value')

        # Step 2: Register on Avast
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[1])
        driver.get("https://id.avast.com/sso#/create-account")
        
        wait.until(EC.presence_of_element_located((By.ID, "email"))).send_keys(temp_email)
        wait.until(EC.presence_of_element_located((By.ID, "password"))).send_keys("aB123456@#$SecurePass")
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))).click()

        # Step 3: Verify email
        driver.switch_to.window(driver.window_handles[0])
        wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Verify your email address')]"))).click()
        verify_button_in_email = wait.until(EC.element_to_be_clickable((By.XPATH, "//td[contains(., 'Verify email')]//a")))
        driver.get(verify_button_in_email.get_attribute('href'))

        # Step 4: Complete profile
        driver.switch_to.window(driver.window_handles[1])
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-test-id='signup-step1-company']"))).send_keys("MyCompany")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-test-id='signup-step1-first-name']"))).send_keys("Test")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-test-id='signup-step1-last-name']"))).send_keys("User")
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))).click()

        # Step 5: Navigate through hub
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-test-id='signup-trialCardStep-submitButton']"))).click()
        time.sleep(2)
        driver.refresh()
        try:
            time.sleep(3)
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "span.ant-modal-close-icon"))).click()
        except:
            pass # Continue if no popup appears

        # Step 6: Go to subscriptions and extract key
        wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Subscriptions']"))).click()
        license_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-test-id='subscriptions-walletKey-trigger']")))
        license_key = license_element.text
        
        return license_key

    except Exception:
        return None
    finally:
        if driver:
            driver.quit()

# --- Telegram and Scheduling Section ---

async def send_to_telegram(keys):
    """Sends the list of keys to the Telegram channel with a header and download buttons."""
    if not keys:
        return

    # Format the message
    keys_formatted = "\n\n".join(f"> `{key}`" for key in keys)
    message = f"Avast secureline vpn keys:\n\n{keys_formatted}"

    # Create inline keyboard buttons in the requested order
    keyboard = [
        [
            InlineKeyboardButton("Android", url="https://play.google.com/store/apps/details?id=com.avast.android.vpn"),
            InlineKeyboardButton("iOS", url="https://apps.apple.com/app/avast-secureline-vpn-proxy/id793096595")
        ],
        [
            InlineKeyboardButton("Windows PC", url="https://www.avast.com/secureline-vpn#pc"),
            InlineKeyboardButton("macOS", url="https://www.avast.com/secureline-vpn#mac")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
        await bot.send_message(
            chat_id=TELEGRAM_CHANNEL_ID,
            text=message,
            parse_mode='MarkdownV2',
            reply_markup=reply_markup
        )
    except Exception as e:
        # If an error occurs, a message is displayed in the terminal
        print(Fore.RED + f"Error sending to Telegram: {e}")

async def job():
    """The main job that runs every 8 hours to get 3 licenses."""
    licenses = []
    for i in range(3):
        key = get_one_license()
        if key:
            licenses.append(key)
    
    if licenses:
        await send_to_telegram(licenses)

def main():
    """The main function to start the application and schedule jobs."""
    # Display the startup message in light cyan
    print(Fore.LIGHTCYAN_EX + "made with ❤️ by @mehdiasmart")
    
    # Schedule the job
    schedule.every(8).hours.do(lambda: asyncio.run(job()))

    # Run the job once immediately at startup
    asyncio.run(job())

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    if TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN" or TELEGRAM_CHANNEL_ID == "@YOUR_CHANNEL_USERNAME":
        print(Fore.RED + "Error: Please set your TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL_ID in the script.")
    else:
        main()
