import os
import sys
import urllib.parse
from multiprocessing import Pool, cpu_count, freeze_support

from bs4 import BeautifulSoup
from loguru import logger
from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.expected_conditions import (
    presence_of_all_elements_located,
)
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm

from .get_image import get_image

NUM_CORES = cpu_count() // 2


def main():
    if sys.platform.startswith("win"):
        freeze_support()

    if len(sys.argv) < 2:
        raise ValueError("Missing URL")

    url = sys.argv[1]
    pr = urllib.parse.urlparse(url)
    if not pr.netloc and not pr.scheme:
        raise ValueError("Invalid URL scheme")

    logger.info(f"Retrieving URL {url}...")
    service = Service(log_path=os.devnull)
    options = Options()
    options.headless = True
    with Firefox(options=options, service=service) as driver:
        driver.get(url)
        WebDriverWait(driver, 10).until(presence_of_all_elements_located((By.CLASS_NAME, "se_mediaImage")))
        html = driver.page_source

    logger.info("Scraping page source...")
    soup = BeautifulSoup(html, "lxml")
    images = soup.find_all(attrs={"class": "se_mediaImage"})
    sources = [img.get("src") for img in images]

    logger.info("Downloading media...")
    with Pool(processes=NUM_CORES - 1) as pool:
        with tqdm(total=len(sources)) as pbar:
            for _ in pool.imap_unordered(get_image, sources):
                pbar.update()


if __name__ == "__main__":
    main()
