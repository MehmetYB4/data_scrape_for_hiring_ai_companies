import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import argparse
import os
from urllib.parse import urljoin, urlparse

# Base URL
BASE_URL = "https://turkiye.ai/girisimler/"

# Headers to mimic a browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def get_soup(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        return BeautifulSoup(response.content, "html.parser")
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def extract_emails(text):
    # Regex for email extraction
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return list(set(re.findall(email_pattern, text)))

def extract_phones(text):
    # Basic regex for phone extraction (Turkish formats mostly)
    # Matches: +90 555 555 55 55, 0212 222 22 22, 05555555555, etc.
    phone_pattern = r'(?:\+90|0)\s*[1-9][0-9]{2}\s*[0-9]{3}\s*[0-9]{2}\s*[0-9]{2}'
    return list(set(re.findall(phone_pattern, text)))

def scrape_company_details(detail_url):
    soup = get_soup(detail_url)
    if not soup:
        return None

    # 1. Company Name
    # Try og:title first as it seems more reliable in raw HTML
    name_tag = soup.find("meta", property="og:title")
    if name_tag and name_tag.get("content"):
        company_name = name_tag.get("content").split(" |")[0].strip()
    else:
        # Fallback to h1
        h1_tag = soup.select_one("h1.entry-title")
        company_name = h1_tag.get_text(strip=True) if h1_tag else "Unknown"

    # 2. Website URL
    # Based on inspection: a.box-button with text "Siteye Git"
    website_url = None
    for a in soup.select("a.box-button"):
        if "Siteye Git" in a.get_text():
            website_url = a.get("href")
            break
    
    if not website_url:

        pass

    print(f"  Found: {company_name} - {website_url}")
    
    email = None
    phone = None
    
    if website_url:
        try:
            print(f"    Visiting external site: {website_url}")
            site_soup = get_soup(website_url)
            
            if site_soup:
                text_content = site_soup.get_text()
                
                # Search in homepage
                emails = extract_emails(text_content)
                phones = extract_phones(text_content)
                
                if not emails or not phones:
                    contact_links = []
                    for link in site_soup.find_all('a', href=True):
                        href = link['href']
                        if any(x in href.lower() for x in ['iletisim', 'contact', 'bize-ulasin']):
                            full_contact_url = urljoin(website_url, href)
                            contact_links.append(full_contact_url)
                    
                    for contact_url in list(set(contact_links))[:2]: # Check max 2 contact pages
                        print(f"    Checking contact page: {contact_url}")
                        contact_soup = get_soup(contact_url)
                        if contact_soup:
                            contact_text = contact_soup.get_text()
                            if not emails:
                                emails = extract_emails(contact_text)
                            if not phones:
                                phones = extract_phones(contact_text)
                
                email = ", ".join(emails) if emails else "Not Found"
                phone = ", ".join(phones) if phones else "Not Found"
                
        except Exception as e:
            print(f"    Error visiting external site: {e}")
            email = "Error"
            phone = "Error"
    else:
        email = "No Website"
        phone = "No Website"

    return {
        "Company Name": company_name,
        "Website": website_url,
        "Email": email,
        "Phone": phone,
        "Source URL": detail_url
    }

def main():
    parser = argparse.ArgumentParser(description="Scrape turkiye.ai companies")
    parser.add_argument("--limit", type=int, help="Limit number of companies to scrape for testing", default=None)
    parser.add_argument("--pages", type=int, help="Number of pages to scrape", default=12)
    args = parser.parse_args()

    all_companies = []
    company_count = 0
    
    # Output file
    output_file = "companies.csv"
    
    # Check if file exists to append or create new
    if os.path.exists(output_file):
        pass

    print(f"Starting scrape for {args.pages} pages...")

    for page in range(1, args.pages + 1):
        if args.limit and company_count >= args.limit:
            break
            
        page_url = BASE_URL if page == 1 else f"{BASE_URL}page/{page}/"
        print(f"Scraping Page {page}: {page_url}")
        
        soup = get_soup(page_url)
        if not soup:
            continue
            

        links = soup.select("a.post-thumbnail-rollover")
        
        for link in links:
            if args.limit and company_count >= args.limit:
                break
                
            detail_url = link.get("href")
            print(f"Processing company {company_count + 1}: {detail_url}")
            
            data = scrape_company_details(detail_url)
            if data:
                all_companies.append(data)
                
                df = pd.DataFrame(all_companies)
                df.to_csv(output_file, index=False, encoding="utf-8-sig")
                
            company_count += 1
            time.sleep(1) # Be polite

    print(f"Scraping completed. Found {len(all_companies)} companies.")
    print(f"Saved to {output_file}")

if __name__ == "__main__":
    main()
