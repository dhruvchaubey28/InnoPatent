from flask import Flask, request, jsonify, render_template
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
app = Flask(__name__)
# Global list to store input data
search_queries = []

def scrape_data(query):
    """Scrape patent data from multiple pages based on the query."""
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Run in headless mode
    chrome_options.add_argument('--disable-gpu')

    # Path to chromedriver
    driver = webdriver.Chrome(service=Service(r'C:\Users\Arnav\DSA\.vscode\.vscode\EDGE 2024\pattern\minor1\app\chromedriver.exe'), options=chrome_options)
    
    results = []
    try:
        for page in range(1, 3):  # Loop through pages 1 to 2 (adjust page range as needed)
            url = f"https://patents.google.com/?q={query}&oq={query}&page={page}"
            driver.get(url)
            
            # Wait until the section containing results is fully loaded
            try:
                section = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'section.style-scope.search-results'))
                )
                
                # Extract all the search-result-item elements inside the section
                result_items = section.find_elements(By.CSS_SELECTOR, 'search-result-item')
                
                if not result_items:
                    print(f"No results found on page {page}.")
                
                # Extract title, authors, description (from htmlContent), patent ID, image, and link
                for item in result_items:
                    try:
                        # Extract the title (htmlContent)
                        title_element = item.find_element(By.CSS_SELECTOR, '#htmlContent')
                        title = title_element.text.strip() if title_element else 'No title'

                        # Extract description (content inside <span id="htmlContent">)
                        description_element = item.find_element(By.CSS_SELECTOR, '#htmlContent')
                        description = description_element.text.strip() if description_element else 'No description available'

                        # Extract authors (if available)
                        authors = ""
                        authors_element = item.find_elements(By.CSS_SELECTOR, '.style-scope.search-result-item')
                        if authors_element:
                            authors = authors_element[0].text.strip()

                        # Extract the patent unique ID (for the URL redirect)
                        patent_id_element = item.find_element(By.CSS_SELECTOR, '[data-proto="OPEN_PATENT_PDF"]')
                        patent_id = patent_id_element.text.strip() if patent_id_element else 'No patent ID'

                        # Extract the link of the patent (redirect to the full patent page)
                        patent_link_element = item.find_element(By.TAG_NAME, 'a')
                        patent_url = patent_link_element.get_attribute('href') if patent_link_element else None

                        # Extract the patent image (if available)
                        image_element = item.find_elements(By.CSS_SELECTOR, 'img')
                        image_url = image_element[0].get_attribute('src') if image_element else None

                        # Store title, description, patent ID, image, and link as a dictionary
                        results.append({
                            'title': title, 
                            'description': description,
                            'authors': authors, 
                            'id': patent_id, 
                            'image': image_url, 
                            'url': patent_url
                        })
                    except Exception as e:
                        print(f"Error extracting data from item: {e}")
            
            except Exception as e:
                print(f"Error loading results for page {page}: {e}")
    
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        driver.quit()
    
    return results

@app.route('/')
def home():
    """Serve the frontend HTML."""
    return render_template('index.html')

@app.route('/search', methods=['GET'])
def search():
    """Handle search requests from the frontend and store query in list."""
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400
    
    # Store the query in the list
    search_queries.append(query)

    # Perform scraping with the query
    results = scrape_data(query)
    
    # Include the list of all search queries at the end of the response
    return jsonify({
        'results': results,
        'queries': search_queries
    })

@app.route('/queries', methods=['GET'])
def get_queries():
    """Return all stored queries."""
    return jsonify(search_queries)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5009)
