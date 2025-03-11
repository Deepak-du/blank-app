import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import pandas as pd
from typing import Dict, List, Tuple
import time
import random

def extract_text_from_url(url: str) -> Tuple[str, List[str]]:
    """Extract text content and links from a URL using requests"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract text content
        paragraphs = [p.get_text(strip=True) for p in soup.find_all(['p', 'h1', 'h2', 'h3', 'article']) 
                     if len(p.get_text(strip=True)) > 20]
        full_text = '\n'.join(paragraphs)

        # Extract links
        links = set()
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            full_link = urljoin(url, href)
            if full_link.startswith(url) and '#' not in full_link:
                links.add(full_link)

        return full_text, list(links)
    except Exception as e:
        raise Exception(f"Error processing URL {url}: {str(e)}")

def process_url(url: str, category: str) -> Dict:
    """Process a single URL and return the results"""
    try:
        time.sleep(random.uniform(1, 3))  # Polite delay between requests
        full_text, links = extract_text_from_url(url)

        result = {
            'url': url,
            'category': category,
            'full_text': full_text[:1000] + '...' if len(full_text) > 1000 else full_text,  # Truncate long text
            'link_count': len(links),
            'status': 'success'
        }
    except Exception as e:
        result = {
            'url': url,
            'category': category,
            'full_text': '',
            'link_count': 0,
            'status': 'error',
            'error_message': str(e)
        }

    return result

def validate_excel_file(file) -> Tuple[bool, str, pd.DataFrame]:
    """Validate the uploaded Excel file"""
    try:
        df = pd.read_excel(file)
        if "URL" not in df.columns or "Category" not in df.columns:
            return False, "Excel file must contain 'URL' and 'Category' columns", None

        # Validate URLs
        invalid_urls = []
        for url in df['URL']:
            if not str(url).startswith(('http://', 'https://')):
                invalid_urls.append(url)

        if invalid_urls:
            return False, f"Invalid URLs found: {', '.join(map(str, invalid_urls[:3]))}", None

        return True, "", df
    except Exception as e:
        return False, f"Error reading Excel file: {str(e)}", None
