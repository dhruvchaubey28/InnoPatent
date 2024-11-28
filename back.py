import time
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from flask import Flask, request, jsonify, render_template
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging

app = Flask(__name__, static_folder='static', template_folder='templates')

# Configure logging to suppress unwanted messages
logging.basicConfig(level=logging.ERROR)

# Fitness function to calculate relevance of a result to the target query
def fitness(result, target_query):
    title_score = target_query.lower() in result['title'].lower()
    description_score = target_query.lower() in result['description'].lower()
    return title_score * 2 + description_score

# Grey Wolf Optimization (GWO) to optimize the search results
def gwo_optimize_results(results, target_query):
    wolves = results.copy()
    wolves_fitness = [(wolf, fitness(wolf, target_query)) for wolf in wolves]
    wolves_fitness.sort(key=lambda x: x[1], reverse=True)
    alpha = wolves_fitness[0][0]
    beta = wolves_fitness[1][0] if len(wolves_fitness) > 1 else None
    delta = wolves_fitness[2][0] if len(wolves_fitness) > 2 else None
    rest = [wolf[0] for wolf in wolves_fitness[3:]]
    return [alpha, beta, delta] + rest if beta and delta else [alpha]

def setup_chrome_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    
    # Add user agent to mimic browser
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36')
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.implicitly_wait(2)  # Default wait time
    return driver

def safe_find_element(container, selector_type, selector, default='N/A'):
    try:
        element = container.find_element(selector_type, selector)
        return element.text.strip()
    except NoSuchElementException:
        return default

def scrape_google_patents(query):
    driver = setup_chrome_driver()
    results = []
    
    try:
        url = f"https://patents.google.com/?q={query}&oq={query}"
        driver.get(url)
        
        # Enhanced wait and error handling
        try:
            WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'search-result-item'))
            )
            time.sleep(2)  # Additional buffer for page load
            
            # More generic selectors
            result_items = driver.find_elements(By.CSS_SELECTOR, 'search-result-item')
            
            for item in result_items:
                title = safe_find_element(item, By.XPATH, './/*[contains(@class, "title")]')
                description = safe_find_element(item, By.XPATH, './/*[contains(@class, "description")]')
                patent_id = safe_find_element(item, By.CSS_SELECTOR, '[data-proto="OPEN_PATENT_PDF"]')
                
                result = {
                    'source': 'Google Patents',
                    'title': title,
                    'description': description,
                    'id': patent_id,
                    'url': f"https://patents.google.com/patent/{patent_id}/en" if patent_id != 'N/A' else ''
                }
                
                results.append(result)
        
        except (TimeoutException, WebDriverException) as e:
            print(f"Error scraping Google Patents: {e}")
    
    finally:
        driver.quit()
    
    return results

def scrape_espacenet(query):
    driver = setup_chrome_driver()
    results = []
    
    try:
        url = f"https://worldwide.espacenet.com/patent/search?q={query}"
        driver.get(url)
        
        try:
            WebDriverWait(driver, 3).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'article'))
            )
            time.sleep(2)  # Additional buffer
            
            # More flexible selectors
            result_items = driver.find_elements(By.CSS_SELECTOR, 'article')
            
            for item in result_items:
                title = safe_find_element(item, By.CSS_SELECTOR, 'h2, .title')
                description = safe_find_element(item, By.CSS_SELECTOR, 'p, .description')
                
                try:
                    patent_link = item.find_element(By.TAG_NAME, 'a')
                    patent_url = patent_link.get_attribute('href')
                    patent_id = patent_url.split('/')[-1] if patent_url else 'N/A'
                except NoSuchElementException:
                    patent_url = ''
                    patent_id = 'N/A'
                
                result = {
                    'source': 'Espacenet',
                    'title': title,
                    'description': description,
                    'id': patent_id,
                    'url': patent_url
                }
                
                results.append(result)
        
        except (TimeoutException, WebDriverException) as e:
            print(f"Error scraping Espacenet: {e}")
    
    finally:
        driver.quit()
    
    return results

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    google_results = scrape_google_patents(query)
    espacenet_results = scrape_espacenet(query)
    combined_results = google_results + espacenet_results
    optimized_results = gwo_optimize_results(combined_results, query)

    return jsonify({'results': optimized_results})

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5013)