import requests
from bs4 import BeautifulSoup
import os

def test_web(url):
    try:
        print(f"Testing URL: {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer"]):
            script.decompose()
            
        text = soup.get_text()
        title = soup.title.string if soup.title else url
        
        print(f"Title: {title}")
        print(f"Text preview: {text.strip()[:100]}...")
        
        # Clean text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = '\n'.join(chunk for chunk in chunks if chunk)
        
        print(f"Clean text length: {len(clean_text)}")
        
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    # Test with a common site
    test_web("https://example.com")
    # Test with a more complex site
    test_web("https://en.wikipedia.org/wiki/Main_Page")
