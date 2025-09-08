




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

def search(query: str = None, username: str = None, headless: bool = True, development: bool = False, max_scrolls: int = 15) -> List[str]:
    """
    Search Twitter and extract post URLs with natural scrolling behavior.

    Args:
        query: Search query string, if None reads from query.txt
        username: Username for loading saved session
        headless: Whether to run in headless mode
        development: Whether to enable detailed logging
        max_scrolls: Maximum number of scrolls to perform

    Returns:
        List of post URLs found during search
    """
    logger = logging.getLogger(__name__)

    if development:
        logger.info("🔍 Starting Twitter search scraping")
        if query:
            logger.info(f"📝 Search query: {query}")
        else:
            logger.info("📄 Reading query from query.txt")
        logger.info(f"🎭 Headless mode: {headless}")
        logger.info(f"📜 Max scrolls: {max_scrolls}")

    # Construct search URL
    url = None
    if query is None:
        import urllib.parse

        with open('query.txt', 'r') as f:
            query_str = f.read().strip()
        terms = [term.strip() for term in query_str.split(',')]
        search_query = ' or '.join(f'"{term}"' for term in terms)
        query = urllib.parse.quote(search_query)
        url = f'https://x.com/search?q={query}&src=typed_query&f=live'
        if development:
            logger.info(f"📋 Query from file: {query_str}")
            logger.info(f"🔗 Constructed search URL: {url}")
    else:
        import urllib.parse

        query_encoded = urllib.parse.quote(query)
        url = f'https://x.com/search?q={query_encoded}&src=typed_query&f=live'
        if development:
            logger.info(f"🔗 Constructed search URL: {url}")

    # Determine which account to use
    if username is None:
        # Load first account from account.json
        try:
            with open('account.json', 'r') as f:
                accounts = json.load(f)
            if accounts:
                username = accounts[0]['username']
                if development:
                    logger.info(f"👤 Using account: {username}")
            else:
                raise ValueError("No accounts found in account.json")
        except FileNotFoundError:
            raise FileNotFoundError("account.json not found")

    # Check if storage state exists
    storage_path = f"storage/{username}_state.json"
    if not os.path.exists(storage_path):
        error_msg = f"Storage state not found for user {username} at {storage_path}"
        if development:
            logger.error(f"❌ {error_msg}")
        raise FileNotFoundError(error_msg)

    with sync_playwright() as playwright:
        if development:
            logger.info("🌐 Launching browser...")

        # Launch browser with headless support but configured to avoid detection
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

        try:
            if development:
                logger.info("🌍 Navigating to search page...")

            # Navigate to search URL
            page.goto(url)
            page.wait_for_timeout(3000)  # Wait for page to load

            if development:
                logger.info("✅ Search page loaded successfully")

            # Wait for search results to load
            if development:
                logger.info("⏳ Waiting for search results to load...")

            # Wait for search results container
            search_selectors = [
                '[data-testid="primaryColumn"]',
                '[role="main"]',
                'div[data-testid*="search"]',
                'section[role="region"]'
            ]

            results_found = False
            for selector in search_selectors:
                try:
                    page.wait_for_selector(selector, timeout=15000)
                    if development:
                        logger.info(f"✅ Search results found with selector: {selector}")
                    results_found = True
                    break
                except:
                    continue

            if not results_found:
                if development:
                    logger.warning("⚠️ Search results not found with standard selectors, proceeding anyway...")

            # Initialize variables for scraping
            post_urls = set()  # Use set to avoid duplicates
            scroll_count = 0
            last_height = page.evaluate("document.body.scrollHeight")
            consecutive_no_change = 0  # Track consecutive scrolls with no height change
            max_consecutive_no_change = 3  # Stop after 3 consecutive no-change scrolls

            if development:
                logger.info("🔄 Starting natural scrolling process...")

            while scroll_count < max_scrolls:
                scroll_count += 1

                if development:
                    logger.info(f"📜 Scroll {scroll_count}/{max_scrolls}")

                # Extract post URLs before scrolling
                try:
                    # Look for tweet links in search results
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
                    # Random scroll distance (between 600-1200px for search results)
                    scroll_distance = random.randint(600, 1200)

                    if development:
                        logger.info(f"⬇️ Scrolling down by {scroll_distance}px...")

                    # Smooth scroll simulation
                    page.evaluate(f"""
                        window.scrollBy({{
                            top: {scroll_distance},
                            behavior: 'smooth'
                        }});
                    """)

                    # Random pause between scrolls (3-6 seconds for search)
                    pause_time = random.uniform(3, 6)
                    if development:
                        logger.info(f"⏳ Pausing for {pause_time:.1f} seconds...")

                    page.wait_for_timeout(int(pause_time * 1000))

                    # Wait a bit more for content to load
                    page.wait_for_timeout(2000)

                    # Check if we've reached the bottom or no new content
                    current_height = page.evaluate("document.body.scrollHeight")

                    # If height hasn't changed after waiting, increment counter
                    if current_height == last_height:
                        consecutive_no_change += 1
                        if development:
                            logger.info(f"🏁 No height change detected ({consecutive_no_change}/{max_consecutive_no_change})")
                        
                        if consecutive_no_change >= max_consecutive_no_change:
                            if development:
                                logger.info("🏁 Reached end of search results (consecutive no-change scrolls)")
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
            logger.info(f"📋 Cleaned Post IDs: {len(cleaned_post_id)}")
            
            # produce to kafka
            for post_id in cleaned_post_id:
                from src.queue.producer import produce as send_post_ids_to_kafka
                send_post_ids_to_kafka(
                    key=post_id,
                    value={
                        'post_id': post_id,
                        'query': query,
                        'scraped_at': int(time.time())
                    },
                    topic='twitter_post_id'
                )
            return cleaned_post_id

        except Exception as e:
            if development:
                logger.error(f"❌ Error during search scraping: {e}")
            raise e

        finally:
            if development:
                logger.info("🧹 Cleaning up browser resources...")

            # Clean up
            context.close()
            browser.close()

            if development:
                logger.info("🎉 Search scraping completed successfully!")
                logger.info("─" * 60)