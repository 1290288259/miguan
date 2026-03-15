import os
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_URL_CITY = "https://github.com/P3TERX/GeoLite.mmdb/raw/download/GeoLite2-City.mmdb"
DB_URL_ASN = "https://github.com/P3TERX/GeoLite.mmdb/raw/download/GeoLite2-ASN.mmdb"
DB_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_PATH_CITY = os.path.join(DB_DIR, "GeoLite2-City.mmdb")
DB_PATH_ASN = os.path.join(DB_DIR, "GeoLite2-ASN.mmdb")

def download_file(url, path, name):
    if os.path.exists(path):
        logger.info(f"{name} already exists.")
        return

    logger.info(f"Downloading {name} (this may take a minute)...")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        logger.info(f"{name} Download completed successfully.")
    except Exception as e:
        logger.error(f"Failed to download {name}: {e}")
        if os.path.exists(path):
            os.remove(path)

def download_db():
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)
        
    download_file(DB_URL_CITY, DB_PATH_CITY, "GeoLite2-City.mmdb")
    download_file(DB_URL_ASN, DB_PATH_ASN, "GeoLite2-ASN.mmdb")

if __name__ == "__main__":
    download_db()
