import scrapy
from scrapy_selenium import SeleniumRequest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import json
import datetime
import time

class YslSpider(scrapy.Spider):
    name = 'ysl'
    custom_settings = {
        'FEED_FORMAT': 'json',
        'FEED_URI': f"WOMAN-WEAR-{datetime.datetime.now().strftime('%Y-%m')}.json",
        'FEED_EXPORT_INDENT': 4,
        'LOG_LEVEL': 'INFO',
    }
    item_count = 0
    current_category = None
    
    def start_requests(self):
        yield SeleniumRequest(url='https://www.ysl.com/en-en', callback=self.parse)

    def parse(self, response):
        parent_li = response.xpath('//button[contains(text(), "SAINT LAURENT WOMEN")]/ancestor::li[@data-ref="item"][1]')
        
        for level2_elem in parent_li.xpath('.//li[@data-level2="true"]'):
            upper_level_href = level2_elem.xpath('./a[@data-ref="link"]/@href').get()
            upper_level_text = level2_elem.xpath('./a[@data-ref="link"]/text()|./button[@data-ref="link"]/text()').get().strip()

            if upper_level_href and upper_level_text:
                self.logger.info(f"[UPPER LEVEL] {upper_level_href} - {upper_level_text}")
                yield response.follow(upper_level_href, self.parse_details, meta={'category': upper_level_text})

            for li in level2_elem.xpath('.//ul[@data-ref="navlist"]/li'):
                href = li.xpath('./a[@data-ref="link"]/@href').get()
                link_text = li.xpath('./a[@data-ref="link"]/text()').get().strip() if href else None

                if href and link_text:
                    self.logger.info(f"[UPPER LEVEL] {upper_level_text}")
                    self.logger.info(f"[LOWER LEVEL] {href} - {link_text}")
                    category_name = f"{upper_level_text} > {link_text}"
                    yield response.follow(href, self.parse_details, meta={'category': category_name})

    def parse_details(self, response):
        self.current_category = response.meta.get('category', None)
        self.item_count = 0 
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(response.url)

        last_height = driver.execute_script("return document.body.scrollHeight")

        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(5)  # ждать 5 секунд

            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        product_divs = response.xpath('//div[@class="c-product__inner"]')
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
            category = response.meta.get('category', None)
            product = {
                        "url": product_link,
                        "categories": category,
                        "article": None,
                        "name": product_name.strip(),
                        "color": None,
                        "images": [],
                        "price": None,
                        "old_price": None,
                        "currency": None,
                        "description": None,
                        "composition": None,
                        "sizes": {}
                    }
            self.item_count += 1 
            yield product
        else:
            self.logger.info("Product Name not found")