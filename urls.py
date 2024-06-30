import csv
import time
import subprocess
import urllib.parse
import sys
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

# Path to your webdriver executable
webdriver_path = '/Users/apple/developments/chromedriver-mac-x64/chromedriver'

# Function to generate the Trustpilot search URL
def generate_trustpilot_url(category, location):
    base_url = 'https://www.trustpilot.com/categories/'
    country_code = 'DE'  # Assuming it's always Germany
    category_formatted = category.lower().replace(' ', '_')
    location_formatted = location.lower().replace(' ', '-')
    return f"{base_url}{category_formatted}?country={country_code}&location={location_formatted}"

# Set the search category and location
category = 'Bank'
location = 'Berlin'
source = 'https://www.trustpilot.com'
source_name = "Trustpilot"

# Generate the URL dynamically
url = generate_trustpilot_url(category, location)

# Initialize Chrome web driver with existing user profile
chrome_options = Options()
# chrome_options.add_argument("/Users/apple/Library/Application Support/Google/Chrome/Default")  # Change to your Chrome profile path

chrome_options.add_argument("/Users/apple/Library/Application Support/Google/Chrome/Default")  # Change to your Chrome profile path
# chrome_options.add_argument("--headless")  # Optional: Run Chrome in headless mode, i.e., without a UI
service = Service(webdriver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

# Open the Trustpilot search page
driver.get(url)

# Wait for the main content to load
wait = WebDriverWait(driver, 20)
try:
    wait.until(EC.presence_of_element_located((By.XPATH, '//div[@class="styles_main__XgQiu"]')))
    print("Main content loaded.")
except Exception as e:
    print(f"Error waiting for main content to load: {e}")
    driver.quit()
    sys.exit()

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
        # Find all the business elements
        business_elements = driver.find_elements(By.XPATH, "//div[@class='paper_paper__1PY90 paper_outline__lwsUX card_card__lQWDv card_noPadding__D8PcU styles_wrapper__2JOo2']")

        print("Found the business elements")

        for business in business_elements:
            try:
                # Locate the link element
                link_element = business.find_element(By.XPATH, './/a[@class="link_internal__7XN06 link_wrapper__5ZJEx styles_linkWrapper__UWs5j"]')
                link = link_element.get_attribute('href')
                name = business.find_element(By.XPATH, './/p[@class="typography_heading-xs__jSwUz typography_appearance-default__AAY17 styles_displayName__GOhL2"]').text
                logging.info(f"the name is {name}")
                # Add the name and link to the dictionary if the name is not already present
                if name not in business_dict:
                    business_dict[name] = link
            except Exception as e:
                print(f"Error extracting name and link: {e}")
                continue

        print(f"Extracted {len(business_dict)} unique business names and links so far.")
    except Exception as e:
        print(f"Error extracting business data: {e}")

# Main script to handle pagination and data extraction
def main(driver):
    all_business_data = {}
    while True:
        extract_business_links_and_names(driver, all_business_data)
        print(f"So far total unique items: {len(all_business_data)}")

        if is_pagination_visible(driver) and is_pagination_button_interactable(driver):
            print("Pagination button found and interactable. Clicking it.")
            try:
                # Wait for the pagination button to be clickable
                pagination_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="styles_paginationWrapper__fukEb styles_pagination__USObu"]/nav[@aria-label="Pagination"]/a[@name="pagination-button-next"]')))

                # Scroll to the pagination button
                driver.execute_script("arguments[0].scrollIntoView(true);", pagination_button)

                # Click the pagination button using ActionChains
                ActionChains(driver).move_to_element(pagination_button).click().perform()

                # Wait for the next page to load
                time.sleep(10)
            except Exception as e:
                print(f"Error clicking pagination button: {e}")
                break
        else:
            print("Pagination button not found or not interactable. Stopping pagination.")
            break

    # Convert the dictionary to a list of tuples
    all_business_data_list = list(all_business_data.items())
    print(f"Total unique business items extracted: {len(all_business_data_list)}")
    
    # Save the links and names to a CSV file
    csv_file_path = f"/Users/apple/Documents/freelance project/scripy/turstpailot/TrustPilot_Automation/{category.replace(' ', '_')}.csv"
    try:
        with open(csv_file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Business Name', 'Business Link'])  # Write the header
            for name, link in all_business_data_list:
                writer.writerow([name, link])
        print(f"Links and names successfully saved to {csv_file_path}")
    except Exception as e:
        print(f"Error saving links and names to CSV: {e}")

    # Close the web driver
    driver.quit()
    
    # Use the full path to Python executable
    python_executable = sys.executable  # This gets the currently running Python executable

    # Call details.py with the CSV file path
    try:
        subprocess.run([python_executable, '/Users/apple/Documents/freelance project/scripy/turstpailot/TrustPilot_Automation/details.py', csv_file_path, source_name, source, category], check=True)
        print(f"details.py executed successfully with {csv_file_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error calling details.py: {e}")

# Run the main function
main(driver)
