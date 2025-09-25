# src/tools/lawyer_finder_tool.py

import requests
from bs4 import BeautifulSoup
from langchain.tools import tool
import re
from typing import Dict, Any

@tool
def find_lawyer(query: str) -> str:
    """
    Finds lawyers by performing a live search on the PathLegal Sri Lanka directory.
    Use this tool ONLY when a user explicitly asks to find or recommend a lawyer.
    
    Input should be a description like: "Find family law lawyers in Colombo" or "Employment lawyers in Galle"
    The tool will extract the specialty and location from the query.
    """
    # Parse the query to extract specialty and location
    specialty = "General Practice"  # Default
    location = "Colombo"  # Default
    
    try:
        query = str(query).lower()
        
        # Extract specialty from common legal terms
        if any(term in query for term in ['family', 'divorce', 'custody', 'marriage']):
            specialty = "Family Law"
        elif any(term in query for term in ['employment', 'labor', 'workplace', 'job']):
            specialty = "Employment Law"
        elif any(term in query for term in ['criminal', 'crime', 'defense']):
            specialty = "Criminal Law"
        elif any(term in query for term in ['property', 'real estate', 'land']):
            specialty = "Property Law"
        elif any(term in query for term in ['business', 'corporate', 'company']):
            specialty = "Corporate Law"
        elif any(term in query for term in ['personal injury', 'accident', 'negligence']):
            specialty = "Personal Injury"
        
        # Extract location from common Sri Lankan cities
        if any(city in query for city in ['colombo']):
            location = "Colombo"
        elif any(city in query for city in ['kandy']):
            location = "Kandy"
        elif any(city in query for city in ['galle']):
            location = "Galle"
        elif any(city in query for city in ['jaffna']):
            location = "Jaffna"
        elif any(city in query for city in ['negombo']):
            location = "Negombo"
        elif any(city in query for city in ['matara']):
            location = "Matara"
            
    except Exception as e:
        print(f"Query parsing error: {e}, using defaults")
    
    print(f"--- 🌐 Executing Live Lawyer Search for: '{specialty}' in '{location}' ---")

    try:
        # Step 1: Format the specialty into the URL format used by PathLegal
        # Example: "Family Law" becomes "Family-Attorneys-Sri_Lanka-"
        formatted_specialty = specialty.replace(" ", "-") + "-Attorneys-Sri_Lanka-"
        base_url = f"https://lk.pathlegal.com/{formatted_specialty}/"
        
        current_url = base_url
        all_results = []
        page_count = 1

        while current_url and page_count <= 5: # Limit to 5 pages to be respectful
            print(f"Scraping page {page_count}: {current_url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(current_url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Find all lawyer listing cards on the page
            lawyer_cards = soup.find_all('div', class_='section01', itemscope=True, itemtype="https://schema.org/Attorney")

            for card in lawyer_cards:
                # Extract location from the 'addressLocality' itemprop
                loc_tag = card.find('span', itemprop='addressLocality')
                lawyer_location = loc_tag.get_text(strip=True) if loc_tag else ""
                
                # Filter by the requested location
                if location.lower() in lawyer_location.lower():
                    name_tag = card.find('span', class_='name')
                    name = name_tag.get_text(strip=True) if name_tag else "Name not found"
                    
                    # Find the specializations text
                    spec_span = card.find('span', string=re.compile(r'Specializations:\s*'))
                    specializations = "N/A"
                    if spec_span and spec_span.parent:
                        specializations = spec_span.parent.get_text(strip=True).replace("Specializations:", "").strip()

                    all_results.append(f"Name: {name}, Location: {lawyer_location}, Specializations: {specializations}")

            # Find the 'Next' link to go to the next page
            next_link = soup.find('a', string='Next')
            if next_link and next_link.has_attr('href'):
                # Make sure the URL is absolute
                next_page_path = next_link['href']
                if next_page_path.startswith('/'):
                    current_url = "https://lk.pathlegal.com" + next_page_path
                else:
                    current_url = next_page_path
                page_count += 1
            else:
                # No 'Next' link found, so we're done
                current_url = None

        if not all_results:
            return f"No lawyers were found for '{specialty}' in '{location}' after searching the directory."
        
        return "Found the following lawyers from a live web search:\n" + "\n".join(all_results)

    except requests.exceptions.RequestException as e:
        return f"Error: Could not connect to the lawyer directory website. Details: {e}"
    except Exception as e:
        return f"An unexpected error occurred while scraping for lawyers: {e}"