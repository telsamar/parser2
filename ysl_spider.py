import scrapy
import datetime
import json

class YslSpider(scrapy.Spider):
    name = 'ysl'
    start_urls = ['https://www.ysl.com/en-en']
    custom_settings = {
        'FEED_FORMAT': 'json',
        'FEED_URI': f"WOMAN-WEAR-{datetime.datetime.now().strftime('%Y-%m')}.json"
    }

    def parse(self, response):
        parent_li = response.xpath('//button[contains(text(), "SAINT LAURENT WOMEN")]/ancestor::li[@data-ref="item"][1]')
        li_elements = parent_li.xpath('.//div[@data-ref="subnav"]/ul/li')

        for li in li_elements:
            href = li.xpath('./a[@data-ref="link"]/@href').get()
            link_text = li.xpath('./a[@data-ref="link"]/text()').get().strip() if href else None
            
            if href and link_text:
                # if li.xpath('@data-level2').get():
                #     print(f"[UPPER LEVEL] {href} - {link_text}")
                # elif li.xpath('@data-level3').get():
                #     print(f"[LOWER LEVEL] {href} - {link_text}")

                product = {
                    "url": response.urljoin(href),
                    "categories": [link_text],  # Добавим больше категорий позже
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
