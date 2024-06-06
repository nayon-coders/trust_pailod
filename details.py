import csv
import logging
import time
import mysql.connector
import sys
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from mysql.connector import errorcode

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# MySQL configuration
mysql_config = {
    'user': 'root',
    'password': 'xxxxxxx', # Here give your password
    'host': 'localhost',
    'database': 'TrustPilot' # You must have schema or database named TrusPilot
}

# Path to your webdriver executable
webdriver_path = '/Users/sabbirahmad/Desktop/chromedriver'

if len(sys.argv) < 2:
    logger.error("CSV file path not provided.")
    sys.exit(1)
csv_input_file_path = sys.argv[1]

table_name = os.path.splitext(os.path.basename(csv_input_file_path))[0]

chrome_options = Options()
service = Service(webdriver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

with open(csv_input_file_path, mode='r') as file:
    csv_reader = csv.reader(file)
    next(csv_reader)  # Skip header row
    links = list(csv_reader)

# Initialize WebDriverWait
wait = WebDriverWait(driver, 20)

# Function to create a table if it doesn't exist
def create_table(cursor, table_name):
    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS `{table_name}` (
        id INT AUTO_INCREMENT PRIMARY KEY,
        Company_name VARCHAR(255),
        Company_link VARCHAR(1000),
        reviewer_name VARCHAR(255),
        review_date VARCHAR(50),
        review_star VARCHAR(50),
        review_description TEXT,
        avg_rating VARCHAR(50)
    );
    """
    try:
        cursor.execute(create_table_query)
        logger.info(f"Table `{table_name}` ensured to exist.")
    except mysql.connector.Error as err:
        logger.error(f"Error creating table: {err}")

# Function to check if a review already exists in the MySQL table
def review_exists(cursor, table_name, reviewer_name, review_date):
    query = f"""
    SELECT COUNT(*) FROM `{table_name}` WHERE reviewer_name = %s AND review_date = %s;
    """
    cursor.execute(query, (reviewer_name, review_date))
    result = cursor.fetchone()
    return result[0] > 0

# Function to insert review data into the MySQL table
def insert_review_data(cursor, table_name, data):
    insert_query = f"""
    INSERT INTO `{table_name}` (Company_name, Company_link, reviewer_name, review_date, review_star, review_description, avg_rating)
    VALUES (%s, %s, %s, %s, %s, %s, %s);
    """
    try:
        cursor.execute(insert_query, data)
    except mysql.connector.Error as err:
        logger.error(f"Error inserting data: {err}")

# Function to check if pagination element is present and visible
def is_pagination_visible(driver):
    try:
        pagination = driver.find_element(By.XPATH, '//div[@class="styles_pagination__6VmQv"]/nav[@aria-label="Pagination"]/a[@name="pagination-button-next"]')
        return pagination.is_displayed()
    except:
        return False

# Function to check if pagination button is interactable
def is_pagination_button_interactable(driver):
    try:
        pagination_button = driver.find_element(By.XPATH, '//div[@class="styles_pagination__6VmQv"]/nav[@aria-label="Pagination"]/a[@name="pagination-button-next"]')
        return pagination_button.is_enabled() and pagination_button.get_attribute("aria-disabled") != "true"
    except:
        return False

def is_all_reviews(driver):
    try:
        button = driver.find_element(By.XPATH, '//a[@name="show-all-reviews"]')
        return button.is_displayed()
    except:
        return False

# Function to extract review information from the current page
def extract_reviews(driver, company_name, company_link, avg_rating, cursor, table_name):
    reviews_data = []
    try:
        time.sleep(5)
        review_elements = driver.find_elements(By.XPATH, '//div[@class="styles_cardWrapper__LcCPA styles_show__HUXRb styles_reviewCard__9HxJJ"]')
        for review in review_elements:
            try:
                reviewer_name = review.find_element(By.XPATH, './/div[@class="styles_consumerDetailsWrapper__p2wdr"]/a[@name="consumer-profile"]/span').text
                logger.info(f"Reviewer name: {reviewer_name}")
            except Exception as e:
                reviewer_name = "N/A"
                logger.error(f"Reviewer name not found: {e}")

            try:
                review_date = review.find_element(By.XPATH, './/div[@class= "typography_body-m__xgxZ_ typography_appearance-subtle__8_H2l styles_datesWrapper__RCEKH"]//time').text
                logger.info(f"Review date: {review_date}")
            except Exception as e:
                review_date = "N/A"
                logger.error(f"Review date not found: {e}")

            # Skip review if it already exists in the database
            if review_exists(cursor, table_name, reviewer_name, review_date):
                logger.info(f"Review by {reviewer_name} on {review_date} already exists. Skipping.")
                continue

            try:
                review_star_elem = review.find_element(By.XPATH, './/div[@class="star-rating_starRating__4rrcf star-rating_medium__iN6Ty"]/img').get_attribute('alt')
                get_review_star = review_star_elem.split()
                review_star = get_review_star[1]
                logger.info(f"Review star rating: {review_star}")
            except Exception as e:
                review_star = "N/A"
                logger.error(f"Review star not found: {e}")

            try:
                review_description = review.find_element(By.XPATH, './/div[@class="styles_reviewContent__0Q2Tg"]/p[@class="typography_body-l__KUYFJ typography_appearance-default__AAY17 typography_color-black__5LYEn"]').text
                logging.info("Got the review description")
            except Exception as e:
                review_description = "N/A"
                logging.info("Review Description Not Found")
                # logger.error(f"Review description not found: {e}")

            reviews_data.append((company_name, company_link, reviewer_name, review_date, review_star, review_description, avg_rating))
        logger.info(f"Extracted {len(reviews_data)} reviews.")

        if len(reviews_data) == 0:
            reviewer_name = "N/A"
            review_date = "N/A"
            review_star = "N/A"
            review_description = "N/A"
            reviews_data.append((company_name, company_link, reviewer_name, review_date, review_star, review_description, avg_rating))
    except Exception as e:
        logger.error(f"Error finding review elements: {e}")
    return reviews_data

# Function to handle pagination
def handle_pagination(driver, company_name, company_link, avg_rating, cursor, table_name):
    all_reviews = []
    while True:
        reviews = extract_reviews(driver, company_name, company_link, avg_rating, cursor, table_name)
        all_reviews.extend(reviews)
        # Scroll down twice to load more reviews
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.PAGE_DOWN)
        time.sleep(6)
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.PAGE_DOWN)
        time.sleep(6)

        try:
            if is_pagination_visible(driver) and is_pagination_button_interactable(driver):
                print("Pagination button found and interactable. Clicking it.")
                try:
                    # Wait for the pagination button to be clickable
                    pagination_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//a[@name="pagination-button-next"]')))
                    pagination_button.click()
                    # Wait for the next page to load
                    time.sleep(10)
                except:
                    break
            else:
                if is_all_reviews(driver):
                    button = driver.find_element(By.XPATH, '//a[@name="show-all-reviews"]')
                    button.click()
                    time.sleep(6)
                else:
                    break
        except Exception as e:
            logger.info(f"No more pages found: {e}")
            break
    return all_reviews

# Connect to MySQL
connection = None
cursor = None

try:
    connection = mysql.connector.connect(**mysql_config)
    cursor = connection.cursor()
    logger.info("Connected to MySQL database.")

    # Create the table
    create_table(cursor, table_name)

    # Iterate over links and extract review data
    for name, link in links:
        logger.info(f"Opening link for: {name}")

        driver.get(link)
        try:
            # Wait for the reviews to load
            wait.until(EC.presence_of_element_located((By.XPATH, '//section[@class="styles_reviewsContainer__3_GQw"]')))
            logger.info("Reviews section loaded.")
            
            # Extract the average rating
            avg_rating = "N/A"
            try:
                avg_rating_element = driver.find_element(By.XPATH, '//span[@class = "typography_heading-m__T_L_X typography_appearance-default__AAY17"]')
                avg_rating = avg_rating_element.text
                logger.info(f'Average rating is {avg_rating}')
            except Exception as e:
                if driver.find_element(By.XPATH, '//p[@class = "typography_body-l__KUYFJ typography_appearance-default__AAY17"]').text == "0 total":
                    avg_rating = "0"
                else:
                    logger.error(f"Average rating not found: {e}")

            # Scroll down twice to load more reviews
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.PAGE_DOWN)
            time.sleep(6)
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.PAGE_DOWN)
            time.sleep(6)

            # Handle pagination and extract review data
            reviews = handle_pagination(driver, name, link, avg_rating, cursor, table_name)
            
            # Insert review data into MySQL
            for review in reviews:
                insert_review_data(cursor, table_name, review)
            
            # Commit the transaction after each company
            connection.commit()

        except Exception as e:
            logger.error(f"Error processing link {link}: {e}")
            continue

except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        logger.error("Something is wrong with your user name or password.")
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
        logger.error("Database does not exist.")
    else:
        logger.error(err)
finally:
    if cursor:
        cursor.close()
    if connection:
        connection.close()
    logger.info("MySQL connection closed.")
    driver.quit()
