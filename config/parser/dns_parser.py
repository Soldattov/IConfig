import os
import django
from config.models import GPU, CPU, Motherboard, RAM, Cooling, PowerSupply, Storage, Case

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "IConfigurator.settings")
django.setup()

import pickle
import sys

from tqdm import tqdm
from random import randint
from time import sleep as pause
from bs4 import BeautifulSoup
import undetected_chromedriver as uc

import requests
from django.core.files import File
from io import BytesIO

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

def parse_gpu_page(driver, url):
    """ Парсит страницу товара по ссылке. """
    driver.get(url)
    pause(randint(7, 11))
    soup = BeautifulSoup(driver.page_source, 'lxml')

    model = soup.find('div', text='модель', class_="product-card-description__title").text.strip()
    price = int(soup.find('div', class_="product-buy__price").text.replace(' ', '').replace('₽', ''))
    #manufacturer = soup.find('span', text='Производитель').find_next('div').text.strip()
    #core = soup.find('span', text='графический процессор').find_next('div').text.strip()
    #line = soup.find('span', text='линейка производителя видеокарты').find_next('div').text.strip()
    frequency = int(soup.find('span', text='Частота ядра').find_next('div').text.strip().split()[0])
    memory_amount = int(soup.find('span', text='Объем памяти').find_next('div').text.strip().split()[0])
    tdp = int(soup.find('span', text='TDP').find_next('div').text.strip().split()[0])
    size = int(soup.find('span', text='Размер').find_next('div').text.strip().split()[0])
    consumption = int(soup.find('span', text='Потребление').find_next('div').text.strip().split()[0])
    main_picture = soup.find('img', class_="product-images-slider__main-img")
    image_url = main_picture.get('src') if main_picture else  None
    image_file = download_image(image_url)

    # Создание объекта GPU
    gpu = GPU.objects.create(
        project=None,  # Если project обязателен, укажите его
        model=model,
        frequency=frequency,
        memory_amount=memory_amount,
        image=image_file,
        tdp=tdp,
        size=size,
        consumption=consumption,
        price=price
    )
    gpu.save()
    print(f"Сохранён GPU: {gpu.model}")
    return gpu




    pictures_list = []
    for i in pictures_soup:
        _ = pictures_list.append(i.get('data-src'))
        if _ is not None:
            pictures_list.append(_)

    span_tags = soup.find_all('span')
    for i in span_tags:
        if bool(str(i).find('data-go-back-catalog') != -1):
            category = i

    tech_spec = {}
    for f1, f2 in zip(charcs, cvalue):
        tech_spec[f1.text.rstrip().lstrip()] = f2.text.rstrip().lstrip()

    notebook = {}

    notebook["Категория"] = category.text.lstrip(': ')
    notebook["Наименование"] = name.text[15:]
    notebook["Цена"] = int(price.text.replace(' ', '')[:-1])
    notebook["Доступность"] = avail.text if avail is not None else 'Товара нет в наличии'
    notebook["Ссылка на товар"] = url
    notebook["Описание"] = desc.text
    notebook["Главное изображение"] = main_picture.get('src') if main_picture is not None else 'У товара нет картинок'
    notebook["Лист с картинками"] = pictures_list
    notebook["Характеристики"] = list(tech_spec.items())

    # for i, j in notebook.items():
    #     print(i, j)
    return notebook

def parse_cpu_page(driver, url):
    """ Парсит страницу процессора по ссылке. """
    driver.get(url)
    pause(randint(7, 11))
    soup = BeautifulSoup(driver.page_source, 'lxml')

    # Извлечение данных
    model = soup.find('span', text='Модель').find_next('div').text.strip()
    frequency = int(soup.find('span', text='Базовая частота').find_next('div').text.strip().split()[0])
    cores = int(soup.find('span', text='Количество ядер').find_next('div').text.strip())
    threads = int(soup.find('span', text='Количество потоков').find_next('div').text.strip())
    socket = soup.find('span', text='Сокет').find_next('div').text.strip()
    price = int(soup.find('div', class_="product-buy__price").text.replace(' ', '').replace('₽', ''))
    main_picture = soup.find('img', class_="product-images-slider__main-img")
    image_url = main_picture.get('src') if main_picture else None

    # Скачивание изображения
    image_file = download_image(image_url)

    # Создание объекта CPU
    cpu = CPU.objects.create(
        project=None,
        model=model,
        frequency=frequency,
        cores=cores,
        threads=threads,
        socket=socket,
        price=price,
        picture=image_file
    )
    print(f"Сохранён CPU: {cpu.model}")
    return cpu

def get_all_category_page_urls(driver, url_to_parse):
    """ Получаем URL категории и парсим ссылки с неё."""
    page = 1
    url = url_to_parse.format(page=page)
    driver.get(url=url)
    pause(10)

    soup = BeautifulSoup(driver.page_source, 'lxml')

    span_tags = soup.find_all('span')
    for i in span_tags:
        if bool(str(i).find('data-role="items-count"') != -1):
            number_of_pages = [int(x) for x in str(i) if x.isdigit()]

    res = int(''.join(map(str, number_of_pages)))
    pages_total = ((res // 18) + 1)
    print(f'Всего в категории {pages_total} страницы')

    urls = []

    while True:
        page_urls = get_urls_from_page(driver)
        urls += page_urls

        if page >= pages_total:
            break

        page += 1
        url = url_to_parse.format(page=page)
        driver.get(url)
        pause(randint(6, 9))

    return urls


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
        'https://www.dns-shop.ru/catalog/17a89a9916404e77/protsessory/?p={page}',
    ]

    for index, url in enumerate(urls_to_parse):
        print(f'Парсинг категории {index + 1}:')
        parsed_urls = get_all_category_page_urls(driver, url)

        for product_url in tqdm(parsed_urls, ncols=70, unit='товаров', colour='blue'):
            try:
                parse_cpu_page(driver, product_url)
            except Exception as e:
                print(f"Ошибка при обработке товара {product_url}: {e}")

    driver.quit()
    print('=' * 20)
    print('Все готово!')

    urls = []
    for index, url in enumerate(urls_to_parse):
        print(f'Получение списка всех ссылок из {index+1} категории:')
        parsed_url = get_all_category_page_urls(driver, url)
        urls.append(parsed_url)

    print("Запись всех ссылок в файл url.txt:")
    with open('urls.txt', 'w') as file:
        for url in urls:
            for link in url:
                file.write(link + "\n")

if __name__ == '__main__':
    main()
    print('=' * 20)
    print('Все готово!')