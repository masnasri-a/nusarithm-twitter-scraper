import re
import os, json
import time
import logging
import random
from typing import List
from playwright.sync_api import Playwright, expect, sync_playwright

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def scrape_trending(username: str, headless: bool = True, development: bool = False, max_trending: int = 10) -> List[str]:
    """
    Scrape Twitter trending topics and return them as a list.

    Args:
        playwright: Playwright instance
        username: Username for loading saved session
        headless: Whether to run in headless mode
        development: Whether to enable detailed logging
        max_trending: Maximum number of trending topics to collect

    Returns:
        List of trending topic strings
    """
    logger = logging.getLogger(__name__)

    if development:
        logger.info("🔍 Starting Twitter trending topics scraping")
        logger.info(f"🎭 Headless mode: {headless}")
        logger.info(f"📊 Max trending topics: {max_trending}")

    # Check if storage state exists
    storage_path = f"storage/{username}_state.json"
    if not os.path.exists(storage_path):
        error_msg = f"Storage state not found for user {username} at {storage_path}"
        if development:
            logger.error(f"❌ {error_msg}")
        raise FileNotFoundError(error_msg)

    if development:
        logger.info("🌐 Launching browser...")
    with sync_playwright() as playwright: 
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
                logger.info("🌍 Navigating to Twitter explore page...")

            # Navigate to Twitter explore page (where trending topics are shown)
            page.goto("https://x.com/explore")
            page.wait_for_timeout(3000)  # Wait for page to load

            if development:
                logger.info("✅ Explore page loaded successfully")

            # Wait for trending section to load
            if development:
                logger.info("⏳ Waiting for trending section to load...")

            # Wait for trending section - try multiple selectors
            trending_selectors = [
                '[data-testid="trend"]',
                '[aria-label="Timeline: Explore"]',
                'div[data-testid*="trend"]',
                'section[role="region"]'
            ]

            trending_found = False
            for selector in trending_selectors:
                try:
                    page.wait_for_selector(selector, timeout=10000)
                    if development:
                        logger.info(f"✅ Trending section found with selector: {selector}")
                    trending_found = True
                    break
                except:
                    continue

            if not trending_found:
                if development:
                    logger.warning("⚠️ Trending section not found with standard selectors, proceeding anyway...")

            # Initialize variables for scraping
            trending_topics = []

            if development:
                logger.info("🔄 Starting trending topics extraction...")

            # Extract trending topics
            try:
                # Look for trending topic elements
                trend_selectors = [
                    '[data-testid="trend"] span[dir="ltr"]',
                    '[data-testid="trend"] div[dir="ltr"]',
                    'div[data-testid="trend"] span',
                    'div[data-testid="trend"] div[dir="ltr"]'
                ]

                for selector in trend_selectors:
                    try:
                        elements = page.query_selector_all(selector)
                        for element in elements:
                            text = element.text_content().strip()
                            if text and len(text) > 0 and text not in trending_topics:
                                # Filter out common non-trending text
                                if not any(skip in text.lower() for skip in ['trending', 'posts', 'hours ago', 'news', 'entertainment']):
                                    trending_topics.append(text)
                                    if development:
                                        logger.info(f"📝 Found trending topic: {text}")

                        if len(trending_topics) >= max_trending:
                            break

                    except Exception as e:
                        if development:
                            logger.debug(f"Selector {selector} failed: {e}")
                        continue

                # Also try to get trending topics from specific trend elements
                try:
                    trend_elements = page.query_selector_all('[data-testid="trend"]')
                    for trend_element in trend_elements:
                        try:
                            # Look for the main text span within each trend element
                            text_spans = trend_element.query_selector_all('span[dir="ltr"]')
                            for span in text_spans:
                                text = span.text_content().strip()
                                if text and len(text) > 1 and not text.isdigit():
                                    # Skip if it's just numbers or common UI text
                                    if not any(skip in text.lower() for skip in ['trending', 'posts', 'hours ago', 'news', 'entertainment', 'politics', '·']):
                                        if text not in trending_topics:
                                            trending_topics.append(text)
                                            if development:
                                                logger.info(f"📝 Found trending topic: {text}")

                        except Exception as e:
                            if development:
                                logger.debug(f"Error extracting from trend element: {e}")
                            continue

                except Exception as e:
                    if development:
                        logger.debug(f"Error with trend elements: {e}")

            except Exception as e:
                if development:
                    logger.warning(f"⚠️ Error extracting trending topics: {e}")

            # Remove duplicates and limit to max_trending
            trending_topics = list(set(trending_topics))[:max_trending]

            if development:
                logger.info("✅ Trending topics extraction completed!")
                logger.info(f"📊 Total trending topics collected: {len(trending_topics)}")
                for i, topic in enumerate(trending_topics, 1):
                    logger.info(f"  {i:2d}. {topic}")

            return trending_topics

        except Exception as e:
            if development:
                logger.error(f"❌ Error during trending scraping: {e}")
            raise e

        finally:
            if development:
                logger.info("🧹 Cleaning up browser resources...")

            # Clean up
            context.close()
            browser.close()

            if development:
                logger.info("🎉 Trending scraping completed successfully!")
                logger.info("─" * 60)
def create_or_query(trending_topics: List[str]) -> str:
    """
    Create an OR query from trending topics.

    Args:
        trending_topics: List of trending topic strings

    Returns:
        OR query string combining all trending topics
    """
    if not trending_topics:
        return ""

    # Clean and format topics for search
    cleaned_topics = []
    for topic in trending_topics:
        # Remove hashtags if present and clean the text
        clean_topic = topic.strip()
        if clean_topic.startswith('#'):
            clean_topic = clean_topic[1:]
        # Quote topics with spaces
        if ' ' in clean_topic:
            clean_topic = f'"{clean_topic}"'
        cleaned_topics.append(clean_topic)

    # Join with OR operator
    or_query = ' OR '.join(cleaned_topics)
    return or_query


def scrape_trending_and_search(username: str, headless: bool = True, development: bool = False, max_trending: int = 10, max_scrolls: int = 15) -> List[str]:
    """
    Scrape trending topics and then search for posts using those topics.

    Args:
        playwright: Playwright instance
        username: Username for loading saved session
        headless: Whether to run in headless mode
        development: Whether to enable detailed logging
        max_trending: Maximum number of trending topics to collect
        max_scrolls: Maximum number of scrolls for search

    Returns:
        List of post URLs found during search
    """
    logger = logging.getLogger(__name__)

    # First, scrape trending topics
    trending_topics = scrape_trending(username, headless, development, max_trending)

    if not trending_topics:
        logger.warning("⚠️ No trending topics found, cannot perform search")
        return []

    # Create OR query from trending topics
    or_query = create_or_query(trending_topics)

    if development:
        logger.info(f"🔍 Created OR query: {or_query}")

    # Now perform search using the OR query
    from src.scraper.search import search
    return search(
        query=or_query,
        username=username,
        headless=headless,
        development=development,
        max_scrolls=max_scrolls
    )


if __name__ == "__main__":
    print("This module is designed to be used through main.py")
    print("Use: python main.py --scrape-trending [--max-trending=N] [--dev]")
    print("Or:   python main.py --trending-search [--max-trending=N] [--max-scrolls=N] [--dev]")
