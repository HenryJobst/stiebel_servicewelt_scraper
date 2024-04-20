import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime

import requests
import schedule
from bs4 import BeautifulSoup


@dataclass
class WpData:
    timestamp: datetime
    ruecklauftemperatur: str
    vorlauftemperatur: str
    aussentemperatur: str
    starts_verdichter: str


# Database setup
conn = sqlite3.connect('scraped_data.db')
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS temperature_data (
    timestamp TEXT,
    ruecklauftemperatur TEXT,
    vorlauftemperatur TEXT,
    aussentemperatur TEXT,
    starts_verdichter TEXT)
''')
conn.commit()


def parse(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        return BeautifulSoup(response.text, 'html.parser')
    except requests.RequestException as e:
        print(f"Error fetching data from {url}: {e}")
        return None


def scrape_and_store():
    url_status = "http://192.168.1.118/?s=1,0"
    url_wp = "http://192.168.1.118/?s=1,1"

    soup_wp = parse(url_wp)
    if soup_wp is None:
        return

    data = WpData(
        timestamp=datetime.now(),
        ruecklauftemperatur=soup_wp.find("td", text="RÜCKLAUFTEMPERATUR").find_next_sibling("td").text,
        vorlauftemperatur=soup_wp.find("td", text="VORLAUFTEMPERATUR").find_next_sibling("td").text,
        aussentemperatur=soup_wp.find("td", text="AUSSENTEMPERATUR").find_next_sibling("td").text,
        starts_verdichter=soup_wp.find("td", text="VERDICHTER").find_next_sibling("td").text
    )

    # Insert data into the database
    with conn:
        conn.execute('''
            INSERT INTO temperature_data (timestamp, ruecklauftemperatur, vorlauftemperatur, aussentemperatur, 
            starts_verdichter)
            VALUES (?, ?, ?, ?, ?)
            ''', (data.timestamp.strftime("%Y-%m-%d %H:%M:%S"), data.ruecklauftemperatur, data.vorlauftemperatur,
                  data.aussentemperatur, data.starts_verdichter))

    print(f"Data stored at {data.timestamp}: {data}")


scrape_and_store()

# Schedule to run every 1 minute
schedule.every(1).minute.do(scrape_and_store)

try:
    while True:
        schedule.run_pending()
        time.sleep(1)
except KeyboardInterrupt:
    print("Stopped.")
    conn.close()
