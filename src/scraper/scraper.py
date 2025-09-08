import re
import re
import os, json
import time
import logging
import random
from typing import List
from playwright.sync_api import Playwright, sync_playwright, expect

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def scrape_timeline(playwright: Playwright, username: str, headless: bool = True, development: bool = False, max_scrolls: int = 15) -> List[str]:
    """
    Scrape Twitter timeline and extract post URLs with natural scrolling behavior.

    Args:
        playwright: Playwright instance
        username: Username for loading saved session
        headless: Whether to run in headless mode
        development: Whether to enable detailed logging
        max_scrolls: Maximum number of scrolls to perform

    Returns:
        List of post URLs found during scraping
    """
    logger = logging.getLogger(__name__)

    if development:
        logger.info(f"🚀 Starting timeline scraping for user: {username}")
        logger.info(f"🎭 Headless mode: {headless}")
        logger.info(f"📜 Max scrolls: {max_scrolls}")

    # Check if storage state exists
    storage_path = f"storage/{username}_state.json"
    if not os.path.exists(storage_path):
        error_msg = f"Storage state not found for user {username} at {storage_path}"
        if development:
            logger.error(f"❌ {error_msg}")
        raise FileNotFoundError(error_msg)

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
        permissions=['geolocation'],
        storage_state=storage_path  # Load saved session
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

    page = context.new_page()

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
        logger.info("🌍 Navigating to Twitter home...")

    try:
        # Navigate to Twitter home
        page.goto("https://x.com/home")
        page.wait_for_timeout(3000)  # Wait for page to load

        if development:
            logger.info("✅ Home page loaded successfully")

        # Wait for timeline to load
        if development:
            logger.info("⏳ Waiting for timeline to load...")

        # Wait for timeline container - try multiple selectors
        timeline_selectors = [
            '[data-testid="primaryColumn"]',
            '[role="main"]',
            'div[data-testid*="timeline"]',
            '.timeline',
            'section[role="region"]'
        ]

        timeline_found = False
        for selector in timeline_selectors:
            try:
                page.wait_for_selector(selector, timeout=10000)
                if development:
                    logger.info(f"✅ Timeline found with selector: {selector}")
                timeline_found = True
                break
            except:
                continue

        if not timeline_found:
            if development:
                logger.warning("⚠️ Timeline not found with standard selectors, proceeding anyway...")

            # Initialize variables for scraping
            post_urls = set()  # Use set to avoid duplicates
            scroll_count = 0
            last_height = page.evaluate("document.body.scrollHeight")
            consecutive_no_change = 0  # Track consecutive scrolls with no height change
            max_consecutive_no_change = 3  # Stop after 3 consecutive no-change scrolls        if development:
            logger.info("🔄 Starting natural scrolling process...")

        while scroll_count < max_scrolls:
            scroll_count += 1

            if development:
                logger.info(f"📜 Scroll {scroll_count}/{max_scrolls}")

            # Extract post URLs before scrolling
            try:
                # Look for tweet links using multiple selectors
                tweet_selectors = [
                    'article[data-testid="tweet"] a[href*="/status/"]',
                    'div[data-testid="Tweet-User-Text"] a[href*="/status/"]',
                    'a[href*="/status/"][role="link"]',
                    'article a[href*="/status/"]'
                ]

                urls_found_this_scroll = 0

                for selector in tweet_selectors:
                    try:
                        elements = page.query_selector_all(selector)
                        for element in elements:
                            href = element.get_attribute('href')
                            if href and '/status/' in href:
                                # Convert relative URLs to absolute
                                if href.startswith('/'):
                                    full_url = f"https://x.com{href}"
                                else:
                                    full_url = href

                                # Only add if it's a valid tweet URL
                                if full_url not in post_urls:
                                    post_urls.add(full_url)
                                    urls_found_this_scroll += 1

                    except Exception as e:
                        if development:
                            logger.debug(f"Selector {selector} failed: {e}")
                        continue

                if development:
                    logger.info(f"🔗 Found {urls_found_this_scroll} new URLs this scroll (total: {len(post_urls)})")

            except Exception as e:
                if development:
                    logger.warning(f"⚠️ Error extracting URLs on scroll {scroll_count}: {e}")

            # Natural scrolling behavior
            if scroll_count < max_scrolls:
                # Random scroll distance (between 500-1000px)
                scroll_distance = random.randint(500, 1000)

                if development:
                    logger.info(f"⬇️ Scrolling down by {scroll_distance}px...")

                # Smooth scroll simulation
                page.evaluate(f"""
                    window.scrollBy({{
                        top: {scroll_distance},
                        behavior: 'smooth'
                    }});
                """)

                # Random pause between scrolls (2-5 seconds)
                pause_time = random.uniform(2, 5)
                if development:
                    logger.info(f"⏳ Pausing for {pause_time:.1f} seconds...")

                page.wait_for_timeout(int(pause_time * 1000))

                # Wait a bit more for content to load
                page.wait_for_timeout(2000)

                # Check if we've reached the bottom
                current_height = page.evaluate("document.body.scrollHeight")
                if current_height == last_height:
                    consecutive_no_change += 1
                    if development:
                        logger.info(f"🏁 No height change detected ({consecutive_no_change}/{max_consecutive_no_change})")
                    
                    if consecutive_no_change >= max_consecutive_no_change:
                        if development:
                            logger.info("🏁 Reached end of timeline (consecutive no-change scrolls)")
                        break
                else:
                    consecutive_no_change = 0  # Reset counter if height changed

                last_height = current_height

                # Additional check: if we've scrolled many times without new content
                # This prevents infinite scrolling on pages with dynamic content
                if scroll_count >= 5 and len(post_urls) == 0:
                    if development:
                        logger.warning("⚠️ No URLs found after 5 scrolls, stopping to prevent infinite loop")
                    break

        if development:
            logger.info("✅ Scrolling completed!")
            logger.info(f"📊 Total unique post URLs collected: {len(post_urls)}")

        # Convert set to sorted list for consistent output
        post_urls_list = sorted(list(post_urls))

        # Extract clean post IDs from URLs (remove duplicates)
        cleaned_post_id = set()
        for url in post_urls_list:
            # Extract post ID from URL pattern: /status/{id}
            match = re.search(r'/status/(\d+)', url)
            if match:
                post_id = match.group(1)
                cleaned_post_id.add(post_id)

        # Convert to sorted list
        cleaned_post_id = sorted(list(cleaned_post_id))

        if development:
            logger.info("📋 Post URLs found:")
            for i, url in enumerate(post_urls_list, 1):
                logger.info(f"  {i:2d}. {url}")
            
            logger.info("🧹 Cleaned Post IDs:")
            for i, post_id in enumerate(cleaned_post_id, 1):
                logger.info(f"  {i:2d}. {post_id}")

        # Save results to file
        if development:
            logger.info("💾 Saving results to file...")

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_file = f"timeline_urls_{username}_{timestamp}.txt"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# Twitter Timeline URLs - {username}\n")
            f.write(f"# Scraped on: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Total URLs: {len(post_urls_list)}\n")
            f.write(f"# Total Clean Post IDs: {len(cleaned_post_id)}\n")
            f.write("#" + "="*50 + "\n\n")
            
            f.write("## FULL URLs:\n")
            for url in post_urls_list:
                f.write(f"{url}\n")
            
            f.write("\n## CLEAN POST IDs:\n")
            for post_id in cleaned_post_id:
                f.write(f"{post_id}\n")

        if development:
            logger.info(f"✅ Results saved to: {output_file}")
            logger.info(f"📊 Summary: {len(post_urls_list)} URLs, {len(cleaned_post_id)} unique post IDs")

    except Exception as e:
        if development:
            logger.error(f"❌ Error during timeline scraping: {e}")
        raise e

    finally:
        if development:
            logger.info("🧹 Cleaning up browser resources...")

        # Clean up
        context.close()
        browser.close()

        if development:
            logger.info(f"🎉 Timeline scraping completed successfully for {username}!")
            logger.info("─" * 60)

    return cleaned_post_id


def scrape_all_timelines(headless: bool = True, development: bool = False, max_scrolls: int = 15):
    """
    Scrape timelines for all accounts in account.json
    """
    logger = logging.getLogger(__name__)

    if development:
        logger.info("🚀 Starting batch timeline scraping...")
        logger.info("═" * 60)

    # Load accounts
    try:
        with open('account.json', 'r') as f:
            accounts = json.load(f)
    except FileNotFoundError:
        error_msg = "account.json not found. Please ensure it exists with account information."
        if development:
            logger.error(f"❌ {error_msg}")
        raise FileNotFoundError(error_msg)

    if development:
        logger.info(f"📋 Found {len(accounts)} accounts to process")

    all_results = {}

    with sync_playwright() as playwright:
        for i, account in enumerate(accounts, 1):
            username = account['username']

            if development:
                logger.info(f"👤 Processing account {i}/{len(accounts)}: {username}")

            try:
                urls = scrape_timeline(
                    playwright=playwright,
                    username=username,
                    headless=headless,
                    development=development,
                    max_scrolls=max_scrolls
                )

                all_results[username] = urls

                if development:
                    logger.info(f"✅ Account {i}/{len(accounts)} completed successfully - {len(urls)} URLs")

            except Exception as e:
                if development:
                    logger.error(f"❌ Account {i}/{len(accounts)} failed: {e}")
                else:
                    print(f"Timeline scraping failed for {username}: {e}")

                all_results[username] = []

    if development:
        logger.info("🏁 Batch timeline scraping completed!")
        logger.info("═" * 60)

        # Summary
        total_urls = sum(len(urls) for urls in all_results.values())
        logger.info(f"📊 Summary: {len(all_results)} accounts processed, {total_urls} total URLs collected")

    return all_results


if __name__ == "__main__":
    # Example usage
    import sys

    if len(sys.argv) > 1:
        username = sys.argv[1]
        development = "--dev" in sys.argv
        headless = "--no-headless" not in sys.argv

        with sync_playwright() as playwright:
            urls = scrape_timeline(playwright, username, headless, development)
            print(f"Found {len(urls)} post URLs")
    else:
        print("Usage: python scraper.py <username> [--dev] [--no-headless]")
