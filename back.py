from flask import Flask, request, jsonify, render_template
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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

# Scrape Google Patents data
def scrape_google_patents(query):
    chrome_options = Options()
    #chrome_options.add_argument('--headless')
    driver = webdriver.Chrome(service=Service(r'chromedriver.exe'), options=chrome_options)
    results = []
    try:
        for page in range(1, 2):  # Adjust page range as needed
            url = f"https://patents.google.com/?q={query}&oq={query}&page={page}"
            driver.get(url)
            try:
                section = WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'section.style-scope.search-results'))
                )
                result_items = section.find_elements(By.CSS_SELECTOR, 'search-result-item')
                for item in result_items:
                    try:
                        title = item.find_element(By.CSS_SELECTOR, '#htmlContent').text.strip()
                        description = item.find_element(By.CSS_SELECTOR, '#htmlContent').text.strip()
                        patent_id = item.find_element(By.CSS_SELECTOR, '[data-proto="OPEN_PATENT_PDF"]').text.strip()
                        authors = item.find_elements(By.CSS_SELECTOR, '.style-scope.search-result-item')[0].text.strip()
                        patent_url = f"https://patents.google.com/patent/{patent_id}/en"
                        image_url = item.find_element(By.CSS_SELECTOR, 'img').get_attribute('src')  # Update based on your page structure
                        results.append({
                            'title': title,
                            'description': description,
                            'authors': authors,
                            'id': patent_id,
                            'url': patent_url,
                            'image': image_url  # Include the image URL in the result
                        })
                    except Exception as e:
                        print(f"Error extracting patent info: {e}")
                        pass
            except Exception as e:
                print(f"Error finding section: {e}")
                pass
    finally:
        driver.quit()
    return results

# Scrape Espacenet data and map to Google Patents
def scrape_espacenet(query):
    chrome_options = Options()
    #chrome_options.add_argument('--headless')
    driver = webdriver.Chrome(service=Service(r'chromedriver.exe'), options=chrome_options)
    results = []
    try:
        for page in range(1, 2):  # Adjust page range as needed
            url = f"https://worldwide.espacenet.com/patent/search?q={query}&page={page}"
            driver.get(url)
            try:
                items = WebDriverWait(driver, 2).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'article.item--wSceB4di'))
                )
                for item in items:
                    try:
                        title = item.find_element(By.CSS_SELECTOR, 'header.h2--2VrrSjFb').text.strip()
                        description = item.find_element(By.CSS_SELECTOR, '.copy-text--uk738M73').text.strip()
                        patent_id = item.find_element(By.TAG_NAME, 'a').get_attribute('href').split('/')[-1]
                        patent_url = f"https://patents.google.com/patent/{patent_id}/en"
                        # Espacenet doesn't always have images, so we handle it as an optional field
                        image_url = item.find_element(By.CSS_SELECTOR, 'img').get_attribute('src') if item.find_element(By.CSS_SELECTOR, 'img') else None
                        results.append({
                            'title': title,
                            'description': description,
                            'id': patent_id,
                            'url': patent_url,
                            'image': image_url  # Include the image URL in the result if available
                        })
                    except Exception as e:
                        print(f"Error extracting patent info: {e}")
                        pass
            except Exception as e:
                print(f"Error finding items: {e}")
                pass
    finally:
        driver.quit()
    return results

@app.route('/')
def home():
    return render_template('index2end.html')

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    google_results = scrape_google_patents(query)
    espacenet_results = scrape_espacenet(query)
    combined_results = google_results + espacenet_results
    optimized_results = gwo_optimize_results(combined_results, query)

    # Debugging: log the image URLs to ensure they are correct
    for result in optimized_results:
        print(".")

    return jsonify({'results': optimized_results})

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5013)
