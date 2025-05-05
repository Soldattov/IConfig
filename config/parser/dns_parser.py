import os
import django

from IConfigurator import settings
from config.models import ParsedGPU,ParsedCPU
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "IConfigurator.settings")
django.setup()
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../..')

import json
from tqdm import tqdm
from random import randint
from time import sleep as pause
from bs4 import BeautifulSoup
from django.db import transaction
import requests
import logging
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import undetected_chromedriver as uc
import re
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from django.db import connection

# Настройка логгера
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("parser.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('parser_logger')


def download_image(image_url, model):
    if not image_url:
        return None
    try:
        response = requests.get(image_url)
        if response.status_code == 200:
            image_dir = os.path.join(settings.MEDIA_ROOT, 'gpu_images')
            os.makedirs(image_dir, exist_ok=True)
            file_name = f"{model.replace(' ', '_')}.jpg"
            file_path = os.path.join(image_dir, file_name)
            with open(file_path, 'wb') as f:
                f.write(response.content)
            return f'gpu_images/{file_name}'
    except Exception as e:
        logger.error(f"Ошибка при загрузке изображения: {e}")
    return None


def extract_spec_value(soup, spec_name):
    """Ищет характеристику по имени внутри <li class="product-characteristics__spec">"""
    specs = soup.find_all('li', class_='product-characteristics__spec')
    for spec in specs:
        title_block = spec.find('div', class_='product-characteristics__spec-title')
        value_block = spec.find('div', class_='product-characteristics__spec-value')
        if title_block and spec_name in title_block.text:
            return value_block.text.strip() if value_block else None
    return None


def extract_number(text):
    """Извлекает первое число из строки или возвращает 0."""
    match = re.search(r'\d+', text)
    return int(match.group()) if match else 0

def extract_from_description(text, pattern):
    """
    Ищет число по шаблону в описании товара.
    Используем re.IGNORECASE для нечувствительности к регистру.
    """
    match = re.search(pattern, text, re.IGNORECASE)
    return int(float(match.group(1))) if match else 0
#================================Парсер видеокарты=====================================
def parse_gpu_page2(driver, url):
    try:
        logger.info(f"Начинаем парсинг страницы: {url}")
        driver.get(url)
        pause(randint(7, 15))
        
        # Добавляем клик по кнопке "Развернуть все"
        try:
            expand_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "product-characteristics__expand"))
            )
            expand_button.click()
            pause(randint(13, 16))  # Ожидаем загрузку расширенных характеристик
            logger.info("Кликнули на кнопку 'Развернуть все'.")
        except Exception as e:
            logger.warning(f"Не удалось найти или кликнуть на кнопку 'Развернуть все': {e}")
        # Ожидаем появления блока характеристик
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'product-characteristics-content'))
        )
        # Прокручиваем страницу вниз, чтобы динамический контент подгрузился
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        pause(randint(3, 6))
        
        # Извлечение цены (если элемент не найден, используем значение 0)
        price = 0
        timeout = 40  # Максимальное время ожидания (сек)
        interval = randint(4,8)   # Интервал повторных проверок (сек)

        for _ in range(timeout // interval):
            try:
                price_tag = driver.find_element(By.CLASS_NAME, "product-buy__price")
                price = int(price_tag.text.replace(" ", "").replace("₽", ""))
                logger.info(f"Цена найдена: {price} руб")
                break
            except Exception:
                pause(interval)  # Ждем перед повторной проверкой

        # Извлечение изображения: пробуем сначала по селектору с классом ".loaded", иначе – базовый селектор
        image_url = None
        timeout = 30  # Время ожидания (сек)
        interval = 2   # Интервал (сек)

        for _ in range(timeout // interval):
            try:
                main_picture = driver.find_element(By.CSS_SELECTOR, ".header-product__image-img.loaded")
                image_url = main_picture.get_attribute("src")
                if image_url:
                    logger.info(f"Изображение найдено: {image_url}")
                    break
            except Exception:
                pause(interval)  # Ждем перед следующей проверкой

        
        # Извлечение характеристик из таблицы
        tech_spec = {}
        groups = driver.find_elements(By.CLASS_NAME, 'product-characteristics__group')

        for group in groups:
            items = group.find_elements(By.CLASS_NAME, 'product-characteristics__spec')
            for item in items:
                try:
                    spec_name = item.find_element(By.CLASS_NAME, 'product-characteristics__spec-title-content').text.strip()
                    spec_value = item.find_element(By.CLASS_NAME, 'product-characteristics__spec-value').text.strip()
                    tech_spec[spec_name] = spec_value
                    logger.info(f'{spec_name}: {spec_value}')
                except Exception as e:
                    logger.error(f"Ошибка при извлечении характеристики: {e}")
        groups1 = driver.find_elements(By.CSS_SELECTOR, '.product-characteristics__group.product-characteristics__ovh')
        
        logger.info(f"=======================product-characteristics__group product-characteristics__ovh: {groups1}")
        for group in groups1:
            items1 = group.find_elements(By.CLASS_NAME, 'product-characteristics__spec')
            for item in items1:
                try:
                    spec_name = item.find_element(By.CLASS_NAME, 'product-characteristics__spec-title-content').text.strip()
                    spec_value = item.find_element(By.CLASS_NAME, 'product-characteristics__spec-value').text.strip()
                    tech_spec[spec_name] = spec_value
                    logger.info(f'{spec_name}: {spec_value}')
                except Exception as e:
                    logger.error(f"Ошибка при извлечении характеристики: {e}")
        
        
        # Извлечение модели 
        model = tech_spec.get("Модель")
        if not model:
            logger.warning(f"Модель не найдена на странице: {url}")
            
        
        # Скачивание изображения
        image_path = image_url if image_url else download_image(image_url, model)
        
        # Попытка извлечения числовых данных из таблицы
        frequency = extract_number(tech_spec.get("Штатная частота работы видеочипа", "0"))
        memory_amount = extract_number(tech_spec.get("Объем видеопамяти", "0"))
        length = extract_number(tech_spec.get("Длина видеокарты", "0"))
        width = extract_number(tech_spec.get("Ширина видеокарты", "0"))
        thickness = extract_number(tech_spec.get("Толщина видеокарты", "0"))
        consumption = extract_number(tech_spec.get("Рекомендуемый блок питания", "0"))
        relative_power = extract_number(tech_spec.get("Рекомендуемый блок", "0"))
        #tdp = extract_number(tech_spec.get("TDP", "0"))
        size = f'{length}x{width}x{thickness}'
        '''
        # пробуем извлечь из описания товара
       
        if any(val == 0 for val in [frequency, memory_amount, size, consumption, relative_power]):
            soup = BeautifulSoup(driver.page_source, "lxml")
            desc_div = soup.find("div", class_="product-card-description-text")
            if desc_div:
                desc_text = desc_div.get_text(separator=" ", strip=True)
                logger.info(f"Описание товара: {desc_text[:150]}...")
                if frequency == 0:
                    # Пример: "Видеопроцессор работает на частоте 954 МГц"
                    frequency = extract_from_description(desc_text, r"Видеопроцессор\s+работает\s+на\s+частоте\s*(?:[\-–:]?\s*)?([\d\.]+)")
                if memory_amount == 0:
                    # Пример: "ее объем – 2 ГБ"
                    memory_amount = extract_from_description(desc_text, r"объем\s*(?:[\-–:])\s*([\d\.]+)\s*ГБ")
                if consumption == 0:
                    # Пример: "Энергопотребление ... – 19 Вт"
                    consumption = extract_from_description(desc_text, r"Энергопотребление.*?(?:[\-–:])\s*([\d\.]+)\s*Вт")
                if relative_power == 0:
                    # Пример: "с мощностью не меньше 300 Вт"
                    relative_power = extract_from_description(desc_text, r"блок питания.*?(?:не\s+менее|от)\s*([\d\.]+)\s*Вт")
                if size == 0:
                    # Пример: "количество занимаемых слотов расширения – 1"
                    size = extract_from_description(desc_text, r"количество\s+занимаемых\s+слотов(?:\s+расширения)?\s*(?:[\-–:])\s*([\d\.]+)")
        '''
        logger.info(f"Извлеченные числовые характеристики: частота={frequency}, видеопамять={memory_amount}, размер={size}, потребление={consumption}, блок питания={relative_power}")
        
        # Сохраняем данные в базу
        max_attempts = 5  # Количество повторных попыток
        attempt = 0

        while attempt < max_attempts:
            try:
                with transaction.atomic():
                    gpu, created = ParsedGPU.objects.update_or_create(
                        model=model,
                        defaults={
                            'price': str(price),
                            'frequency': str(frequency),
                            'memory_amount': str(memory_amount),
                            'size': str(size),
                            'consumption': str(consumption),
                            #'relative_power': str(relative_power),
                            'picture': str(image_path)
                        }
                    )
                connection.close()
                gpu.save()
                logger.info(f"{'Создан' if created else 'Обновлен'} GPU: {model}")
                break  # Успешное сохранение → выход из цикла
            except Exception as e:
                logger.warning(f"Ошибка доступа к базе (попытка {attempt + 1}): {e}")
                attempt += 1
                time.sleep(2) 
        if image_path:
            gpu.picture.name = image_path
        gpu.save()
        
        logger.info(f"{'Создан' if created else 'Обновлен'} GPU: {model}")
        return gpu
        
    except Exception as e:
        logger.error(f"Ошибка при парсинге страницы {url}: {e}")
        return None
#==============================Парсер процессора=====================================
def parse_cpu_page2(driver, url):
    try:
        logger.info(f"Начинаем парсинг страницы: {url}")
        driver.get(url)
        pause(randint(7, 15))
        
        # Пытаемся кликнуть по кнопке "Развернуть все", если она есть
        try:
            expand_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "product-characteristics__expand"))
            )
            expand_button.click()
            pause(randint(13, 16))
            logger.info("Кликнули на кнопку 'Развернуть все'.")
        except Exception as e:
            logger.warning(f"Не удалось найти или кликнуть на кнопку 'Развернуть все': {e}")
        
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'product-characteristics-content'))
        )
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        pause(randint(3, 6))
        
        # Извлечение цены
        price = 0
        timeout = 40
        interval = randint(4, 8)
        for _ in range(timeout // interval):
            try:
                price_tag = driver.find_element(By.CLASS_NAME, "product-buy__price")
                # Допустим, цена указана аналогично
                price = int(price_tag.text.replace(" ", "").replace("₽", ""))
                logger.info(f"Цена найдена: {price} руб")
                break
            except Exception:
                pause(interval)
        
        # Извлечение изображения (если есть; иначе можно попробовать скачать)
        image_url = None
        timeout = 30
        interval = 2
        for _ in range(timeout // interval):
            try:
                main_picture = driver.find_element(By.CSS_SELECTOR, ".header-product__image-img.loaded")
                image_url = main_picture.get_attribute("src")
                if image_url:
                    logger.info(f"Изображение найдено: {image_url}")
                    break
            except Exception:
                pause(interval)
        
        # Извлечение характеристик из таблицы
        tech_spec = {}
        groups = driver.find_elements(By.CLASS_NAME, 'product-characteristics__group')
        for group in groups:
            items = group.find_elements(By.CLASS_NAME, 'product-characteristics__spec')
            for item in items:
                try:
                    spec_name = item.find_element(By.CLASS_NAME, 'product-characteristics__spec-title-content').text.strip()
                    spec_value = item.find_element(By.CLASS_NAME, 'product-characteristics__spec-value').text.strip()
                    tech_spec[spec_name] = spec_value
                    logger.info(f'{spec_name}: {spec_value}')
                except Exception as e:
                    logger.error(f"Ошибка при извлечении характеристики: {e}")
        
        # Извлечение основных данных. Обязательно проверьте, соответствуют ли имена ключей вашей странице.
        model = tech_spec.get("Модель")
        if not model:
            logger.warning(f"Модель не найдена на странице: {url}")
        
        cores_amount = tech_spec.get("Исполнительные блоки", "")         # если ключ отличается, измените его
        frequency = tech_spec.get("Базовая частота процессора", "0")           # можно применять extract_number, если нужно число
        socket = tech_spec.get("Сокет", "")
        tdp = tech_spec.get("Тепловыделение (TDP)", "") #такого критерия нет
        consumption = tech_spec.get("Потребление", "")
        
        # Скачивание изображения: вместо загрузки можно сохранить ссылку, как для GPU
        image_path = image_url if image_url else download_image(image_url, model)
        
        logger.info(f"Извлеченные характеристики: модель={model}, ядер={cores_amount}, частота={frequency}, сокет={socket}, TDP={tdp}, потребление={consumption}")
        
        # Сохраняем данные в базу
        max_attempts = 5
        attempt = 0
        while attempt < max_attempts:
            try:
                with transaction.atomic():
                    cpu, created = ParsedCPU.objects.update_or_create(
                        model=model,
                        defaults={
                            'price': str(price),
                            'cores_amount': cores_amount,  # уже строка
                            'frequency': frequency,
                            'socket': socket,
                            'tdp': tdp,
                            'consumption': consumption,
                            'relative_power': "0",  # заглушка, расчет можно выполнить позже
                            'picture': str(image_path)
                        }
                    )
                connection.close()
                cpu.save() 
                logger.info(f"{'Создан' if created else 'Обновлен'} CPU: {model}")
                break
            except Exception as e:
                logger.warning(f"Ошибка доступа к базе (CPU, попытка {attempt + 1}): {e}")
                attempt += 1
                time.sleep(2)
        if image_path:
            cpu.picture.name = image_path
        cpu.save()
        logger.info(f"{'Создан' if created else 'Обновлен'} CPU: {model}")
        return cpu

    except Exception as e:
        logger.error(f"Ошибка при парсинге страницы {url}: {e}")
        return None



def save_to_json(data, file_name="parsed_data.json"):
    os.makedirs(os.path.dirname(file_name), exist_ok=True)
    with open(file_name, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
    logger.info(f"Данные сохранены в {file_name}")


def get_urls_from_page(driver):
    soup = BeautifulSoup(driver.page_source, 'lxml')
    elements = soup.find_all('a', class_="catalog-product__name ui-link ui-link_black")
    return ['https://www.dns-shop.ru' + e.get("href") + 'characteristics/' for e in elements]


def main():
    # Запрашиваем у пользователя тип компонента для парсинга: gpu или cpu
    component_choice = input("Выберите тип компонента для парсинга (gpu / cpu): ").strip().lower()
    
    if component_choice == "gpu":
        base_url = 'https://www.dns-shop.ru/catalog/17a89aab16404e77/videokarty/?p={page}'
        parse_page_function = parse_gpu_page2
        get_urls_function = get_urls_from_page  # уже определена для GPU
        component_label = "GPU"
    elif component_choice == "cpu":
        base_url = 'https://www.dns-shop.ru/catalog/17a899cd16404e77/processory/?p={page}'
        parse_page_function = parse_cpu_page2
        get_urls_function = get_urls_from_page  # новая функция для CPU
        component_label = "CPU"
    else:
        print("Неверный выбор. Завершаем парсинг.")
        return

    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = uc.Chrome(version_main=135, options=options)
    page = 1
    parsed_data = []
    max_entries = 100

    while True:
        url = base_url.format(page=page)
        logger.info(f"Открываем страницу каталога: {url}")
        driver.get(url)
        pause(randint(6, 9))

        product_urls = get_urls_function(driver)
        if len(parsed_data) >= max_entries:
            logger.info("Достигнуто 100 записей. Останавливаем парсинг.")
            break

        for product_url in tqdm(product_urls, ncols=70, unit='товаров', colour='blue'):
            # Остановка, если достигнут лимит записей
            if len(parsed_data) >= max_entries:
                logger.info("Достигнуто 100 записей. Останавливаем парсинг.")
                break
            try:
                component_data = parse_page_function(driver, product_url)
                if component_data:
                    parsed_data.append(component_data.model)
                    save_to_json(parsed_data, file_name='parsed.json')
            except Exception as e:
                logger.error(f"Ошибка при обработке {product_url}: {e}")

        page += 1

    driver.quit()
    logger.info("Парсинг завершен.")
    print("Готово!")
