import argparse
from src.scraper.login import login_all
from src.scraper.search import search
from src.scraper.trending import scrape_trending, scrape_trending_and_search

from dotenv import load_dotenv
import os

parser = argparse.ArgumentParser(description='Twitter Scraper')
parser.add_argument('--login-all', action='store_true', help='Login to all accounts')
parser.add_argument('--scrape-timeline', action='store_true', help='Scrape timeline for all accounts')
parser.add_argument('--headless', action='store_true', default=True, help='Run browser in headless mode (default: True)')
parser.add_argument('--no-headless', action='store_true', help='Run browser with GUI (overrides --headless)')
parser.add_argument('--search', type=str, help='Search query')
parser.add_argument('--search-from-file', action='store_true', help='Search using queries from query.txt')
parser.add_argument('--kafka', action='store_true', help='Send results to Kafka')
parser.add_argument('--max-scrolls', type=int, default=15, help='Maximum number of scrolls for timeline scraping (default: 15)')
parser.add_argument('--enrich-details', action='store_true', help='Enrich tweet details from tweet IDs')
parser.add_argument('--scrape-trending', action='store_true', help='Scrape trending topics from Twitter')
parser.add_argument('--trending-search', action='store_true', help='Scrape trending topics and search for posts using them')
parser.add_argument('--max-trending', type=int, default=10, help='Maximum number of trending topics to collect (default: 10)')

if __name__ == "__main__":
    load_dotenv()
    mode = os.getenv('MODE', 'production')
    development = mode.lower() == 'development'

    args = parser.parse_args()

    if args.login_all:
        # Determine headless mode
        headless = args.headless and not args.no_headless
        login_all(headless=headless, development=development)

    if args.scrape_trending:
        # Determine headless mode
        headless = args.headless and not args.no_headless
        from playwright.sync_api import sync_playwright

        topics = scrape_trending(
            username="kencingberdiri2",
            headless=headless,
            development=development,
            max_trending=args.max_trending
        )
        print(f"📊 Found {len(topics)} trending topics:")
        for i, topic in enumerate(topics, 1):
            print(f"  {i:2d}. {topic}")

    if args.trending_search:
        # Determine headless mode
        headless = args.headless and not args.no_headless

        # with sync_playwright() as playwright:
        post_ids = scrape_trending_and_search(
            username="makkohijauehe",
            headless=headless,
            development=development,
            max_trending=args.max_trending,
            max_scrolls=args.max_scrolls
        )

    if args.search_from_file or args.search:
        q = None
        if args.search:
            q = args.search
        # Determine headless mode
        headless = args.headless and not args.no_headless
        search(
            query=q,
            headless=headless,
            username="kencingberdiri2",
            development=development,
            max_scrolls=args.max_scrolls,
        )

    if args.enrich_details:
        from src.enrichment.detail_post import start_enrich_detail
        start_enrich_detail()