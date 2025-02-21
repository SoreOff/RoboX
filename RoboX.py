import requests
import sys
import json
from datetime import datetime
import asyncio
import aiohttp
import os
import time

def extract_urls_from_robots(content):
    urls = set()
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith(('Allow:', 'Disallow:', 'Sitemap:')):
            parts = line.split(':', 1)
            if len(parts) > 1:
                url = parts[1].strip()
                if url and url != '/':
                    urls.add(url)
    return urls

async def fetch_robots_content(session, timestamp, url):
    wayback_url = f'http://web.archive.org/web/{timestamp}/{url}'
    try:
        async with session.get(wayback_url, timeout=10) as response:
            if response.status == 200:
                content = await response.text()
                return content
    except:
        pass
    return None

class URLSaver:
    def __init__(self, host):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.txt_filename = f'{host}_urls.txt'
        self.json_filename = f'{host}_urls.json'
        self.all_urls = set()
        self.host = host
        
        if not os.path.exists(self.txt_filename):
            with open(self.txt_filename, 'w') as f:
                f.write(f'# URLs extracted from {host} robots.txt versions\n')
        
        if not os.path.exists(self.json_filename):
            with open(self.json_filename, 'w') as f:
                json.dump({
                    'domain': host,
                    'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'urls': [],
                    'total_processed': 0
                }, f, indent=2)
    
    def save_batch(self, new_urls, processed_count, total_count):
        if not new_urls:
            return
        
        self.all_urls.update(new_urls)
        
        with open(self.txt_filename, 'a') as f:
            for url in sorted(new_urls):
                if url.startswith('/'):
                    url = f'https://{self.host}{url}'
                f.write(f'{url}\n')
        
        with open(self.json_filename, 'r') as f:
            data = json.load(f)
        
        data['urls'] = sorted(list(self.all_urls))
        data['total_processed'] = processed_count
        data['total_urls'] = len(self.all_urls)
        data['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        data['progress'] = f'{processed_count}/{total_count}'
        
        with open(self.json_filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f'[+] Found {len(new_urls)} new URLs (Total unique: {len(self.all_urls)})')
        print(f'[+] Progress: {processed_count}/{total_count} versions processed')

async def get_all_robots_urls(host, batch_size=50):
    url = f'http://web.archive.org/cdx/search/cdx?url={host}/robots.txt&output=json&fl=timestamp,original'
    url_saver = URLSaver(host)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    print(f'[-] Error: Could not fetch archive list')
                    return None
                
                results = await response.json()
                if len(results) <= 1:
                    print('[-] No historical versions found')
                    return None
                
                entries = results[1:]
                total_versions = len(entries)
                print(f'[*] Found {total_versions} historical robots.txt versions')
                
                current_batch_urls = set()
                for i, (timestamp, original_url) in enumerate(entries, 1):
                    content = await fetch_robots_content(session, timestamp, original_url)
                    if content:
                        new_urls = extract_urls_from_robots(content)
                        current_batch_urls.update(new_urls)
                    
                    if i % batch_size == 0 or i == total_versions:
                        url_saver.save_batch(current_batch_urls, i, total_versions)
                        current_batch_urls = set()
                    
                    elif i % 10 == 0:
                        print(f'[*] Processed {i}/{total_versions} versions...')
                
                return url_saver.txt_filename, url_saver.json_filename
                
    except Exception as e:
        print(f'[-] Error: {str(e)}')
        return None

async def main_with_retry(host, batch_size, max_retries=5, retry_delay=10):
    retries = 0
    while retries < max_retries:
        try:
            print(f'\n[*] Attempt {retries + 1} of {max_retries}')
            result = await get_all_robots_urls(host, batch_size)
            
            if result:
                txt_file, json_file = result
                print(f'\n[+] Success! Results saved to:')
                print(f'    - URLs: {txt_file}')
                print(f'    - Detailed info: {json_file}')
                return
            
            print(f'[-] No results found, retrying in {retry_delay} seconds...')
            retries += 1
            if retries < max_retries:
                await asyncio.sleep(retry_delay)
                
        except Exception as e:
            print(f'[-] Error occurred: {str(e)}')
            print(f'[-] Retrying in {retry_delay} seconds...')
            retries += 1
            if retries < max_retries:
                await asyncio.sleep(retry_delay)
    
    print(f'\n[-] Failed after {max_retries} attempts. Please try again later.')

def main():
    if len(sys.argv) not in [2, 3]:
        print('Usage:\n\tpython3 wayback_robots_urls.py <domain> [batch_size]')
        print('Example:\n\tpython3 wayback_robots_urls.py example.com')
        print('\tpython3 wayback_robots_urls.py example.com 100')
        sys.exit(1)
    
    host = sys.argv[1]
    batch_size = int(sys.argv[2]) if len(sys.argv) == 3 else 50
    
    print(f'[*] Starting to fetch robots.txt history for {host}...')
    
    asyncio.run(main_with_retry(host, batch_size))

if __name__ == '__main__':
    main()
