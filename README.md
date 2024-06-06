# TrustPilot_Automation

Certainly! Below is a README file that you can provide to your client. It includes instructions on how to configure the paths, change the search name, and run the script.

```markdown
# TrustPilot Review Scraper

This script extracts reviews from TrustPilot and saves them into a MySQL database. The table name in the database is dynamically set based on the name of the CSV file containing the URLs to be scraped.

## Prerequisites

1. **Python**: Ensure that Python is installed on your machine. You can download it from [python.org](https://www.python.org/).
2. **MySQL**: Install MySQL and set up a database. You can download it from [mysql.com](https://www.mysql.com/).
3. **Selenium WebDriver**: Download the Chrome WebDriver from [chromedriver.chromium.org](https://chromedriver.chromium.org/).
4. **Python Packages**: Install the necessary Python packages using the following command:
    ```sh
    pip install selenium mysql-connector-python
    ```

## Configuration

### Step 1: Update the `details.py` Script

1. **WebDriver Path**: Change the `webdriver_path` variable to the path where you have saved the Chrome WebDriver executable on your machine.
    ```python
    webdriver_path = '/path/to/chromedriver'
    ```

2. **MySQL Configuration**: Update the `mysql_config` dictionary with your MySQL username, password, host, and database name.
    ```python
    mysql_config = {
        'user': 'your_mysql_username',
        'password': 'your_mysql_password',
        'host': 'localhost',
        'database': 'your_database_name'
    }
    ```

3. **CSV File Path**: When running the script, provide the path to your CSV file as a command-line argument.

### Step 2: Prepare Your CSV File

Create a CSV file containing the URLs to be scraped. The first row should contain the headers, and the subsequent rows should contain the company names and URLs. For example:

```csv
CompanyName,CompanyURL
Company A,https://www.trustpilot.com/review/company-a
Company B,https://www.trustpilot.com/review/company-b
```

### Step 3: Running the Script

To run this you can click the run button of visual studio code or pycharme.

## Logging

The script will log its progress and any errors encountered. This information can be helpful for debugging if something goes wrong.

## Additional Information

- **Search Name**: If you need to change the search criteria or add additional logic for extracting reviews, you can modify the `extract_reviews` function in the script.

## Troubleshooting

- **MySQL Connection Issues**: Ensure that MySQL is running and the credentials provided in `mysql_config` are correct.
- **WebDriver Issues**: Ensure that the Chrome WebDriver version matches your installed Chrome browser version.
- **Dependencies**: Make sure all required Python packages are installed.

## Contact

For any issues or questions, please contact [Sabbir Ahmad] at [sabbirahmad653@gmail.com].

---

Thank you for using TrustPilot Review Scraper!
```

