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


mysql_config = {
    'user': 'u323738017_scrapy_user',
    'password': 'Scrapy@0001',
    'host': 'srv1267.hstgr.io',
    'database': 'u323738017_scrapy',
    'connect_timeout': 60,
    'connection_timeout': 60
}

webdriver_path = '/Users/apple/developments/chromedriver-mac-x64/chromedriver'

if len(sys.argv) < 5:
    logger.error("CSV file path not provided.")
    sys.exit(1)
csv_input_file_path = sys.argv[1]
source = sys.argv[3]
category = sys.argv[4]
source_name = sys.argv[2]

table_name = "Scrapped_Data"
chrome_options = Options()
service = Service(webdriver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

with open(csv_input_file_path, mode='r') as file:
    csv_reader = csv.reader(file)
    next(csv_reader)  
    links = list(csv_reader)

wait = WebDriverWait(driver, 20)

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
        phone_num VARCHAR(50),
        avg_rating VARCHAR(50),
        Source_Name VARCHAR(50),
        Source_Website VARCHAR(255),
        Company_category VARCHAR(100)
    );
    """
    try:
        cursor.execute(create_table_query)
        logger.info(f"Table `{table_name}` ensured to exist.")
    except mysql.connector.Error as err:
        logger.error(f"Error creating table: {err}")

def review_exists(cursor, table_name, reviewer_name, review_date):
    query = f"""
    SELECT COUNT(*) FROM `{table_name}` WHERE reviewer_name = %s AND review_date = %s;
    """
    try:
        cursor.execute(query, (reviewer_name, review_date))
        result = cursor.fetchone()
        return result[0] > 0
    except mysql.connector.Error as err:
        if err.errno in [errorcode.CR_SERVER_LOST, errorcode.CR_SERVER_GONE_ERROR]:
            logger.error(f"Lost connection to MySQL server. Attempting to reconnect: {err}")
            reconnect_mysql(connection, cursor)
            cursor.execute(query, (reviewer_name, review_date))
            result = cursor.fetchone()
            return result[0] > 0
        else:
            logger.error(f"Error checking review existence: {err}")
            return False

def insert_review_data(cursor, table_name, data):
    insert_query = f"""
    INSERT INTO `{table_name}` (Company_name, Company_link, reviewer_name, review_date, review_star, review_description, phone_num, avg_rating,Source_Name, Source_Website, Company_category)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """
    try:
        cursor.execute(insert_query, data)
    except mysql.connector.Error as err:
        if err.errno in [errorcode.CR_SERVER_LOST, errorcode.CR_SERVER_GONE_ERROR]:
            logger.error(f"Lost connection to MySQL server. Attempting to reconnect: {err}")
            reconnect_mysql(connection, cursor)
            cursor.execute(insert_query, data)
        else:
            logger.error(f"Error inserting data: {err}")

def reconnect_mysql(connection, cursor):
    try:
        connection.ping(reconnect=True, attempts=3, delay=5)
        logger.info("Reconnected to MySQL server.")
    except mysql.connector.Error as err:
        logger.error(f"Failed to reconnect to MySQL server: {err}")
        sys.exit(1)

def is_pagination_visible(driver):
    try:
        pagination = driver.find_element(By.XPATH, '//div[@class="styles_pagination__6VmQv"]/nav[@aria-label="Pagination"]/a[@name="pagination-button-next"]')
        return pagination.is_displayed()
    except:
        return False

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

def extract_reviews(driver, company_name, company_link, phone_num, avg_rating, Source_Name, source, category, cursor, table_name):
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

            reviews_data.append((company_name, company_link, reviewer_name, review_date, review_star, review_description, phone_num, avg_rating,Source_Name, source, category))
        logger.info(f"Extracted {len(reviews_data)} reviews.")

        if len(reviews_data) == 0:
            reviewer_name = "N/A"
            review_date = "N/A"
            review_star = "N/A"
            review_description = "N/A"
            reviews_data.append((company_name, company_link, reviewer_name, review_date, review_star, review_description, phone_num, avg_rating,Source_Name, source, category))
    except Exception as e:
        logger.error(f"Error finding review elements: {e}")
    return reviews_data

def handle_pagination(driver, company_name, company_link, phone_num, avg_rating,Source_Name, source, category, cursor, table_name):
    all_reviews = []
    while True:
        reviews = extract_reviews(driver, company_name, company_link, phone_num, avg_rating,Source_Name, source, category, cursor, table_name)
        all_reviews.extend(reviews)
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.PAGE_DOWN)
        time.sleep(4)
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.PAGE_DOWN)
        time.sleep(3)

        try:
            if is_pagination_visible(driver) and is_pagination_button_interactable(driver):
                print("Pagination button found and interactable. Clicking it.")
                try:
                    pagination_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//a[@name="pagination-button-next"]')))
                    pagination_button.click()
                    time.sleep(7)
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

connection = None
cursor = None

try:
    connection = mysql.connector.connect(**mysql_config)
    cursor = connection.cursor()
    logger.info("Connected to MySQL database.")

    create_table(cursor, table_name)

    for name, link in links:
        logger.info(f"Opening link for: {name}")

        driver.get(link)
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, '//section[@class="styles_reviewsContainer__3_GQw"]')))
            logger.info("Reviews section loaded.")

            phone_num = "N/A"
            
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

            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.PAGE_DOWN)
            time.sleep(3)
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.PAGE_DOWN)
            time.sleep(3)

            reviews = handle_pagination(driver, name, link, phone_num, avg_rating,source_name, source, category, cursor, table_name)
            
            for review in reviews:
                insert_review_data(cursor, table_name, review)
            
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
