import os
import django
from config.models import GPU, CPU, Motherboard, RAM, Cooling, PowerSupply, Storage, Case
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "IConfigurator.settings")
django.setup()
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../..')


import pickle
import json

from tqdm import tqdm
from random import randint
from time import sleep as pause
from bs4 import BeautifulSoup
import undetected_chromedriver as uc

import requests
from django.core.files import File
from io import BytesIO
import logging

# Настройка логгера
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("parser.log"),  # Логи будут записываться в файл
        logging.StreamHandler()            # Логи также будут выводиться в консоль
    ]
)
logger = logging.getLogger('parser_logger')

def download_image(image_url):
    """ Скачивает изображение и возвращает объект File. """
    if not image_url:
        return None

    response = requests.get(image_url)
    if response.status_code == 200:
        file_name = image_url.split('/')[-1]  # Извлекаем имя файла из URL
        file_content = BytesIO(response.content)
        return File(file_content, name=file_name)
    return None

def parse_gpu_page2(driver, url):
    try:
        logger.info(f"Начинаем парсинг страницы: {url}")
        driver.get(url)
        pause(randint(7, 11))
        soup = BeautifulSoup(driver.page_source, 'lxml')

        logger.debug(f"страница {url} успешно загружена")

        # Извлечение данных
        #name_tag = soup.find('div', class_="product-card-description__title")
        price_tag = soup.find('div', class_="product-buy__price")
        main_picture = soup.find('img', class_="header-product__image-img loaded")

        # Проверка наличия тегов
        #model = name_tag.text.strip() if name_tag else None
        price = int(price_tag.text.replace(' ', '').replace('₽', '')) if price_tag else 0
        image_url = main_picture.get('src') if main_picture else None

        # Логирование
        #if not name_tag: logger.warning(f"Модель не найдена на странице: {url}")
        if not price_tag:
            logger.warning(f"Цена не найдена на странице: {url}")
        if not main_picture:
            logger.warning(f"Изображение не найдено на странице: {url}")

        # Скачивание изображения
        image_file = download_image(image_url)

        # Характеристики
        charcs = soup.find_all('div', class_="product-characteristics__spec-title")
        cvalue = soup.find_all('div', class_="product-characteristics__spec-value")
        tech_spec = {}
        for f1, f2 in zip(charcs, cvalue):
            tech_spec[f1.text.rstrip().lstrip()] = f2.text.rstrip().lstrip()

        model = tech_spec.get("Модель", None)
        if not model:
            logger.warning(f"Модель не найдена на странице: {url}")
        # Извлечение характеристик с проверкой
        frequency = int(tech_spec.get("Частота ядра", "0").split()[0]) if tech_spec.get("Частота ядра") else 0
        memory_amount = int(tech_spec.get("Объем памяти", "0").split()[0]) if tech_spec.get("Объем памяти") else 0
        tdp = int(tech_spec.get("TDP", "0").split()[0]) if tech_spec.get("TDP") else 0
        size = int(tech_spec.get("Размер", "0").split()[0]) if tech_spec.get("Размер") else 0
        consumption = int(tech_spec.get("Потребление", "0").split()[0]) if tech_spec.get("Потребление") else 0

        # Создание словаря GPU
        gpu = {
            "model": model,
            "price": price,
            "frequency": frequency,
            "memory_amount": memory_amount,
            "tdp": tdp,
            "size": size,
            "consumption": consumption,
            "picture": image_url,
        }

        logger.info(f"Спарсены данные: {gpu['model']}")
        return gpu

    except Exception as e:
        logger.error(f"Ошибка при парсинге страницы {url}: {e}")
        return None

def save_to_json(data, file_name="parsed_data.json"):
    """
    Сохраняет данные в JSON-файл.
    :param data: Список словарей с данными.
    :param file_name: Имя файла для сохранения.
    """
    # Убедитесь, что папка для файла существует
    os.makedirs(os.path.dirname(file_name), exist_ok=True)

    # Сохранение данных в JSON
    with open(file_name, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

    print(f"Данные успешно сохранены в файл {file_name}")

def get_urls_from_page(driver):
    """ Собирает все ссылки на текущей странице. """
    soup = BeautifulSoup(driver.page_source, 'lxml')
    elements = soup.find_all('a', class_="catalog-product__name ui-link ui-link_black")
    return list(map(
        lambda element: 'https://www.dns-shop.ru' + element.get("href") + 'characteristics/',
        elements
    ))

def main():
    driver = uc.Chrome()
    urls_to_parse = [
        'https://www.dns-shop.ru/catalog/17a89aab16404e77/videokarty/?p={page}',
    ]

    parsed_data = []
    for url_template in urls_to_parse:
        page = 1
        while True:
            url = url_template.format(page=page)
            logger.info(f"Парсим страницу категории: {url}")
            driver.get(url)
            pause(randint(6, 9))
            soup = BeautifulSoup(driver.page_source, 'lxml')

            # Получаем ссылки на товары
            product_urls = get_urls_from_page(driver)
            if not product_urls:
                break

            for product_url in tqdm(product_urls, ncols=70, unit='товаров', colour='blue'):
                try:
                    gpu_data = parse_gpu_page2(driver, product_url)
                    if gpu_data:
                        parsed_data.append(gpu_data)
                        save_to_json(parsed_data, file_name='parsed.json')
                except Exception as e:
                    logger.error(f"Ошибка при парсинге {product_url}: {e}")

            page += 1

    driver.quit()
    logger.info("Парсинг завершен.")
    print("Все готово!")


if __name__ == '__main__':
    main()
    print('=' * 20)
    print('Все готово!')