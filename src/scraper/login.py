import re
import os, json
import time
import logging
from typing import TypedDict
from playwright.sync_api import Playwright, sync_playwright, expect

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class LoginInfo(TypedDict):
    username: str
    password: str
    expired_token: int

def login_fn(playwright: Playwright, account: LoginInfo, headless: bool = True, development: bool = False) -> None:
    logger = logging.getLogger(__name__)
    
    if development:
        logger.info(f"🚀 Starting login process for user: {account['username']}")
        logger.info(f"🎭 Headless mode: {headless}")
    
    # Launch browser with headless support but configured to avoid detection
    if development:
        logger.info("🌐 Launching browser...")
    
    browser = playwright.chromium.launch(
        headless=headless,
        args=[
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-extensions',
            '--disable-plugins',
            '--disable-images',  # Speed up loading
            '--disable-javascript-harmony-shipping',
            '--disable-background-timer-throttling',
            '--disable-renderer-backgrounding',
            '--disable-backgrounding-occluded-windows',
            '--disable-component-extensions-with-background-pages',
            '--disable-web-security',
            '--disable-features=TranslateUI',
            '--disable-ipc-flooding-protection',
            '--no-first-run',
            '--no-default-browser-check',
            '--disable-default-apps',
            '--disable-popup-blocking',
            '--disable-prompt-on-repost',
            '--disable-hang-monitor',
            '--disable-sync'
        ],
        slow_mo=100 if not headless else 0  # Add slight delay for non-headless mode
    )
    
    if development:
        logger.info("✅ Browser launched successfully")
        logger.info("🎯 Creating browser context with realistic settings...")
    
    # Create context with realistic settings to avoid detection
    context = browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        locale='en-US',
        timezone_id='America/New_York',
        permissions=['geolocation']
    )
    
    # Add realistic headers and behavior
    context.set_extra_http_headers({
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-User': '?1',
        'Sec-Fetch-Dest': 'document'
    })
    
    if development:
        logger.info("📄 Creating new page...")
    
    page = context.new_page()
    
    if development:
        logger.info("🔧 Injecting anti-detection scripts...")
    
    # Remove webdriver property to avoid detection
    page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
        
        // Mock plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
        });
        
        // Mock languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en'],
        });
        
        // Mock permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
    """)
    
    if development:
        logger.info("🌍 Navigating to X.com...")
    
    page.goto("https://x.com/")
    
    # Wait for page to fully load and login button to be available
    if development:
        logger.info("⏳ Waiting for page to load and login button to appear...")
    
    try:
        # Wait for the login button with a longer timeout
        page.wait_for_selector('[data-testid="loginButton"]', timeout=60000)
        if development:
            logger.info("✅ Login button found!")
        
        page.wait_for_timeout(2000)  # Wait to simulate natural loading
        
        # Check if login button is visible and clickable
        login_button = page.get_by_test_id("loginButton")
        login_button.wait_for(state="visible", timeout=10000)
        
        if development:
            logger.info("🔘 Clicking login button...")
        
        login_button.click()
        
        if development:
            logger.info("✅ Login button clicked successfully!")
            
    except Exception as e:
        if development:
            logger.error(f"❌ Error clicking login button: {e}")
            logger.info("🔄 Trying alternative selectors...")
        
        print(f"Error clicking login button: {e}")
        # Try alternative selectors if the main one fails
        try:
            page.click('a[href="/login"]', timeout=10000)
            if development:
                logger.info("✅ Used alternative login link!")
        except:
            if development:
                logger.warning("⚠️ Alternative selectors failed, navigating directly to login page...")
            # If all else fails, navigate directly to login page
            page.goto("https://x.com/login")
            page.wait_for_timeout(3000)
    
    page.wait_for_timeout(1000)  # Brief pause before interacting
    
    if development:
        logger.info("📝 Looking for username field...")
    
    # Wait for username field and fill it
    try:
        username_field = page.get_by_role("textbox", name="Phone, email, or username")
        username_field.wait_for(state="visible", timeout=15000)
        
        if development:
            logger.info("✅ Username field found!")
            logger.info("🖱️ Clicking username field...")
        
        username_field.click()
        page.wait_for_timeout(500)  # Simulate typing delay
        
        if development:
            logger.info(f"⌨️ Typing username: {account['username']}")
        
        username_field.fill(account["username"])
        page.wait_for_timeout(1000)  # Pause after filling
        
        if development:
            logger.info("🔘 Looking for Next button...")
        
        # Click Next button
        next_button = page.get_by_role("button", name="Next")
        next_button.wait_for(state="visible", timeout=10000)
        
        if development:
            logger.info("🔘 Clicking Next button...")
        
        next_button.click()
        page.wait_for_timeout(2000)  # Wait for next page load
        
        if development:
            logger.info("✅ Next button clicked, waiting for password page...")
            
    except Exception as e:
        if development:
            logger.error(f"❌ Error with username field: {e}")
            logger.info("🔄 Trying alternative approach...")
        
        print(f"Error with username field: {e}")
        # Try alternative approach
        try:
            page.fill('input[name="text"]', account["username"])
            page.click('div[role="button"]:has-text("Next")')
            page.wait_for_timeout(2000)
            if development:
                logger.info("✅ Alternative username approach worked!")
        except Exception as e2:
            if development:
                logger.error(f"❌ Alternative username approach also failed: {e2}")
            print(f"Alternative username approach also failed: {e2}")
            raise e2
    
    # Wait for password field and fill it
    if development:
        logger.info("🔐 Looking for password field...")
    
    try:
        password_field = page.get_by_role("textbox", name="Password Reveal password")
        password_field.wait_for(state="visible", timeout=15000)
        
        if development:
            logger.info("✅ Password field found!")
            logger.info("🖱️ Clicking password field...")
        
        password_field.click()
        page.wait_for_timeout(500)  # Simulate interaction
        
        if development:
            logger.info("⌨️ Typing password...")
        
        password_field.fill(account["password"])
        page.wait_for_timeout(1000)  # Pause after filling password
        
        if development:
            logger.info("🔘 Looking for login submit button...")
        
        # Click login button
        login_submit = page.get_by_test_id("LoginForm_Login_Button")
        login_submit.wait_for(state="visible", timeout=10000)
        
        if development:
            logger.info("🔘 Clicking login submit button...")
        
        login_submit.click()
        page.wait_for_timeout(3000)  # Wait for login to complete
        
        if development:
            logger.info("⏳ Waiting for successful login redirect...")
        
        # Wait for successful login (check for URL change or home page elements)
        page.wait_for_url("**/home", timeout=30000)
        
        if development:
            logger.info("🎉 Login successful! Redirected to home page.")
        
    except Exception as e:
        if development:
            logger.error(f"❌ Error with password field or login: {e}")
            logger.info("🔄 Trying alternative approach...")
        
        print(f"Error with password field or login: {e}")
        # Try alternative approach
        try:
            page.fill('input[name="password"]', account["password"])
            page.click('div[data-testid="LoginForm_Login_Button"]')
            page.wait_for_timeout(5000)
            # Check if we're redirected to home or main page
            if "login" not in page.url:
                if development:
                    logger.info("✅ Login appears successful (alternative method)")
                print("Login appears successful")
            else:
                if development:
                    logger.warning("⚠️ Login may have failed - still on login page")
                print("Login may have failed - still on login page")
        except Exception as e2:
            if development:
                logger.error(f"❌ Alternative password approach also failed: {e2}")
            print(f"Alternative password approach also failed: {e2}")
            raise e2
    
    # Create storage folder if it doesn't exist
    if development:
        logger.info("💾 Preparing to save session data...")
    
    if not os.path.exists('storage'):
        os.makedirs('storage')
        if development:
            logger.info("📁 Created storage directory")

    # Save localStorage and cookies using storage_state
    if development:
        logger.info(f"💾 Saving session state for {account['username']}...")
    
    page.context.storage_state(path=f"storage/{account['username']}_state.json")
    
    if development:
        logger.info("✅ Session state saved successfully!")

    # Update expired_token in account.json (assuming 30 days validity)
    if development:
        logger.info("📝 Updating account expiration token...")
    
    with open('account.json', 'r') as f:
        accounts = json.load(f)
    for acc in accounts:
        if acc['username'] == account['username']:
            acc['expired_token'] = int(time.time()) + 30 * 24 * 3600
            if development:
                logger.info(f"🕒 Token expiration updated for {account['username']}")
            break
    with open('account.json', 'w') as f:
        json.dump(accounts, f, indent=4)

    if development:
        logger.info("🧹 Cleaning up browser resources...")

    # ---------------------
    context.close()
    browser.close()
    
    if development:
        logger.info(f"🎉 Login process completed successfully for {account['username']}!")
        logger.info("─" * 60)


def login_all(headless: bool = True, development: bool = False):
    logger = logging.getLogger(__name__)
    
    if development:
        logger.info("🚀 Starting batch login process...")
        logger.info("═" * 60)
    
    with sync_playwright() as playwright:
        with open('account.json', 'r') as f:
            accounts: list[LoginInfo] = json.load(f)
            
            if development:
                logger.info(f"📋 Found {len(accounts)} accounts to process")
                
            for i, account in enumerate(accounts, 1):
                if development:
                    logger.info(f"👤 Processing account {i}/{len(accounts)}: {account['username']}")
                
                try:
                    login_fn(playwright, account, headless, development)
                    if development:
                        logger.info(f"✅ Account {i}/{len(accounts)} completed successfully")
                except Exception as e:
                    if development:
                        logger.error(f"❌ Account {i}/{len(accounts)} failed: {e}")
                    else:
                        print(f"Login failed for {account['username']}: {e}")
                        
    if development:
        logger.info("🏁 Batch login process completed!")
        logger.info("═" * 60)  
