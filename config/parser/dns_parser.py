import os
import django

from IConfigurator import settings
from config.models import ParsedGPU, CPU, Motherboard, RAM, Cooling, PowerSupply, Storage, Case
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

def download_image(image_url, model):
    """ Скачивает изображение и возвращает объект File. """
    if not image_url:
        return None

    try:
        response = requests.get(image_url)
        if response.status_code == 200:
            # Создаем директорию для изображений, если ее нет
            image_dir = os.path.join(settings.MEDIA_ROOT, 'gpu_images')
            os.makedirs(image_dir, exist_ok=True)

            # Генерируем имя файла на основе модели
            file_name = f"{model.replace(' ', '_')}.jpg"
            file_path = os.path.join(image_dir, file_name)

            logger.info(f"путь для сохранения изображения: {file_path}")

            # Сохраняем изображение
            with open(file_path, 'wb') as f:
                f.write(response.content)

            # Возвращаем путь для сохранения в модели
            return f'gpu_images/{file_name}'
    except Exception as e:
        logger.error(f"Ошибка при загрузке изображения: {e}")
    return None


def parse_gpu_page2(driver, url):
    try:
        logger.info(f"Начинаем парсинг страницы: {url}")
        print(f"MEDIA_ROOT: {settings.MEDIA_ROOT}")
        driver.get(url)
        pause(randint(7, 11))
        soup = BeautifulSoup(driver.page_source, 'lxml')

        # Извлечение данных
        price_tag = soup.find('div', class_="product-buy__price")
        main_picture = soup.find('img', class_="header-product__image-img loaded")

        price = int(price_tag.text.replace(' ', '').replace('₽', '')) if price_tag else 0
        image_url = main_picture.get('src') if main_picture else None

        # Характеристики
        charcs = soup.find_all('div', class_="product-characteristics__spec-title")
        cvalue = soup.find_all('div', class_="product-characteristics__spec-value")
        tech_spec = {}
        for f1, f2 in zip(charcs, cvalue):
            tech_spec[f1.text.rstrip().lstrip()] = f2.text.rstrip().lstrip()

        model = tech_spec.get("Модель", None)
        if not model:
            logger.warning(f"Модель не найдена на странице: {url}")
            return None

        # Скачивание изображения
        image_path = download_image(image_url, model)

        frequency = int(tech_spec.get("Частота ядра", "0").split()[0]) if tech_spec.get("Частота ядра") else 0,
        memory_amount = int(tech_spec.get("Объем памяти", "0").split()[0]) if tech_spec.get("Объем памяти") else 0,
        tdp = int(tech_spec.get("TDP", "0").split()[0]) if tech_spec.get("TDP") else 0,
        size = int(tech_spec.get("Размер", "0").split()[0]) if tech_spec.get("Размер") else 0,
        consumption = int(tech_spec.get("Потребление", "0").split()[0]) if tech_spec.get("Потребление") else 0,

        # Создание объекта GPU и сохранение в базу
        gpu,created = ParsedGPU.objects.update_or_create(
            model=model,
            defaults={
                'price': price,
                'frequency': frequency,
                'memory_amount': memory_amount,
                'tdp': tdp,
                'size': size,
                'consumption': consumption,
                'picture': image_path
            }
        )


        if image_path:
            gpu.picture.name = image_path

        gpu.save()

        logger.info(f"{'Создан' if created else 'Обновлен'} GPU: {model}")
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