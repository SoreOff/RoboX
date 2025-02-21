# RoboX - Wayback Robots URL Extractor

This script retrieves the history of `robots.txt` for a given domain from the Wayback Machine, processes all archived versions, and extracts and saves the URLs found within.

## Features ✨

- Fetches all historical `robots.txt` versions of a domain from the Internet Archive
- Extracts `Allow:`, `Disallow:`, and `Sitemap:` URLs
- Saves extracted links in `txt` and `json` formats
- Utilizes `asyncio` and `aiohttp` for faster processing
- Prevents duplicate file creation and continues using the existing file in case of errors

## Installation 📦

```bash
pip install -r requirements.txt
```

### Requirements

Ensure you have the following installed:

- Python 3.7+
- `aiohttp`
- `requests`

## Usage 🚀

```bash
python3 robox.py <domain> [batch_size]
```

Example:

```bash
python3 robox.py example.com
python3 robox.py example.com 100
```

## Output 📂

- `<domain>_urls_<timestamp>.txt` → Contains a list of extracted URLs
- `<domain>_urls_<timestamp>.json` → Includes additional information such as execution time, total versions processed, and total URLs found

## License ⚖️

This project is licensed under the MIT License.

