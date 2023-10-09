import scrapy
from scrapy_selenium import SeleniumRequest
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
import json
import datetime
import time
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

class YslSpider(scrapy.Spider):
    name = 'ysl'
    custom_settings = {
        'FEED_FORMAT': 'json',
        'FEED_URI': f"WOMANn-WEAR-{datetime.datetime.now().strftime('%Y-%m')}.json",
        'FEED_EXPORT_INDENT': 4,
        'LOG_LEVEL': 'INFO',
        'ITEM_PIPELINES': {'ysl_parser.pipelines.JsonWriterPipeline': 1},
    }

    item_count = 0
    current_category = None
    
    def start_requests(self):
        yield SeleniumRequest(url='https://www.ysl.com/en-en', callback=self.parse)

    def parse(self, response):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(response.url)
        time.sleep(5)
        driver.quit()

        parent_li = response.xpath('//button[contains(text(), "SAINT LAURENT WOMEN")]/ancestor::li[@data-ref="item"][1]')
        
        for level2_elem in parent_li.xpath('.//li[@data-level2="true"]'):
            upper_level_href = level2_elem.xpath('./a[@data-ref="link"]/@href').get()
            upper_level_text = level2_elem.xpath('./a[@data-ref="link"]/text()|./button[@data-ref="link"]/text()').get().strip()

            if upper_level_href and upper_level_text:
                self.logger.info(f"[UPPER LEVEL] {upper_level_href} - {upper_level_text}")
                yield response.follow(upper_level_href, self.parse_details, meta={'category': [upper_level_text]})

            for li in level2_elem.xpath('.//ul[@data-ref="navlist"]/li'):
                href = li.xpath('./a[@data-ref="link"]/@href').get()
                link_text = li.xpath('./a[@data-ref="link"]/text()').get().strip() if href else None

                if href and link_text:
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

        self.logger.info(f"Processed {self.item_count} items for category {self.current_category}")
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
            composition = [elem.replace('\n', ' ').strip() for elem in composition_elements if elem.strip()]
            primary_color = response.css('p.c-product__colorvalue::text').get()

            sizes_divs = response.xpath('//div[@class="c-customselect__menu"]/div')
            sizes_dict = {}
            for div in sizes_divs:
                size_name = div.xpath('.//text()').get().strip()
                if size_name and "YSL" in size_name:  # это может помочь фильтровать ненужные элементы, если такие есть
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
                        "price": None,
                        "old_price": None,
                        "currency": None,
                        "description": description,
                        "composition": composition,
                        "sizes": sizes_value,
                    }
                    
            self.item_count += 1 
            yield product
        else:
            self.logger.info("Не найдено такого продукта")