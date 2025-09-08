# Twitter Scraper with Kafka Integration

A comprehensive Twitter scraping tool that extracts post URLs and IDs with natural scrolling behavior, featuring Kafka integration for data streaming.

## Features

- ✅ **Natural Scrolling**: Mimics human behavior to avoid detection
- ✅ **Headless Support**: Runs in background with anti-detection measures
- ✅ **Kafka Integration**: Stream scraped data to Kafka topics
- ✅ **Post ID Extraction**: Automatically extracts clean post IDs from URLs
- ✅ **Detailed Logging**: Step-by-step progress tracking
- ✅ **Multiple Data Sources**: Search results and timeline scraping

## Prerequisites

- Python 3.8+
- Playwright
- Kafka broker
- Twitter account with stored session

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
playwright install
```

2. Configure environment:
```bash
# Copy and edit .env file
cp .env.example .env
```

Edit `.env`:
```env
MODE=development  # or production
KAFKA_BROKER=192.168.8.187:9092  # Your Kafka broker address
```

3. Set up Kafka:
```bash
python3 setup_kafka.py
```

## Usage

### Basic Commands

```bash
# Login to all accounts
python3 main.py --login-all

# Search with specific query
python3 main.py --search "python programming"

# Search using queries from query.txt
python3 main.py --search-from-file

# Scrape timeline for all accounts
python3 main.py --scrape-timeline
```

## Kafka Integration

### Connection Behavior
When connecting to Kafka, you may see logs showing connection attempts to `localhost:9092` even when your `KAFKA_BROKER` is set to a different address. This is **normal behavior**:

- ✅ **Successful connection** to your configured broker (`192.168.8.187:9092`)
- ⚠️ **Connection attempts** to `localhost:9092` (discovered from cluster metadata)
- This happens because Kafka shares information about all brokers in the cluster

The connection will work fine as long as your primary broker is accessible.

### Setup
```bash
# Test Kafka connection and create topics
python3 setup_kafka.py
```

### Usage with Kafka
```bash
# Search and send results to Kafka
python3 main.py --search "python programming" --kafka

# Search from file with Kafka output
python3 main.py --search-from-file --kafka

# Timeline scraping with Kafka
python3 main.py --scrape-timeline --kafka
```

### Advanced Options

```bash
# Run in GUI mode (non-headless)
python3 main.py --search "query" --no-headless

# Limit scroll count
python3 main.py --search "query" --max-scrolls 5

# Enable development logging
# (set MODE=development in .env or use --dev flag if available)
```

## Kafka Topics

The scraper creates and uses these Kafka topics:

- **`twitter-posts`**: General post data
- **`twitter-search-results`**: Search-specific results with query metadata
- **`twitter-timeline`**: Timeline data with user information

### Message Format

Each Kafka message contains:

```json
{
  "metadata": {
    "timestamp": "2025-09-08T12:34:56.789012",
    "source": "twitter-scraper",
    "data_type": "post_ids",
    "count": 10,
    "query": "python programming",
    "account": "username"
  },
  "post_id": "1964739523142955142",
  "sequence": 1
}
```

## Configuration Files

### accounts.json
```json
[
  {
    "username": "your_username",
    "password": "your_password",
    "expired_token": 1735689600
  }
]
```

### query.txt
```
python programming
machine learning
artificial intelligence
```

### .env
```env
MODE=development
KAFKA_BROKER=192.168.8.187:9092
```

## Output Files

The scraper generates timestamped output files:

- `search_results_{query}_{timestamp}.txt`: Search results
- `timeline_urls_{username}_{timestamp}.txt`: Timeline data

Each file contains:
- Full URLs with analytics/photo variants
- Clean post IDs (deduplicated)
- Metadata and statistics

## Architecture

```
src/
├── config/
│   └── kafka.py          # Kafka configuration
├── queue/
│   └── producer.py       # Kafka producer
├── login.py              # Twitter authentication
├── search.py             # Search functionality
└── scraper.py            # Timeline scraping
```

## Anti-Detection Measures

- Realistic browser fingerprints
- Natural scrolling patterns
- Randomized delays
- Webdriver property removal
- Plugin and language mocking

## Error Handling

- Comprehensive logging
- Graceful failure recovery
- Kafka connection validation
- Automatic retries for network issues

## Development

Enable detailed logging by setting `MODE=development` in `.env`:

```bash
export MODE=development
python3 main.py --search "query" --kafka
```

## Troubleshooting

### Kafka Connection Issues
```bash
# Test Kafka connection
python3 setup_kafka.py
```

### Browser Issues
```bash
# Reinstall browsers
playwright install
```

### Session Issues
```bash
# Re-login to accounts
python3 main.py --login-all
```

## License

This project is for educational purposes only. Please respect Twitter's Terms of Service and robots.txt.
