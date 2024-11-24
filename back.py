from flask import Flask, request, jsonify, render_template
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import random
import logging
app = Flask(__name__, static_folder='static', template_folder='templates')
    # Configure logging to suppress unwanted messages
logging.basicConfig(level=logging.ERROR)  # This will suppress most logs (set to WARNING/ERROR)
    # Fitness function to calculate relevance of a result to the target query
def fitness(result, target_query):
    title_score = target_query.lower() in result['title'].lower()  # Check if the query is in the title
    description_score = target_query.lower() in result['description'].lower()  # Check if the query is in the description
    return title_score * 2 + description_score  # Title is more important
    # Grey Wolf Optimization (GWO) to optimize the search results
def gwo_optimize_results(results, target_query):
    wolves = results.copy()  # Copy results as wolves
    wolves_fitness = [(wolf, fitness(wolf, target_query)) for wolf in wolves]
    wolves_fitness.sort(key=lambda x: x[1], reverse=True)
    alpha = wolves_fitness[0][0]
    beta = wolves_fitness[1][0]
    delta = wolves_fitness[2][0]
    rest = [wolf[0] for wolf in wolves_fitness[3:]]
    return [alpha, beta, delta] + rest
    # Function to scrape patent data
def scrape_data(query):
    """Scrape patent data from multiple pages based on the query."""
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Run in headless mode
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--log-level=3')  # Suppress logs
    # Initialize a new WebDriver for each query
    driver = webdriver.Chrome(service=Service(r'chromedriver.exe'), options=chrome_options)
    results = []
    try:
        for page in range(1, 2):                           # Loop through pages (adjust page range as needed)
            url = f"https://patents.google.com/?q={query}&oq={query}&page={page}"
            driver.get(url)                                # Wait until the section containing results is fully loaded
            try:
                section = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR,'section.style-scope.search-results'))
                )
                result_items = section.find_elements(By.CSS_SELECTOR, 'search-result-item')
                for item in result_items:
                    try:
                        title_element = item.find_element(By.CSS_SELECTOR, '#htmlContent')
                        title = title_element.text.strip() if title_element else 'No title'
                        description_element = item.find_element(By.CSS_SELECTOR, '#htmlContent')
                        description = description_element.text.strip() if description_element else 'No description available'
                        authors = ""
                        authors_element = item.find_elements(By.CSS_SELECTOR, '.style-scope.search-result-item')
                        if authors_element:
                            authors = authors_element[0].text.strip()
                        patent_id_element = item.find_element(By.CSS_SELECTOR, '[data-proto="OPEN_PATENT_PDF"]')
                        patent_id = patent_id_element.text.strip() if patent_id_element else 'No patent ID'
                        patent_link_element = item.find_element(By.TAG_NAME, 'a')
                        patent_url = patent_link_element.get_attribute('href') if patent_link_element else None
                        image_element = item.find_elements(By.CSS_SELECTOR, 'img')
                        image_url = image_element[0].get_attribute('src') if image_element else None
                        results.append({
                            'title': title, 
                            'description': description,
                            'authors': authors, 
                            'id': patent_id, 
                            'image': image_url, 
                            'url': patent_url
                        })
                    except Exception as e:
                        pass                          # Silently ignore errors
            except Exception as e:
                pass                             # Silently ignore errors
    except Exception as e:
        pass                                 # Silently ignore errors
    finally:
        driver.quit()                             # Close the WebDriver once scraping is complete
    if results:
        results = gwo_optimize_results(results, query)    # 
    return results
@app.route('/')
def home():
    return render_template('index.html')
@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400
    results = scrape_data(query)
    return jsonify({
        'results': results
    })
if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5013)
