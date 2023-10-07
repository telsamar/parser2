import scrapy

class YslSpider(scrapy.Spider):
    name = 'ysl'
    start_urls = ['https://www.ysl.com/en-en']

    def parse(self, response):
        text_element = response.xpath('//button[contains(text(), "SAINT LAURENT WOMEN")]').get()
        if text_element:
            print("Элемент найден!")
        else:
            print("Элемент не найден")


