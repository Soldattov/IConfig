import os
import django

from IConfigurator import settings
from config.models import (
    ParsedGPU, ParsedCPU, ParsedMotherboard, ParsedRAM,
    ParsedCooling, ParsedPowerSupply, ParsedStorage, ParsedCase
)
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


def download_image(image_url, model, component_type):
    """
    Проверяет доступность изображения по URL и возвращает URL, если изображение доступно.
    
    Args:
        image_url (str): URL изображения для проверки
        model (str): Модель компонента (для логирования)
        component_type (str): Тип компонента (для логирования)
    
    Returns:
        str: URL изображения, если оно доступно, иначе None
    """
    if not image_url:
        return None
    try:
        # Проверяем доступность изображения через HEAD-запрос
        response = requests.head(image_url)
        if response.status_code == 200:
            return image_url
    except Exception as e:
        logger.error(f"Ошибка при проверке изображения для {component_type} {model}: {e}")
    return None


def extract_spec_value(soup, spec_name):
    """
    Ищет значение характеристики по имени в HTML-разметке.
    
    Args:
        soup (BeautifulSoup): Объект BeautifulSoup с HTML-страницей
        spec_name (str): Название искомой характеристики
    
    Returns:
        str: Значение характеристики или None, если не найдено
    """
    specs = soup.find_all('li', class_='product-characteristics__spec')
    for spec in specs:
        title_block = spec.find('div', class_='product-characteristics__spec-title')
        value_block = spec.find('div', class_='product-characteristics__spec-value')
        if title_block and spec_name in title_block.text:
            return value_block.text.strip() if value_block else None
    return None


def extract_number(text):
    """
    Извлекает первое число из строки.
    
    Args:
        text (str): Строка, из которой нужно извлечь число
    
    Returns:
        int: Первое найденное число или 0, если числа не найдены
    """
    match = re.search(r'\d+', text)
    return int(match.group()) if match else 0

def extract_from_description(text, pattern):
    """
    Ищет число по шаблону в описании товара.
    
    Args:
        text (str): Текст описания товара
        pattern (str): Регулярное выражение для поиска числа
    
    Returns:
        int: Найденное число или 0, если не найдено
    """
    match = re.search(pattern, text, re.IGNORECASE)
    return int(float(match.group(1))) if match else 0

#================================Парсер видеокарты=====================================
def parse_gpu_page2(driver, url):
    """
    Парсит страницу видеокарты на DNS.
    
    Args:
        driver: Экземпляр веб-драйвера Selenium
        url (str): URL страницы видеокарты
    
    Returns:
        ParsedGPU: Объект модели с данными видеокарты или None в случае ошибки
    """
    try:
        logger.info(f"Начинаем парсинг страницы: {url}")
        driver.get(url)
        pause(randint(7, 15))
        
        # Пытаемся развернуть все характеристики
        try:
            expand_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "product-characteristics__expand"))
            )
            expand_button.click()
            pause(randint(13, 16))
            logger.info("Кликнули на кнопку 'Развернуть все'.")
        except Exception as e:
            logger.warning(f"Не удалось найти или кликнуть на кнопку 'Развернуть все': {e}")

        # Ждем загрузки характеристик
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'product-characteristics-content'))
        )
        
        # Прокручиваем страницу для загрузки динамического контента
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        pause(randint(3, 6))
        
        # Извлекаем цену
        price = 0
        timeout = 40
        interval = randint(4, 8)
        for _ in range(timeout // interval):
            try:
                price_tag = driver.find_element(By.CLASS_NAME, "product-buy__price")
                price = int(price_tag.text.replace(" ", "").replace("₽", ""))
                logger.info(f"Цена найдена: {price} руб")
                break
            except Exception:
                pause(interval)

        # Извлекаем изображение
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

        # Извлекаем характеристики
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

        # Поиск в скрытых группах характеристик
        groups1 = driver.find_elements(By.CSS_SELECTOR, '.product-characteristics__group.product-characteristics__ovh')
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

        # Извлекаем основные данные
        model = tech_spec.get("Модель")
        if not model:
            logger.warning(f"Модель не найдена на странице: {url}")
            return None

        # Извлекаем числовые характеристики
        frequency = extract_number(tech_spec.get("Штатная частота работы видеочипа", "0"))
        memory_amount = extract_number(tech_spec.get("Объем видеопамяти", "0"))
        length = extract_number(tech_spec.get("Длина видеокарты", "0"))
        width = extract_number(tech_spec.get("Ширина видеокарты", "0"))
        thickness = extract_number(tech_spec.get("Толщина видеокарты", "0"))
        consumption = extract_number(tech_spec.get("Рекомендуемый блок питания", "0"))
        size = f'{length} x {width} x {thickness}'

        # Получаем URL изображения
        image_path = download_image(image_url, model, 'gpu')
        
        # Сохраняем данные в базу
        max_attempts = 5
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
                            'picture': str(image_path),
                            'source_url': url
                        }
                    )
                connection.close()
                gpu.save()
                logger.info(f"{'Создан' if created else 'Обновлен'} GPU: {model}")
                break
            except Exception as e:
                logger.warning(f"Ошибка доступа к базе (попытка {attempt + 1}): {e}")
                attempt += 1
                time.sleep(2)

        if image_path:
            gpu.picture = image_path
        gpu.save()
        
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

        groups1 = driver.find_elements(By.CSS_SELECTOR, '.product-characteristics__group.product-characteristics__ovh')

        logger.info(f"=======================product-characteristics__group product-characteristics__ovh: {groups1}")
        # Извлечение основных данных. Обязательно проверьте, соответствуют ли имена ключей вашей странице.
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

        model = tech_spec.get("Модель")
        if not model:
            logger.warning(f"Модель не найдена на странице: {url}")
        
        cores_amount = tech_spec.get("Общее количество ядер", "6")         # если ключ отличается, измените его
        frequency = tech_spec.get("Базовая частота процессора", "3.5 ГГц")           # можно применять extract_number, если нужно число
        socket = tech_spec.get("Сокет", "")
        tdp = tech_spec.get("Тепловыделение (TDP)", "60 Вт") #такого критерия нет
        
        # Получаем URL изображения
        image_path = download_image(image_url, model, 'cpu')
        
        logger.info(f"Извлеченные характеристики: модель={model}, ядер={cores_amount}, частота={frequency}, сокет={socket}, TDP={tdp}")
        
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
                            'frequency': str(frequency),
                            'cores_amount': str(cores_amount),
                            'socket': str(socket),
                            'tdp': str(tdp),
                            'picture': str(image_path),
                            'source_url': url
                        }
                    )
                connection.close()
                cpu.save()
                logger.info(f"{'Создан' if created else 'Обновлен'} CPU: {model}")
                break  # Успешное сохранение → выход из цикла

            except Exception as e:
                logger.warning(f"Ошибка доступа к базе (CPU, попытка {attempt + 1}): {e}")
                attempt += 1
                time.sleep(2)  # Увеличиваем время ожидания между попытками
        if image_path:
            cpu.picture = image_path
        cpu.save()

        logger.info(f"{'Создан' if created else 'Обновлен'} CPU: {model}")
        return cpu

    except Exception as e:
        logger.error(f"Ошибка при парсинге страницы {url}: {e}")
        return None


def parse_motherboard_page(driver, url):
    try:
        logger.info(f"Начинаем парсинг страницы материнской платы: {url}")
        driver.get(url)
        pause(randint(7, 15))

        try:
            expand_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "product-characteristics__expand"))
            )
            expand_button.click()
            pause(randint(13, 16))
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
                price = int(price_tag.text.replace(" ", "").replace("₽", ""))
                logger.info(f"Цена найдена: {price} руб")
                break
            except Exception:
                pause(interval)

        # Извлечение изображения
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

        # Извлечение характеристик
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

        # Поиск в скрытых группах
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

        model = tech_spec.get("Модель")
        if not model:
            logger.warning(f"Модель не найдена на странице: {url}")
            return None

        form_factor = tech_spec.get("Форм-фактор", "")
        socket = tech_spec.get("Сокет", "")
        ram_slots = tech_spec.get("Количество слотов памяти", "2")
        ram_type = tech_spec.get("Тип поддерживаемой памяти", "")
        nvme_slot = tech_spec.get("Количество разъемов M.2", "0")
        sata_slot = tech_spec.get("Количество портов SATA", "0")

        # Получаем URL изображения
        image_path = download_image(image_url, model, 'motherboard')

        # Сохранение в базу
        max_attempts = 5
        attempt = 0
        while attempt < max_attempts:
            try:
                with transaction.atomic():
                    motherboard, created = ParsedMotherboard.objects.update_or_create(
                        model=model,
                        defaults={
                            'price': str(price),
                            'form_factor': str(form_factor),
                            'socket': str(socket),
                            'ram_slots': str(ram_slots),
                            'ram_type': str(ram_type),
                            'nvme_slot': str(nvme_slot),
                            'sata_slot': str(sata_slot),
                            'picture': str(image_path),
                            'source_url': url
                        }
                    )
                connection.close()
                motherboard.save()
                logger.info(f"{'Создан' if created else 'Обновлен'} Motherboard: {model}")
                break
            except Exception as e:
                logger.warning(f"Ошибка доступа к базе (Motherboard, попытка {attempt + 1}): {e}")
                attempt += 1
                time.sleep(2)
        if image_path:
            motherboard.picture = image_path
        motherboard.save()
        return motherboard

    except Exception as e:
        logger.error(f"Ошибка при парсинге страницы {url}: {e}")
        return None


def parse_ram_page(driver, url):
    try:
        logger.info(f"Начинаем парсинг страницы RAM: {url}")
        driver.get(url)
        pause(randint(7, 15))

        try:
            expand_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "product-characteristics__expand"))
            )
            expand_button.click()
            pause(randint(13, 16))
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
                price = int(price_tag.text.replace(" ", "").replace("₽", ""))
                logger.info(f"Цена найдена: {price} руб")
                break
            except Exception:
                pause(interval)

        # Извлечение изображения
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

        # Извлечение характеристик
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

        # Поиск в скрытых группах
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

        model = tech_spec.get("Модель")
        if not model:
            logger.warning(f"Модель не найдена на странице: {url}")
            return None

        modules = tech_spec.get("Количество модулей в комплекте", "1")
        amount = tech_spec.get("Суммарный объем памяти всего комплекта", "")
        typee = tech_spec.get("Тип памяти", "")

        # Получаем URL изображения
        image_path = download_image(image_url, model, 'ram')

        # Сохранение в базу
        max_attempts = 5
        attempt = 0
        while attempt < max_attempts:
            try:
                with transaction.atomic():
                    ram, created = ParsedRAM.objects.update_or_create(
                        model=model,
                        defaults={
                            'price': str(price),
                            'modules': str(modules),
                            'amount': str(amount),
                            'typee': str(typee),
                            'picture': str(image_path),
                            'source_url': url
                        }
                    )
                connection.close()
                ram.save()
                logger.info(f"{'Создан' if created else 'Обновлен'} RAM: {model}")
                break
            except Exception as e:
                logger.warning(f"Ошибка доступа к базе (RAM, попытка {attempt + 1}): {e}")
                attempt += 1
                time.sleep(2)
        if image_path:
            ram.picture = image_path
        ram.save()
        return ram

    except Exception as e:
        logger.error(f"Ошибка при парсинге страницы {url}: {e}")
        return None


def parse_cooling_page(driver, url):
    try:
        logger.info(f"Начинаем парсинг страницы системы охлаждения: {url}")
        driver.get(url)
        pause(randint(7, 15))

        try:
            expand_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "product-characteristics__expand"))
            )
            expand_button.click()
            pause(randint(13, 16))
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
                price = int(price_tag.text.replace(" ", "").replace("₽", ""))
                logger.info(f"Цена найдена: {price} руб")
                break
            except Exception:
                pause(interval)

        # Извлечение изображения
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

        # Извлечение характеристик
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

        # Поиск в скрытых группах
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

        model = tech_spec.get("Модель")
        if not model:
            logger.warning(f"Модель не найдена на странице: {url}")
            return None

        typee = tech_spec.get("Тип конструкции", "башенный")
        socket = tech_spec.get("Сокет", "")
        tdp = tech_spec.get("Рассеиваемая мощность", "70")
        length = tech_spec.get("Длина", "70")
        width = tech_spec.get("Ширина", "100")
        height = tech_spec.get("Высота", "140")
        size = f"{length} x {width} x {height}"
        backlight = tech_spec.get("Тип подсветки", "нет")

        # Получаем URL изображения
        image_path = download_image(image_url, model, 'cooling')

        # Сохранение в базу
        max_attempts = 5
        attempt = 0
        while attempt < max_attempts:
            try:
                with transaction.atomic():
                    cooling, created = ParsedCooling.objects.update_or_create(
                        model=model,
                        defaults={
                            'price': str(price),
                            'typee': str(typee),
                            'socket': str(socket),
                            'tdp': str(tdp),
                            'size': str(size),
                            'backlight': str(backlight),
                            'picture': str(image_path),
                            'source_url': url
                        }
                    )
                connection.close()
                cooling.save()
                logger.info(f"{'Создан' if created else 'Обновлен'} Cooling: {model}")
                break
            except Exception as e:
                logger.warning(f"Ошибка доступа к базе (Cooling, попытка {attempt + 1}): {e}")
                attempt += 1
                time.sleep(2)
        if image_path:
            cooling.picture = image_path
        cooling.save()
        return cooling

    except Exception as e:
        logger.error(f"Ошибка при парсинге страницы {url}: {e}")
        return None


def parse_power_supply_page(driver, url):
    try:
        logger.info(f"Начинаем парсинг страницы блока питания: {url}")
        driver.get(url)
        pause(randint(7, 15))

        try:
            expand_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "product-characteristics__expand"))
            )
            expand_button.click()
            pause(randint(13, 16))
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
                price = int(price_tag.text.replace(" ", "").replace("₽", ""))
                logger.info(f"Цена найдена: {price} руб")
                break
            except Exception:
                pause(interval)

        # Извлечение изображения
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

        # Извлечение характеристик
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

        # Поиск в скрытых группах
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

        model = tech_spec.get("Модель")
        if not model:
            logger.warning(f"Модель не найдена на странице: {url}")
            return None

        power = tech_spec.get("Мощность (номинал)", "")

        # Получаем URL изображения
        image_path = download_image(image_url, model, 'powersupply')

        # Сохранение в базу
        max_attempts = 5
        attempt = 0
        while attempt < max_attempts:
            try:
                with transaction.atomic():
                    power_supply, created = ParsedPowerSupply.objects.update_or_create(
                        model=model,
                        defaults={
                            'price': str(price),
                            'power': str(power),
                            'picture': str(image_path),
                            'source_url': url
                        }
                    )
                connection.close()
                power_supply.save()
                logger.info(f"{'Создан' if created else 'Обновлен'} PowerSupply: {model}")
                break
            except Exception as e:
                logger.warning(f"Ошибка доступа к базе (PowerSupply, попытка {attempt + 1}): {e}")
                attempt += 1
                time.sleep(2)
        if image_path:
            power_supply.picture = image_path
        power_supply.save()
        return power_supply

    except Exception as e:
        logger.error(f"Ошибка при парсинге страницы {url}: {e}")
        return None


def parse_storage_page(driver, url):
    try:
        logger.info(f"Начинаем парсинг страницы накопителя: {url}")
        driver.get(url)
        pause(randint(7, 15))

        try:
            expand_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "product-characteristics__expand"))
            )
            expand_button.click()
            pause(randint(13, 16))
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
                price = int(price_tag.text.replace(" ", "").replace("₽", ""))
                logger.info(f"Цена найдена: {price} руб")
                break
            except Exception:
                pause(interval)

        # Извлечение изображения
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

        # Извлечение характеристик
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

        # Поиск в скрытых группах
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

        model = tech_spec.get("Модель")
        if not model:
            logger.warning(f"Модель не найдена на странице: {url}")
            return None

        capacity = tech_spec.get("Объем накопителя", "256 Гб")
        typee = tech_spec.get("Тип", "SSD")

        # Получаем URL изображения
        image_path = download_image(image_url, model, 'storage')

        # Сохранение в базу
        max_attempts = 5
        attempt = 0
        while attempt < max_attempts:
            try:
                with transaction.atomic():
                    storage, created = ParsedStorage.objects.update_or_create(
                        model=model,
                        defaults={
                            'price': str(price),
                            'capacity': str(capacity),
                            'typee': str(typee),
                            'picture': str(image_path),
                            'source_url': url
                        }
                    )
                connection.close()
                storage.save()
                logger.info(f"{'Создан' if created else 'Обновлен'} Storage: {model}")
                break
            except Exception as e:
                logger.warning(f"Ошибка доступа к базе (Storage, попытка {attempt + 1}): {e}")
                attempt += 1
                time.sleep(2)
        if image_path:
            storage.picture = image_path
        storage.save()
        return storage

    except Exception as e:
        logger.error(f"Ошибка при парсинге страницы {url}: {e}")
        return None


def parse_case_page(driver, url):
    try:
        logger.info(f"Начинаем парсинг страницы корпуса: {url}")
        driver.get(url)
        pause(randint(7, 15))

        try:
            expand_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "product-characteristics__expand"))
            )
            expand_button.click()
            pause(randint(13, 16))
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
                price = int(price_tag.text.replace(" ", "").replace("₽", ""))
                logger.info(f"Цена найдена: {price} руб")
                break
            except Exception:
                pause(interval)

        # Извлечение изображения
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

        # Извлечение характеристик
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

        # Поиск в скрытых группах
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

        model = tech_spec.get("Модель")
        if not model:
            logger.warning(f"Модель не найдена на странице: {url}")
            return None

        supported_form_factor = tech_spec.get("Форм-фактор совместимых плат", "")
        length = tech_spec.get("Длина", "70")
        width = tech_spec.get("Ширина", "100")
        height = tech_spec.get("Высота", "140")
        size = f"{length} x {width} x {height}"
        backlight = tech_spec.get("Тип подсветки", "")

        # Получаем URL изображения
        image_path = download_image(image_url, model, 'case')

        # Сохранение в базу
        max_attempts = 5
        attempt = 0
        while attempt < max_attempts:
            try:
                with transaction.atomic():
                    case, created = ParsedCase.objects.update_or_create(
                        model=model,
                        defaults={
                            'price': str(price),
                            'supported_form_factor': str(supported_form_factor),
                            'size': str(size),
                            'backlight': str(backlight),
                            'picture': str(image_path),
                            'source_url': url
                        }
                    )
                connection.close()
                case.save()
                logger.info(f"{'Создан' if created else 'Обновлен'} Case: {model}")
                break
            except Exception as e:
                logger.warning(f"Ошибка доступа к базе (Case, попытка {attempt + 1}): {e}")
                attempt += 1
                time.sleep(2)
        if image_path:
            case.picture = image_path
        case.save()
        return case

    except Exception as e:
        logger.error(f"Ошибка при парсинге страницы {url}: {e}")
        return None


def save_to_json(data, file_name="parsed_data.json"):
    """
    Сохраняет данные в JSON-файл.
    
    Args:
        data: Данные для сохранения
        file_name (str): Имя файла для сохранения
    """
    os.makedirs(os.path.dirname(file_name), exist_ok=True)
    with open(file_name, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
    logger.info(f"Данные сохранены в {file_name}")


def get_urls_from_page(driver):
    """
    Получает список URL-адресов товаров со страницы каталога.
    
    Args:
        driver: Экземпляр веб-драйвера Selenium
    
    Returns:
        list: Список URL-адресов товаров
    """
    try:
        # Добавляем параметр сортировки по популярности
        current_url = driver.current_url
        if '?' in current_url:
            if 'order=popular' not in current_url:
                current_url += '&order=popular'
        else:
            current_url += '?order=popular'
        driver.get(current_url)
        
        # Ждем загрузки страницы
        WebDriverWait(driver, randint(5, 8)).until(
            EC.presence_of_element_located((By.CLASS_NAME, "catalog-product"))
        )
        
        # Прокручиваем страницу для загрузки всех элементов
        for _ in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            pause(randint(2, 4))
        
        # Пробуем разные селекторы для поиска ссылок
        selectors = [
            "a.catalog-product__name.ui-link.ui-link_black",
            "a.catalog-product__name",
            "a.ui-link.ui-link_black",
            "a.catalog-product__link",
            "a.catalog-product__name-link",
            "a.product-card-top__name"
        ]
        
        urls = []
        for selector in selectors:
            try:
                elements = WebDriverWait(driver, 5).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                )
                if elements:
                    for element in elements:
                        try:
                            href = element.get_attribute("href")
                            if href:
                                if not href.endswith('characteristics/'):
                                    href = href + 'characteristics/'
                                urls.append(href)
                        except Exception as e:
                            logger.warning(f"Ошибка при получении URL: {e}")
                            continue
                    
                    if urls:
                        logger.info(f"Найдено {len(urls)} товаров на странице")
                        return urls
            except Exception as e:
                logger.warning(f"Не удалось найти элементы по селектору {selector}: {e}")
                continue
        
        # Если селекторы не сработали, пробуем через BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'lxml')
        elements = soup.find_all('a', class_=lambda x: x and ('catalog-product__name' in x or 'ui-link_black' in x or 'product-card-top__name' in x))
        for element in elements:
            href = element.get('href')
            if href:
                if not href.startswith('http'):
                    href = 'https://www.dns-shop.ru' + href
                if not href.endswith('characteristics/'):
                    href = href + 'characteristics/'
                urls.append(href)
        
        if urls:
            logger.info(f"Найдено {len(urls)} товаров на странице через BeautifulSoup")
            return urls
        
        logger.error("Не удалось найти ссылки на товары на странице")
        return []
        
    except Exception as e:
        logger.error(f"Ошибка при получении URL-адресов: {e}")
        return []


def parse_with_retry(driver, url, parse_function):
    """
    Выполняет парсинг с повторными попытками в случае ошибки.
    
    Args:
        driver: Экземпляр веб-драйвера Selenium
        url (str): URL страницы для парсинга
        parse_function: Функция для парсинга
    
    Returns:
        Результат выполнения parse_function или None в случае ошибки
    """
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            return parse_function(driver, url)
        except Exception as e:
            logger.error(f"Ошибка при парсинге (попытка {attempt + 1}): {e}")
            if attempt == max_attempts - 1:
                return None
            # Очищаем куки и кэш
            driver.delete_all_cookies()
            driver.execute_script("window.localStorage.clear();")
            driver.execute_script("window.sessionStorage.clear();")
            pause(randint(10, 15))


def main():
    """
    Основная функция парсера.
    Запрашивает тип компонента у пользователя и запускает парсинг.
    """
    # Запрашиваем тип компонента для парсинга
    component_choice = input("Выберите тип компонента для парсинга (gpu / cpu / ram / mother / storage / psu / cooler / case): ").strip().lower()
    
    # Определяем параметры парсинга в зависимости от выбранного компонента
    if component_choice == "gpu":
        base_url = 'https://www.dns-shop.ru/catalog/17a89aab16404e77/videokarty/?order=popular&p={page}'
        parse_page_function = parse_gpu_page2
        get_urls_function = get_urls_from_page
        component_label = "GPU"
    elif component_choice == "cpu":
        base_url = 'https://www.dns-shop.ru/catalog/17a899cd16404e77/processory/?order=popular&p={page}'
        parse_page_function = parse_cpu_page2
        get_urls_function = get_urls_from_page
        component_label = "CPU"
    elif component_choice == "ram":
        base_url = 'https://www.dns-shop.ru/catalog/17a89a3916404e77/operativnaya-pamyat-dimm/?order=popular&p={page}'
        parse_page_function = parse_ram_page
        get_urls_function = get_urls_from_page
        component_label = "RAM"
    elif component_choice == "mother":
        base_url = 'https://www.dns-shop.ru/catalog/17a89a0416404e77/materinskie-platy/?order=popular&p={page}'
        parse_page_function = parse_motherboard_page
        get_urls_function = get_urls_from_page
        component_label = "Motherboard"
    elif component_choice == "storage":
        base_url = 'https://www.dns-shop.ru/catalog/8a9ddfba20724e77/ssd-nakopiteli/?order=popular&p={page}'
        parse_page_function = parse_storage_page
        get_urls_function = get_urls_from_page
        component_label = "Storage"
    elif component_choice == "psu":
        base_url = 'https://www.dns-shop.ru/catalog/17a89c2216404e77/bloki-pitaniya/?order=popular&p={page}'
        parse_page_function = parse_power_supply_page
        get_urls_function = get_urls_from_page
        component_label = "Power Supply"
    elif component_choice == "cooler":
        base_url = 'https://www.dns-shop.ru/catalog/17a9cc2d16404e77/kulery-dlya-processorov/?order=popular&p={page}'
        parse_page_function = parse_cooling_page
        get_urls_function = get_urls_from_page
        component_label = "Cooling"
    elif component_choice == "case":
        base_url = 'https://www.dns-shop.ru/catalog/17a89c5616404e77/korpusa/?order=popular&p={page}'
        parse_page_function = parse_case_page
        get_urls_function = get_urls_from_page
        component_label = "Case"
    else:
        print("Неверный выбор. Завершаем парсинг.")
        return

    # Настраиваем драйвер
    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = uc.Chrome(version_main=135, options=options)
    page = 1
    parsed_data = []
    max_entries = 100

    # Основной цикл парсинга
    while True:
        url = base_url.format(page=page)
        logger.info(f"Открываем страницу каталога: {url}")
        driver.get(url)
        pause(randint(6, 9))

        # Получаем URL'ы товаров на странице
        product_urls = get_urls_function(driver)
        if len(parsed_data) >= max_entries:
            logger.info("Достигнуто 100 записей. Останавливаем парсинг.")
            break

        # Парсим каждый товар
        for product_url in tqdm(product_urls, ncols=70, unit='товаров', colour='blue'):
            if len(parsed_data) >= max_entries:
                logger.info("Достигнуто 100 записей. Останавливаем парсинг.")
                break
            try:
                component_data = parse_with_retry(driver, product_url, parse_page_function)
                if component_data:
                    parsed_data.append(component_data.model)
                    save_to_json(parsed_data, file_name='parsed.json')
            except Exception as e:
                logger.error(f"Ошибка при обработке {product_url}: {e}")

        page += 1

    driver.quit()
    logger.info("Парсинг завершен.")
    print("Готово!")

if __name__ == "__main__":
    main()
