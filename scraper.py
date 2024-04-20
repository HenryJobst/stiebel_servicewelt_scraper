import re
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
    # Prozessdaten
    ruecklauftemperatur: str
    vorlauftemperatur: str
    frostschutztemperatur: str
    aussentemperatur: str
    verdampfertemperatur: str
    verdichtereintrittstemperatur: str
    heissgastemperatur: str
    verfluessigertemperatur: str
    oelsumpftemperatur: str
    druck_niederdruck: str
    druck_hochdruck: str
    wp_wasservolumenstrom: str
    strom_inverter: str
    spannung_inverter: str
    istdrehzahl_verdichter: str
    solldrehzahl_verdichter: str
    luefterleistung_rel: str
    verdampfereintrittstemperatur: str
    expansionsventileintrittstemperatur: str
    inverter_aufnahmeleistung: str
    # Starts
    starts_verdichter: str
    # Wärmemenge
    waermemenge_vd_heizen_tag: str
    waermemenge_vd_heizen_summe: str
    waermemenge_vd_warmwasser_tag: str
    waermemenge_vd_warmwasser_summe: str
    waermemenge_nhz_heizen_summe: str
    waermemenge_nhz_warmwasser_summe: str
    # Leistungsaufnahme
    leistungsaufnahme_vd_heizen_tag: str
    leistungsaufnahme_vd_heizen_summe: str
    leistungsaufnahme_vd_warmwasser_tag: str
    leistungsaufnahme_vd_warmwasser_summe: str
    laufzeit_vd_heizen: str
    laufzeit_vd_warmwasser: str
    laufzeit_vd_kuehlen: str
    laufzeit_vd_abtauen: str
    laufzeit_nhz_1: str
    laufzeit_nhz_2: str
    laufzeit_nhz_1_2: str
    laufzeit_zeit_abtauen: str
    laufzeit_starts_abtauen: str


@dataclass
class WpStatus:
    raumtemp_ist: str
    raumtemp_soll: str
    raumfeuchte: str
    taupunkttemp: str
    timestamp: datetime
    warmwasser_ist: str
    warmwasser_soll: str
    warmwasser_volumenstrom: str
    kuehlen_ist: str
    kuehlen_soll: str
    aussentemp: str
    hk1_ist: str
    hk1_soll: str
    vorlaufisttemp_wp: str
    vorlaufisttemp_nhz: str
    ruecklaufisttemp_wp: str
    pufferisttemp: str
    puffersolltemp: str
    heizungsdruck: str
    frostschutz: str


# Database setup
conn = sqlite3.connect('wpl_data.db')
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS data (
    timestamp TEXT,
    raumtemp_ist TEXT,
    raumtemp_soll TEXT,
    raumfeuchte TEXT,
    taupunkttemp TEXT,
    warmwasser_ist TEXT,
    warmwasser_soll TEXT,
    warmwasser_volumenstrom TEXT,
    kuehlen_ist TEXT,
    kuehlen_soll TEXT,
    aussentemp TEXT,
    hk1_ist TEXT,
    hk1_soll TEXT,
    vorlaufisttemp_wp TEXT,
    vorlaufisttemp_nhz TEXT,
    ruecklaufisttemp_wp TEXT,
    pufferisttemp TEXT,
    puffersolltemp TEXT,
    heizungsdruck TEXT,
    frostschutz TEXT,
    ruecklauftemperatur TEXT,
    vorlauftemperatur TEXT,
    frostschutztemperatur TEXT,
    aussentemperatur TEXT,
    verdampfertemperatur TEXT,
    verdichtereintrittstemperatur TEXT,
    heissgastemperatur TEXT,
    verflüssigertemperatur TEXT,
    oelsumpftemperatur TEXT,
    druck_niederdruck TEXT,
    druck_hochdruck TEXT,
    wp_wasservolumenstrom TEXT,
    strom_inverter TEXT,
    spannung_inverter TEXT,
    istdrehzahl_verdichter TEXT,
    solldrehzahl_verdichter TEXT,
    luefterleistung_rel TEXT,
    verdampfereintrittstemperatur TEXT,
    expansionsventileintrittstemperatur TEXT,
    inverter_aufnahmeleistung TEXT,
    starts_verdichter TEXT,
    waermemenge_vd_heizen_tag TEXT,
    waermemenge_vd_heizen_summe TEXT,
    waermemenge_vd_warmwasser_tag TEXT,
    waermemenge_vd_warmwasser_summe TEXT,
    waermemenge_nhz_heizen_summe TEXT,
    waermemenge_nhz_warmwasser_summe TEXT,
    leistungsaufnahme_vd_heizen_tag TEXT,
    leistungsaufnahme_vd_heizen_summe TEXT,
    leistungsaufnahme_vd_warmwasser_tag TEXT,
    leistungsaufnahme_vd_warmwasser_summe TEXT,
    laufzeit_vd_heizen TEXT,
    laufzeit_vd_warmwasser TEXT,
    laufzeit_vd_kuehlen TEXT,
    laufzeit_vd_abtauen TEXT,
    laufzeit_nhz_1 TEXT,
    laufzeit_nhz_2 TEXT,
    laufzeit_nhz_1_2 TEXT,
    laufzeit_zeit_abtauen TEXT,
    laufzeit_starts_abtauen TEXT
    )
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


def extract_data(soup, header_label, label):
    tables = soup.find_all('table', class_='info')
    for table in tables:
        header = table.find('th')
        if header and header_label in header.text:
            ist_row = table.find('td', string=label)
            if ist_row:
                return ist_row.find_next_sibling('td').string

    return None


def extract_timestamp(soup):
    scripts = soup.find_all('script')
    timestamp = None
    for script in scripts:
        if script.string and 'timestampunterschied' in script.string:
            match = re.search(r'var timestampunterschied = (\d+) \* 1000', script.string)
            if match:
                timestamp = datetime.fromtimestamp(int(match.group(1)))
                break

    return timestamp


def scrape_and_store():
    url_status = "http://192.168.1.118/?s=1,0"
    url_wp = "http://192.168.1.118/?s=1,1"

    soup_status = parse(url_status)
    if soup_status is None:
        return

    soup_wp = parse(url_wp)
    if soup_wp is None:
        return

    timestamp = extract_timestamp(soup_wp)
    if not timestamp:
        timestamp = datetime.now()

    data_status = WpStatus(timestamp=timestamp,
                           raumtemp_ist=extract_data(soup_status, 'RAUMTEMPERATUR', 'ISTTEMPERATUR 1'),
                           raumtemp_soll=extract_data(soup_status, 'RAUMTEMPERATUR', 'SOLLTEMPERATUR 1'),
                           raumfeuchte=extract_data(soup_status, 'RAUMTEMPERATUR', 'RAUMFEUCHTE 1'),
                           taupunkttemp=extract_data(soup_status, 'RAUMTEMPERATUR', 'TAUPUNKTTEMPERATUR 1'),
                           warmwasser_ist=extract_data(soup_status, 'WARMWASSER', 'ISTTEMPERATUR'),
                           warmwasser_soll=extract_data(soup_status, 'WARMWASSER', 'SOLLTEMPERATUR'),
                           warmwasser_volumenstrom=extract_data(soup_status, 'WARMWASSER', 'VOLUMENSTROM'),
                           kuehlen_ist=extract_data(soup_status, 'KÜHLEN', 'ISTTEMPERATUR'),
                           kuehlen_soll=extract_data(soup_status, 'KÜHLEN', 'VOLUMENSTROM'),
                           aussentemp=extract_data(soup_status, 'HEIZUNG', 'AUSSENTEMPERATUR'),
                           hk1_ist=extract_data(soup_status, 'HEIZUNG', 'ISTTEMPERATUR HK 1'),
                           hk1_soll=extract_data(soup_status, 'HEIZUNG', 'SOLLTEMPERATUR HK 1'),
                           vorlaufisttemp_wp=extract_data(soup_status, 'HEIZUNG', 'VORLAUFISTTEMPERATUR WP'),
                           vorlaufisttemp_nhz=extract_data(soup_status, 'HEIZUNG', 'VORLAUFISTTEMPERATUR NHZ'),
                           ruecklaufisttemp_wp=extract_data(soup_status, 'HEIZUNG', 'RÜCKLAUFISTTEMPERATUR WP'),
                           pufferisttemp=extract_data(soup_status, 'HEIZUNG', 'PUFFERISTTEMPERATUR'),
                           puffersolltemp=extract_data(soup_status, 'HEIZUNG', 'PUFFERSOLLTEMPERATUR'),
                           heizungsdruck=extract_data(soup_status, 'HEIZUNG', 'HEIZUNGSDRUCK'),
                           frostschutz=extract_data(soup_status, 'HEIZUNG', 'FROSTSCHUTZ')
                           )

    data_wp = WpData(
        timestamp=timestamp,
        ruecklauftemperatur=extract_data(soup_status, 'PROZESSDATEN', 'RÜCKLAUFTEMPERATUR'),
        vorlauftemperatur=extract_data(soup_status, 'PROZESSDATEN', 'VORLAUFTEMPERATUR'),
        frostschutztemperatur=extract_data(soup_status, 'PROZESSDATEN', 'FROSTSCHUTZTEMPERATUR'),
        aussentemperatur=extract_data(soup_status, 'PROZESSDATEN', 'AUSSENTEMPERATUR'),
        verdampfertemperatur=extract_data(soup_status, 'PROZESSDATEN', 'VERDAMPFERTEMPERATUR'),
        verdichtereintrittstemperatur=extract_data(soup_status, 'PROZESSDATEN', 'VERDICHTEREINTRITTSTEMPERATUR'),
        heissgastemperatur=extract_data(soup_status, 'PROZESSDATEN', 'HEISSGASTEMPERATUR'),
        verfluessigertemperatur=extract_data(soup_status, 'PROZESSDATEN', 'VERFLÜSSIGERTEMPERATUR'),
        oelsumpftemperatur=extract_data(soup_status, 'PROZESSDATEN', 'ÖLSUMPFTEMPERATUR'),
        druck_niederdruck=extract_data(soup_status, 'PROZESSDATEN', 'DRUCK NIEDERDRUCK'),
        druck_hochdruck=extract_data(soup_status, 'PROZESSDATEN', 'DRUCK HOCHDRUCK'),
        wp_wasservolumenstrom=extract_data(soup_status, 'PROZESSDATEN', 'WP WASSERVOLUMENSTROM'),
        strom_inverter=extract_data(soup_status, 'PROZESSDATEN', 'STROM INVERTER'),
        spannung_inverter=extract_data(soup_status, 'PROZESSDATEN', 'SPANNUNG INVERTER'),
        istdrehzahl_verdichter=extract_data(soup_status, 'PROZESSDATEN', 'ISTDREHZAHL VERDICHTER'),
        solldrehzahl_verdichter=extract_data(soup_status, 'PROZESSDATEN', 'SOLLDREHZAHL VERDICHTER'),
        luefterleistung_rel=extract_data(soup_status, 'PROZESSDATEN', 'LÜFTERLEISTUNG REL'),
        verdampfereintrittstemperatur=extract_data(soup_status, 'PROZESSDATEN', 'VERDAMPFEREINTRITTSTEMPERATUR'),
        expansionsventileintrittstemperatur=extract_data(soup_status,
                                                         'PROZESSDATEN',
                                                         'EXPANSIONSVENTILEINTRITTSTEMPERATUR'),
        inverter_aufnahmeleistung=extract_data(soup_status, 'PROZESSDATEN', 'INVERTER AUFNAHMELEISTUNG'),
        starts_verdichter=extract_data(soup_status, 'STARTS', 'VERDICHTER'),
        waermemenge_vd_heizen_tag=extract_data(soup_status, 'WÄRMEMENGE', 'VD HEIZEN TAG'),
        waermemenge_vd_heizen_summe=extract_data(soup_status, 'WÄRMEMENGE', 'VD HEIZEN SUMME'),
        waermemenge_vd_warmwasser_tag=extract_data(soup_status, 'WÄRMEMENGE', 'VD WARMWASSER TAG'),
        waermemenge_vd_warmwasser_summe=extract_data(soup_status, 'WÄRMEMENGE', 'VD WARMWASSER SUMME'),
        waermemenge_nhz_heizen_summe=extract_data(soup_status, 'WÄRMEMENGE', 'NHZ HEIZEN SUMME'),
        waermemenge_nhz_warmwasser_summe=extract_data(soup_status, 'WÄRMEMENGE', 'NHZ WARMWASSER SUMME'),
        leistungsaufnahme_vd_heizen_tag=extract_data(soup_status, 'LEISTUNGSAUFNAHME', 'VD HEIZEN TAG'),
        leistungsaufnahme_vd_heizen_summe=extract_data(soup_status, 'LEISTUNGSAUFNAHME', 'VD HEIZEN SUMME'),
        leistungsaufnahme_vd_warmwasser_tag=extract_data(soup_status, 'LEISTUNGSAUFNAHME', 'VD WARMWASSER TAG'),
        leistungsaufnahme_vd_warmwasser_summe=extract_data(soup_status, 'LEISTUNGSAUFNAHME', 'VD WARMWASSER SUMME'),
        laufzeit_vd_heizen=extract_data(soup_status, 'LAUFZEIT', 'VD HEIZEN'),
        laufzeit_vd_warmwasser=extract_data(soup_status, 'LAUFZEIT', 'VD WARMWASSER'),
        laufzeit_vd_kuehlen=extract_data(soup_status, 'LAUFZEIT', 'VD KÜHLEN'),
        laufzeit_vd_abtauen=extract_data(soup_status, 'LAUFZEIT', 'VD ABTAUEN'),
        laufzeit_nhz_1=extract_data(soup_status, 'LAUFZEIT', 'NHZ 1'),
        laufzeit_nhz_2=extract_data(soup_status, 'LAUFZEIT', 'NHZ 2'),
        laufzeit_nhz_1_2=extract_data(soup_status, 'LAUFZEIT', 'NHZ 1/2'),
        laufzeit_zeit_abtauen=extract_data(soup_status, 'LAUFZEIT', 'ZEIT ABTAUEN'),
        laufzeit_starts_abtauen=extract_data(soup_status, 'LAUFZEIT', 'STARTS ABTAUEN'),
        )

    # Insert data_wp into the database
    with conn:
        conn.execute('''
            INSERT INTO data (
            timestamp,
            raumtemp_ist, raumtemp_soll, raumfeuchte, taupunkttemp,
            warmwasser_ist, warmwasser_soll, warmwasser_volumenstrom,
            kuehlen_ist, kuehlen_soll, 
            aussentemp, hk1_ist, hk1_soll, vorlaufisttemp_wp, vorlaufisttemp_nhz,
            ruecklaufisttemp_wp, pufferisttemp, puffersolltemp, heizungsdruck,
            frostschutz,
    ruecklauftemperatur,
    vorlauftemperatur,
    frostschutztemperatur,
    aussentemperatur,
    verdampfertemperatur,
    verdichtereintrittstemperatur,
    heissgastemperatur,
    verflüssigertemperatur,
    oelsumpftemperatur,
    druck_niederdruck,
    druck_hochdruck,
    wp_wasservolumenstrom,
    strom_inverter,
    spannung_inverter,
    istdrehzahl_verdichter,
    solldrehzahl_verdichter,
    luefterleistung_rel,
    verdampfereintrittstemperatur,
    expansionsventileintrittstemperatur,
    inverter_aufnahmeleistung,
    starts_verdichter,
    waermemenge_vd_heizen_tag,
    waermemenge_vd_heizen_summe,
    waermemenge_vd_warmwasser_tag,
    waermemenge_vd_warmwasser_summe,
    waermemenge_nhz_heizen_summe,
    waermemenge_nhz_warmwasser_summe,
    leistungsaufnahme_vd_heizen_tag,
    leistungsaufnahme_vd_heizen_summe,
    leistungsaufnahme_vd_warmwasser_tag,
    leistungsaufnahme_vd_warmwasser_summe,
    laufzeit_vd_heizen,
    laufzeit_vd_warmwasser,
    laufzeit_vd_kuehlen,
    laufzeit_vd_abtauen,
    laufzeit_nhz_1,
    laufzeit_nhz_2,
    laufzeit_nhz_1_2,
    laufzeit_zeit_abtauen,
    laufzeit_starts_abtauen             
            )
            VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            ''', (data_wp.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                  data_status.raumtemp_ist, data_status.raumtemp_soll, data_status.raumfeuchte,
                  data_status.taupunkttemp,
                  data_status.warmwasser_ist, data_status.warmwasser_soll, data_status.warmwasser_volumenstrom,
                  data_status.kuehlen_ist,
                  data_status.kuehlen_soll,
                  data_status.aussentemp,
                  data_status.hk1_ist,
                  data_status.hk1_soll,
                  data_status.vorlaufisttemp_wp,
                  data_status.vorlaufisttemp_nhz,
                  data_status.ruecklaufisttemp_wp,
                  data_status.pufferisttemp,
                  data_status.puffersolltemp,
                  data_status.heizungsdruck,
                  data_status.frostschutz,

                  data_wp.ruecklauftemperatur,
                  data_wp.vorlauftemperatur,
                  data_wp.frostschutztemperatur,
                  data_wp.aussentemperatur,
                  data_wp.verdampfertemperatur,
                  data_wp.verdichtereintrittstemperatur,
                  data_wp.heissgastemperatur,
                  data_wp.verfluessigertemperatur,
                  data_wp.oelsumpftemperatur,
                  data_wp.druck_niederdruck,
                  data_wp.druck_hochdruck,
                  data_wp.wp_wasservolumenstrom,
                  data_wp.strom_inverter,
                  data_wp.spannung_inverter,
                  data_wp.istdrehzahl_verdichter,
                  data_wp.solldrehzahl_verdichter,
                  data_wp.luefterleistung_rel,
                  data_wp.verdampfereintrittstemperatur,
                  data_wp.expansionsventileintrittstemperatur,
                  data_wp.inverter_aufnahmeleistung,
                  data_wp.starts_verdichter,
                  data_wp.waermemenge_vd_heizen_tag,
                  data_wp.waermemenge_vd_heizen_summe,
                  data_wp.waermemenge_vd_warmwasser_tag,
                  data_wp.waermemenge_vd_warmwasser_summe,
                  data_wp.waermemenge_nhz_heizen_summe,
                  data_wp.waermemenge_nhz_warmwasser_summe,
                  data_wp.leistungsaufnahme_vd_heizen_tag,
                  data_wp.leistungsaufnahme_vd_heizen_summe,
                  data_wp.leistungsaufnahme_vd_warmwasser_tag,
                  data_wp.leistungsaufnahme_vd_warmwasser_summe,
                  data_wp.laufzeit_vd_heizen,
                  data_wp.laufzeit_vd_warmwasser,
                  data_wp.laufzeit_vd_kuehlen,
                  data_wp.laufzeit_vd_abtauen,
                  data_wp.laufzeit_nhz_1,
                  data_wp.laufzeit_nhz_2,
                  data_wp.laufzeit_nhz_1_2,
                  data_wp.laufzeit_zeit_abtauen,
                  data_wp.laufzeit_starts_abtauen
                  ))

    print(f"Data stored at {data_wp.timestamp}: {data_wp}, {data_status}")


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
