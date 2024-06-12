from flask import Flask, request, jsonify
import csv
import time
import subprocess
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import sys

app = Flask(__name__)

# Path to your webdriver executable
webdriver_path = '/Users/sabbirahmad/Desktop/chromedriver'

# Function to generate the Trustpilot search URL
def generate_trustpilot_url(category, location):
    base_url = 'https://www.trustpilot.com/categories/'
    country_code = 'DE'  # Assuming it's always Germany
    category_formatted = category.lower().replace(' ', '_')
    location_formatted = location.lower().replace(' ', '-')
    return f"{base_url}{category_formatted}?country={country_code}&location={location_formatted}"

# Function to check if pagination element is present and visible
def is_pagination_visible(driver):
    try:
        pagination = driver.find_element(By.XPATH, '//div[@class="styles_paginationWrapper__fukEb styles_pagination__USObu"]/nav[@aria-label="Pagination"]/a[@name="pagination-button-next"]')
        return pagination.is_displayed()
    except:
        return False

# Function to check if pagination button is interactable
def is_pagination_button_interactable(driver):
    try:
        pagination_button = driver.find_element(By.XPATH, '//div[@class="styles_paginationWrapper__fukEb styles_pagination__USObu"]/nav[@aria-label="Pagination"]/a[@name="pagination-button-next"]')
        return pagination_button.is_enabled() and pagination_button.get_attribute("aria-disabled") != "true"
    except:
        return False

# Function to extract business links and names from the current page
def extract_business_links_and_names(driver, business_dict):
    try:
        business_elements = driver.find_elements(By.XPATH, "//div[@class='paper_paper__1PY90 paper_outline__lwsUX card_card__lQWDv card_noPadding__D8PcU styles_wrapper__2JOo2']")
        for business in business_elements:
            try:
                link_element = business.find_element(By.XPATH, './/a[@class="link_internal__7XN06 link_wrapper__5ZJEx styles_linkWrapper__UWs5j"]')
                link = link_element.get_attribute('href')
                name = business.find_element(By.XPATH, './/p[@class="typography_heading-xs__jSwUz typography_appearance-default__AAY17 styles_displayName__GOhL2"]').text
                if name not in business_dict:
                    business_dict[name] = link
                logging.info(f"So far total {len(business_dict)} unique elements Scrapped")
            except Exception as e:
                logging.error(f"Error extracting name and link: {e}")
                continue
    except Exception as e:
        logging.error(f"Error extracting business data: {e}")

# Main function to handle the scraping process
def scrape_trustpilot(category, location):
    # Initialize Chrome web driver with existing user profile
    chrome_options = Options()
    chrome_options.add_argument("/Users/sabbirahmad/Library/Application Support/Google/Chrome/Default")
    service = Service(webdriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    url = generate_trustpilot_url(category, location)
    driver.get(url)

    wait = WebDriverWait(driver, 20)
    try:
        wait.until(EC.presence_of_element_located((By.XPATH, '//div[@class="styles_main__XgQiu"]')))
    except Exception as e:
        logging.error(f"Error waiting for main content to load: {e}")
        driver.quit()
        return []

    all_business_data = {}
    while True:
        extract_business_links_and_names(driver, all_business_data)
        if is_pagination_visible(driver) and is_pagination_button_interactable(driver):
            try:
                pagination_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="styles_paginationWrapper__fukEb styles_pagination__USObu"]/nav[@aria-label="Pagination"]/a[@name="pagination-button-next"]')))
                driver.execute_script("arguments[0].scrollIntoView(true);", pagination_button)
                ActionChains(driver).move_to_element(pagination_button).click().perform()
                time.sleep(10)
            except Exception as e:
                logging.error(f"Error clicking pagination button: {e}")
                break
        else:
            break

    driver.quit()
    return all_business_data

@app.route('/scrape', methods=['GET'])
def scrape():
    category = request.args.get('category')
    location = request.args.get('location')
    if not category or not location:
        return jsonify({'error': 'Category and location parameters are required'}), 400

    business_data = scrape_trustpilot(category, location)
    csv_file_path = f"/Users/sabbirahmad/Trustpilot/{category.replace(' ', '_')}.csv"
    
    try:
        with open(csv_file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Business Name', 'Business Link'])
            for name, link in business_data.items():
                writer.writerow([name, link])
        logging.info(f"Links and names successfully saved to {csv_file_path}")
    except Exception as e:
        logging.error(f"Error saving links and names to CSV: {e}")
        return jsonify({'error': 'Error saving CSV file'}), 500

    try:
        python_executable = sys.executable
        subprocess.run([python_executable, '/Users/sabbirahmad/TrustPilot/details.py', csv_file_path, 'https://www.trustpilot.com', category], check=True)
        logging.info(f"details.py executed successfully with {csv_file_path}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error calling details.py: {e}")
        return jsonify({'error': 'Error executing details.py'}), 500

    return jsonify({'message': 'Scraping completed successfully', 'data': business_data}), 200

if __name__ == '__main__':
    app.run(debug=True)
