import scrapy
import datetime
import json
import os

class YslSpider(scrapy.Spider):
    name = 'ysl'
    start_urls = ['https://www.ysl.com/en-en']
    custom_settings = {
        'FEED_FORMAT': 'json',
        'FEED_URI': f"WOMAN-WEAR-{datetime.datetime.now().strftime('%Y-%m')}.json",
        'FEED_EXPORT_INDENT': 4
    }

    def parse(self, response):
        parent_li = response.xpath('//button[contains(text(), "SAINT LAURENT WOMEN")]/ancestor::li[@data-ref="item"][1]')
        
        for level2_elem in parent_li.xpath('.//li[@data-level2="true"]'):
            upper_level_href = level2_elem.xpath('./a[@data-ref="link"]/@href').get()
            upper_level_text = level2_elem.xpath('./a[@data-ref="link"]/text()|./button[@data-ref="link"]/text()').get().strip()

            if upper_level_href and upper_level_text:
                print(f"[UPPER LEVEL] {upper_level_href} - {upper_level_text}")

                product_upper = {
                    "url": response.urljoin(upper_level_href),
                    "categories": [upper_level_text],
                    "article": None,
                    "name": upper_level_text,
                    "color": None,
                    "images": [],
                    "price": None,
                    "old_price": None,
                    "currency": None,
                    "description": None,
                    "composition": None,
                    "sizes": {}
                }
                yield product_upper

            for li in level2_elem.xpath('.//ul[@data-ref="navlist"]/li'):
                href = li.xpath('./a[@data-ref="link"]/@href').get()
                link_text = li.xpath('./a[@data-ref="link"]/text()').get().strip() if href else None

                if href and link_text:
                    print(f"[UPPER LEVEL] {upper_level_text}")
                    print(f"[LOWER LEVEL] {href} - {link_text}")

                    product = {
                        "url": response.urljoin(href),
                        "categories": [upper_level_text, link_text],
                        "article": None,
                        "name": link_text,
                        "color": None,
                        "images": [],
                        "price": None,
                        "old_price": None,
                        "currency": None,
                        "description": None,
                        "composition": None,
                        "sizes": {}
                    }
                    yield product
