import os
import django
import sys
from config.models import GPU, CPU, Motherboard, RAM, Cooling, PowerSupply, Storage, Case

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "IConfigurator.settings")
django.setup()
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../..')
import pickle

from tqdm import tqdm
from random import randint
from time import sleep as pause
from bs4 import BeautifulSoup
import undetected_chromedriver as uc

import requests
from django.core.files import File
from io import BytesIO

import logging

# Создаем логгер
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


def parse_product_page(driver, url, model_class, fields_to_parse):
    """
    Универсальный парсер для товаров.

    :param driver: WebDriver для загрузки страницы.
    :param url: URL страницы товара.
    :param model_class: Класс модели Django (например, GPU или CPU).
    :param fields_to_parse: Словарь с настройками для парсинга характеристик.
                            Пример: {'model': 'Модель', 'frequency': 'Частота'}
    """
    logger.info(f"начинаем парсинг страницы: {url}")
    driver.get(url)
    pause(randint(7, 11))
    soup = BeautifulSoup(driver.page_source, 'lxml')

    # Словарь для хранения спарсенных данных
    parsed_data = {}

    for field, label in fields_to_parse.items():
        try:
            title = soup.find('span', text=label)
            if title:
                value = title.find_next_sibling('div', class_='product-characteristics__spec-value')
                parsed_data[field] = value.text.strip()
                if value:
                    logger.debug(f"парсинг поля {field}: {value}")
            else:
                logger.warning(f"не удалось найти характеристику {field} на странице {url}")
                parsed_data[field] = None  # Если характеристика не найдена
        except Exception as e:
            logger.error(f"Ошибка при парсинге поля {field}: {e}")
            parsed_data[field] = None

    # Парсинг цены
    price_tag = soup.find('div', class_="product-buy__price")
    if price_tag:
        price_text = price_tag.text.replace(' ', '').replace('₽', '') if price_tag else 0
        try:
            parsed_data['price'] = int(price_text)
            logger.debug(f"парсинг цены: {parsed_data['price']}")
        except ValueError:
            logger.error(f"Некорректная цена: {price_text} на странице {url}")
            parsed_data['price'] = 0
    else:
        logger.warning(f"цена не найдена на странице {url}")
        parsed_data['price'] = 0

    #parsed_data['price'] = int(price_tag.text.replace(' ', '').replace('₽', '')) if price_tag else 0

    # Парсинг изображения
    main_picture = soup.find('img', class_="product-images-slider__main-img")
    if main_picture and main_picture.get('src'):
        image_url = main_picture.get('src')
        parsed_data['picture'] = download_image(image_url)
        logger.debug(f"изображение успешно скачано: {image_url}")
    else:
        logger.warning(f"изображение не найдено на странице {url}")
        parsed_data['picture'] = None
    #image_url = main_picture.get('src') if main_picture else None
    #parsed_data['picture'] = download_image(image_url)

    # Создание объекта модели
    product = model_class.objects.create(
        project=None,  # Если project обязателен, укажите его
        **parsed_data
    )
    logger.info(f"Сохранён {model_class.__name__}: {parsed_data.get('model')}")
    return product

gpu_fields_to_parse = {
    'model': 'Модель',
    'frequency': 'Частота ядра',
    'memory_amount': 'Объем памяти',
    'tdp': 'TDP',
    'size': 'Размер',
    'consumption': 'Потребление'
}

cpu_fields_to_parse = {
    'model': 'Модель',
    'cores_amount': 'Количество ядер',
    'frequency': 'Базовая частота',
    'socket': 'Сокет',
    'tdp': 'TDP',
    'consumption': 'Потребление'
}

motherboard_fields_to_parse = {
    'model': 'модель',
    'chipset': 'Чипсет',
    'form_factor': 'Форм-фактор',
    'socket': 'Сокет',
    'ram_slots': 'Количество слотов RAM',
    'ram_type': 'Тип RAM',
    'nvme_slot': 'Количество слотов NVMe',
    'sata_slot': 'Количество слотов SATA',
    'consumption': 'Потребление'
}

ram_fields_to_parse = {
    'model': 'модель',
    'modules': 'Количество модулей',
    'amount': 'Объем памяти',
    'typee': 'Тип памяти'
}

cooling_fields_to_parse = {
    'model': 'модель',
    'typee': 'Тип охлаждения',
    'socket': 'Сокет',
    'tdp': 'TDP',
    'consumption': 'Потребление',
    'size': 'Размер'
}

power_supply_fields_to_parse = {
    'model': 'модель',
    'power': 'Мощность'
}

storage_fields_to_parse = {
    'model': 'модель',
    'capacity': 'Объем',
    'typee': 'Тип накопителя'
}

case_fields_to_parse = {
    'model': 'Модель',
    'supported_form_factor': 'Форм-фактор совместимых плат',
    'size': 'Размер'
}

def main():
    driver = uc.Chrome()
    try:
        urls_to_parse = {
            'GPU': ('https://www.dns-shop.ru/catalog/17a89aab16404e77/videokarty/?p={page}', gpu_fields_to_parse, GPU),
        'CPU': ('https://www.dns-shop.ru/catalog/17a89a9916404e77/protsessory/?p={page}', cpu_fields_to_parse, CPU),
        'Motherboard': ('https://www.dns-shop.ru/catalog/17a89a8816404e77/materinskie-platy/?p={page}', motherboard_fields_to_parse, Motherboard),
        'RAM': ('https://www.dns-shop.ru/catalog/17a89a7716404e77/operativnaya-pamyat/?p={page}', ram_fields_to_parse, RAM),
        'Cooling': ('https://www.dns-shop.ru/catalog/17a89b3416404e77/sistemy-ohlazhdeniya/?p={page}', cooling_fields_to_parse, Cooling),
        'PowerSupply': ('https://www.dns-shop.ru/catalog/17a89aa516404e77/bloki-pitaniya/?p={page}', power_supply_fields_to_parse, PowerSupply),
        'Storage': ('https://www.dns-shop.ru/catalog/17a89a6616404e77/nakopiteli/?p={page}', storage_fields_to_parse, Storage),
        'Case': ('https://www.dns-shop.ru/catalog/17a89ba716404e77/korpusa/?p={page}', case_fields_to_parse, Case),
        }

        for category, (url_template, fields, model_class) in urls_to_parse.items():
            print(f'Парсинг категории {category}:')
            page = 1
            while True:
                url = url_template.format(page=page)
                driver.get(url)
                pause(randint(6, 9))
                soup = BeautifulSoup(driver.page_source, 'lxml')

                # Получаем ссылки на товары
                items = soup.find_all('a', class_="catalog-product__name ui-link ui-link_black")
                product_urls = [f"https://www.dns-shop.ru{i.get('href')}" for i in items]

                if not product_urls:
                    break

                for product_url in tqdm(product_urls, ncols=70, unit='товаров', colour='blue'):
                    try:
                        parse_product_page(driver, product_url, model_class, fields)
                    except Exception as e:
                        print(f"Ошибка при обработке товара {product_url}: {e}")

                page += 1
    finally:
        driver.quit()  # Гарантированное закрытие браузера
        print('=' * 20)
        print('Все готово!')