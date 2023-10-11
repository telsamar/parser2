import scrapy
from scrapy_selenium import SeleniumRequest
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
import json
from datetime import datetime
import time
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import queue
import threading
import signal
import sys
from scrapy.exceptions import CloseSpider

def set_permission(drive_service, file_id, email):
    permission = {
        'type': 'user',
        'role': 'writer',
        'emailAddress': email
    }
    try:
        drive_service.permissions().create(fileId=file_id, body=permission).execute()
        print(f"Разрешение установлено для {email}")
    except Exception as e:
        print(f"Ошибка разрешения для {email}. Причина: {e}")

def find_or_create_sheet():
    creds = Credentials.from_service_account_file('ysl_parser/spiders/newtest-401506-8c354a45d760.json',
                                                  scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
    
    drive_service = build('drive', 'v3', credentials=creds)
    sheets_service = build('sheets', 'v4', credentials=creds)

    title = f"WOMAN_9_R5-WEAR-{datetime.now().strftime('%Y-%m')}"

    results = drive_service.files().list(q=f"name='{title}'", fields="files(id, name)").execute()
    items = results.get('files', [])

    if items:
        print(f"Таблица уже существует с ID: {items[0]['id']}")
        file_id = items[0]['id']
        sheet_metadata = sheets_service.spreadsheets().get(spreadsheetId=file_id).execute()
        current_rows = sheet_metadata['sheets'][0]['properties']['gridProperties']['rowCount']
        if current_rows < 30000:
            rows_to_add = 30000 - current_rows

            request = {
                "requests": [
                    {
                        "appendCells": {
                            "sheetId": 0,
                            "rows": [{"values": [{}]} for _ in range(rows_to_add)],
                            "fields": "*"
                        }
                    }
                ]
            }
            sheets_service.spreadsheets().batchUpdate(spreadsheetId=file_id, body=request).execute()
        set_permission(drive_service, file_id, "testarmen4@gmail.com")
        return file_id, creds, sheets_service

    else:
        print("Создание новой таблицы.")
        spreadsheet = {
            'properties': {
                'title': title
            }
        }
        spreadsheet = sheets_service.spreadsheets().create(body=spreadsheet, fields='spreadsheetId').execute()
        file_id = spreadsheet.get("spreadsheetId")
        
        headers = ["Article", "Image 1", "Image 2", "Image 3", "Categories", "Name", 
                   "URL", "Color", "Price", "Old Price", "Currency", "Price, rub.", "Composition", "Sizes", "Description", "Tags", "Date"]
        body = {
            'values': [headers]
        }
        sheets_service.spreadsheets().values().update(spreadsheetId=file_id, range="A1:T1", body=body, valueInputOption="USER_ENTERED").execute()

        current_rows = 1
        rows_to_add = 30000 - current_rows

        set_row_height_request = {
            "updateDimensionProperties": {
                "range": {
                    "sheetId": 0,
                    "dimension": "ROWS",
                    "startIndex": 1,
                },
                "properties": {
                    "pixelSize": 245
                },
                "fields": "pixelSize"
            }
        }

        text_wrap_request = {
            "repeatCell": {
                "range": {
                    "sheetId": 0,
                    "startColumnIndex": 0,
                    "endColumnIndex": 17
                },
                "cell": {
                    "userEnteredFormat": {
                        "wrapStrategy": "WRAP"
                    }
                },
                "fields": "userEnteredFormat.wrapStrategy"
            }
        }

        set_column_width_request = {
            "updateDimensionProperties": {
                "range": {
                    "sheetId": 0,
                    "dimension": "COLUMNS",
                    "startIndex": 0,
                    "endIndex": 17
                },
                "properties": {
                    "pixelSize": 150
                },
                "fields": "pixelSize"
            }
        }

        text_alignment_request = {
            "repeatCell": {
                "range": {
                    "sheetId": 0,
                    "startColumnIndex": 0,
                    "endColumnIndex": 17
                },
                "cell": {
                    "userEnteredFormat": {
                        "horizontalAlignment": "LEFT",
                        "verticalAlignment": "TOP"
                    }
                },
                "fields": "userEnteredFormat.horizontalAlignment,userEnteredFormat.verticalAlignment"
            }
        }

        sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=file_id, 
            body={"requests": [set_column_width_request, set_row_height_request, text_wrap_request, text_alignment_request]}
        ).execute()

        set_permission(drive_service, file_id, "testarmen4@gmail.com")

        return file_id, creds, sheets_service

write_queue = queue.Queue()

def signal_handler(signum, frame):
    write_queue.put(None)
    worker_thread.join()
    raise CloseSpider('Пробуй еще:-)')

def worker():
    while True:
        task = write_queue.get()
        if task is None:
            break
        task()

worker_thread = threading.Thread(target=worker)

class YslSpider(scrapy.Spider):
    name = 'ysl'
    custom_settings = {
        'FEED_FORMAT': 'json',
        'FEED_URI': f"WOMAN_9_R5-WEAR-{datetime.now().strftime('%Y-%m')}.json",
        'FEED_EXPORT_INDENT': 4,
        'LOG_LEVEL': 'INFO',
        'ITEM_PIPELINES': {'ysl_parser.pipelines.JsonWriterPipeline': 1},
    }

    item_count = 0
    current_category = None
    
    def start_requests(self):
        self.file_id, self.creds, self.sheets_service = find_or_create_sheet()
        signal.signal(signal.SIGINT, signal_handler)
        worker_thread.start()
        self.logger.warning("Второй поток начал работу")
        yield SeleniumRequest(url='https://www.ysl.com/en-en', callback=self.parse)

    def parse(self, response):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(response.url)
        time.sleep(5)
        driver.quit()

        parent_li = response.xpath('//button[contains(text(), "SAINT LAURENT WOMEN")]/ancestor::li[@data-ref="item"][1]')
        
        excluded_links = [
            "WINTER 23 LOOKS", "FALL 23 LOOKS", "ALL READY TO WEAR",
            "ALL SHOES", "ALL HANDBAGS", "ALL SMALL LEATHER GOODS",
            "ALL ACCESSORIES", "ALL JEWELRY"
        ]
        for level2_elem in parent_li.xpath('.//li[@data-level2="true"]'):
            upper_level_href = level2_elem.xpath('./a[@data-ref="link"]/@href').get()
            upper_level_text = level2_elem.xpath('./a[@data-ref="link"]/text()|./button[@data-ref="link"]/text()').get().strip()

            if upper_level_href and upper_level_text:
                self.logger.info(f"[UPPER LEVEL] {upper_level_href} - {upper_level_text}")
                yield response.follow(upper_level_href, self.parse_details, meta={'category': [upper_level_text]})

            for li in level2_elem.xpath('.//ul[@data-ref="navlist"]/li'):
                href = li.xpath('./a[@data-ref="link"]/@href').get()
                link_text = li.xpath('./a[@data-ref="link"]/text()').get().strip() if href else None

                if href and link_text and link_text not in excluded_links:
                    self.logger.info(f"[UPPER LEVEL] {upper_level_text}")
                    self.logger.info(f"[LOWER LEVEL] {href} - {link_text}")
                    category_list = [upper_level_text, link_text]
                    yield response.follow(href, self.parse_details, meta={'category': category_list})

    def parse_details(self, response):
        self.current_category = response.meta.get('category', None)
        self.item_count = 0 
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(response.url)
        time.sleep(1)
        last_height = driver.execute_script("return document.body.scrollHeight")

        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            self.logger.warning("Еще листаю")
        self.logger.warning("Долистали до конца")

        source = driver.page_source
        new_response = scrapy.http.HtmlResponse(url=response.url, body=source, encoding='utf-8')
        
        product_divs = new_response.xpath('//div[@class="c-product__inner"]')
        for product_div in product_divs:
            product_link = product_div.xpath('.//a[@class="c-product__link c-product__focus"]/@href').get()
            if product_link:
                self.item_count += 1
                category = response.meta.get('category', None)
                yield response.follow(product_link, self.parse_product_details, meta={'category': category})

        self.logger.info(f"Обработано {self.item_count} предметов из категории {self.current_category}")
        driver.quit()

    def parse_product_details(self, response):
        product_name = response.css('h1.c-product__name::text').get()
        product_link = response.url
        if product_name:
            self.logger.info(f"Product Name: {product_name.strip()}")
            category_list = response.meta.get('category', [])

            article = response.css('span[data-bind="styleMaterialColor"]::text').get().strip()
            description = response.css('p[data-bind="longDescription"]::text').get().strip()
            composition_elements = response.css('li.c-product__detailsitem::text').getall()
            composition = [elem.replace('\n', ' ').strip() for elem in composition_elements if elem.strip() and "%" in elem]
            primary_color = response.css('p.c-product__colorvalue::text').get()

            sizes_divs = response.xpath('//div[@class="c-customselect__menu"]/div')
            sizes_dict = {}
            for div in sizes_divs:
                size_name = div.xpath('.//text()').get().strip()
                if size_name and "YSL" in size_name:
                    sizes_dict[size_name] = {
                        "name": size_name,
                        "quantity": None,
                        "is_available": None,
                        "is_one_size": None
                    }

            sizes_value = sizes_dict if sizes_dict else None

            color_list = []     
            if primary_color:
                color_list.append(primary_color.strip())
            else:
                color_values = response.css('span[data-display-value]::attr(data-display-value)').getall()
                unique_colors = list(set(color_values))
                color_list.extend(unique_colors)

            image_urls = response.css('ul.c-productcarousel__wrapper img.c-product__image::attr(src)').getall()
            unique_image_urls = list(set(image_urls))

            product = {
                        "url": product_link,
                        "categories": category_list,
                        "article": article,
                        "name": product_name.strip(),
                        "color": color_list,
                        "images": unique_image_urls,
                        "price": "-",
                        "old_price": "-",
                        "currency": "-",
                        "description": description,
                        "composition": composition,
                        "sizes": sizes_value,
                    }

            image_formula1 = f'=IMAGE("{product["images"][0]}")' if len(product["images"]) > 0 else "-"
            image_formula2 = f'=IMAGE("{product["images"][1]}")' if len(product["images"]) > 1 else "-"
            image_formula3 = f'=IMAGE("{product["images"][2]}")' if len(product["images"]) > 2 else "-"

            row = [product["article"], 
                image_formula1, image_formula2, image_formula3,
                "; ".join(product["categories"]), product["name"], product["url"],
                "\n".join(product["color"]), product["price"], product["old_price"], product["currency"], "-", 
                " ".join(product["composition"]), "\n".join(product["sizes"]), product["description"], "-", datetime.now().strftime('%d.%m.%Y %H:%M:%S')]

            def update_sheet():
                max_retries = 5
                delay = 13
                for attempt in range(max_retries):
                    try:
                        result = self.sheets_service.spreadsheets().values().get(spreadsheetId=self.file_id, range="A:A").execute()
                        break
                    except Exception as e:
                        if "Quota exceeded" in str(e) and attempt < max_retries - 1:
                            time.sleep(delay)
                        else:
                            raise e
                articles = [item[0] for item in result.get("values", []) if item]
                if product["article"] in articles:
                    row_index = articles.index(product["article"]) + 1
                    for attempt in range(max_retries):
                        try:
                            categories_result = self.sheets_service.spreadsheets().values().get(spreadsheetId=self.file_id, range=f"E{row_index}").execute()
                            break
                        except Exception as e:
                            if "Quota exceeded" in str(e) and attempt < max_retries - 1:
                                time.sleep(delay)
                            else:
                                raise e
                    existing_categories = categories_result.get("values")[0][0].split("; ")
                    combined_categories = list(set(existing_categories + product["categories"]))
                    row[4] = "; ".join(combined_categories)
                    
                    range_name = f"A{row_index}:Q{row_index}"
                else:
                    next_row = len(articles) + 1
                    range_name = f"A{next_row}:Q{next_row}"
                body = {
                    "values": [row]
                }

                for attempt in range(max_retries):
                    try:
                        self.sheets_service.spreadsheets().values().update(spreadsheetId=self.file_id, range=range_name, body=body, valueInputOption="USER_ENTERED").execute()
                        self.logger.info(f"В таблицу успешно добавлено: {product_name.strip()}")
                        break
                    except Exception as e:
                        if "Quota exceeded" in str(e) and attempt < max_retries - 1:
                            time.sleep(delay)
                        else:
                            raise e
                self.item_count += 1 

            write_queue.put(update_sheet)
            yield product
        else:
            self.logger.info("Не найдено такого продукта")

    def closed(self, reason):
        write_queue.put(None)
        self.logger.warning("Второй поток завершил работу")
        worker_thread.join()
