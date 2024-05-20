#!/usr/bin/env python3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import requests
import time
import json
import os

def main():
    # Ids of all battles scraped to prevent duplicates.
    with open("Create json file to save duplicates and put your filepath here", 'r') as data:
        battle_ids = set(json.load(data))

    # Open headless browser
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("enable-automation")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-infobars")
    options.binary_location = "/usr/bin/google-chrome"

    # Setup Selenium with ChromeDriver
    service = Service(ChromeDriverManager().install())
    counter = 0
    driver = webdriver.Chrome(options=options, service=service)
    print("Successfully started driver")

    # Array of how many battles are added on each iteration of scrape()
    battles_added_each_iteration = []

    try:
        while True:
            scrape(driver, battle_ids, battles_added_each_iteration)
            counter += 1
            print("Waiting before the next scrape. Counter: {}".format(counter))
            # Wait 1:20 minute between scrapes
            time.sleep(80)
    except KeyboardInterrupt:
        print("Script interrupted by user. Exiting.")
    finally:
        del battles_added_each_iteration[0]
        max_hits = battles_added_each_iteration.count(50)
        print("Amount of times scraped the max amount of times: {}, rate: {}\n(Should scrape"
              " under 50 values to capture all the files)".format(max_hits, max_hits/len(battles_added_each_iteration)))
        mean = sum(battles_added_each_iteration) / len(battles_added_each_iteration)
        print("Average battles added during call to scrape: {}".format(mean))
        driver.quit()


def scrape(driver, battle_ids, battles_added_each_iteration):

    # Navigate to the webpage
    driver.get('https://replay.pokemonshowdown.com/')

    # Wait for the dynamic content to load
    time.sleep(5)

    # Finds recent replays on webpage
    recent_replays_links = driver.find_elements(By.XPATH, "//h1[contains(text(), 'Recent replays')]/following-sibling::ul//a")

    # Counts the amount of battles added after the scrape
    battles_added_counter = 0

    # Extract and print the href attributes
    for link in recent_replays_links:
        href = link.get_attribute('href')
        href += '.json'
        for attempt in range(10):  # Retry connecting 10 times if there is a connection issue
            try:
                response = requests.get(href)
                if response.status_code == 200:
                    # Parse the JSON response
                    data = response.json()
                    data_string = json.dumps(data)
                    id_value = data['id']
                    battle_id = id_value
                    if battle_id not in battle_ids:
                        battles_added_counter += 1
                        battle_format = data['format']
                        save_file(battle_format, battle_id, data_string)
                        battle_ids.add(id_value)
                        save_battle_ids(battle_ids)
                    break
                else:
                    print(f"Failed to fetch data. Status code: {response.status_code}")
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                print(f"Error fetching data: {e}. Attempt {attempt + 1} of 3.")
                time.sleep(30 * 60)  # Wait before retrying
            except json.JSONDecodeError as e:
                print(f"{e}. Failed to decode JSON from response:", response.text)

    # Adds the amount of battles added to a list for analysis
    battles_added_each_iteration.append(battles_added_counter)
    print(f"Battles added after scrape: {battles_added_counter}")


def save_battle_ids(battle_ids):
    # Convert set to list for JSON serialization
    battle_ids_list = list(battle_ids)
    battle_ids_json = json.dumps(battle_ids_list)
    with open('example', 'w') as file:  # Open a file for writing
        file.write(battle_ids_json)


def save_file(battle_format, battle_id, content):
    # Construct the directory
    directory = os.path.join("Your own base directory", battle_format)

    # Construct the file name
    filename = f"{battle_id}.json"

    # Construct the full file path
    file_path = os.path.join(battle_format, filename)

    # Create the directory if it does not exist
    if not os.path.exists(battle_format):
        os.makedirs(battle_format)

    # Write JSON content to the file
    with open(file_path, 'w') as file:
        file.write(content)


if __name__ == "__main__":
    main()