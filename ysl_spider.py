import scrapy

class YslSpider(scrapy.Spider):
    name = 'ysl'
    start_urls = ['https://www.ysl.com/en-en']

    def parse(self, response):
        # Найдем родительский элемент li, который содержит нужный button
        parent_li = response.xpath('//button[contains(text(), "SAINT LAURENT WOMEN")]/ancestor::li[@data-ref="item"][1]')
        
        # Извлекаем все дочерние li элементы
        li_elements = parent_li.xpath('.//div[@data-ref="subnav"]/ul/li')

        for li in li_elements:
            # Извлекаем href и текст ссылки для каждого li
            href = li.xpath('./a[@data-ref="link"]/@href').get()
            link_text = li.xpath('./a[@data-ref="link"]/text()').get().strip() if href else None
            
            if href and link_text:
                if li.xpath('@data-level2').get():
                    print(f"[UPPER LEVEL] {href} - {link_text}")
                elif li.xpath('@data-level3').get():
                    print(f"[LOWER LEVEL] {href} - {link_text}")
