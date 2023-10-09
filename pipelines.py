# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


# class YslParserPipeline:
#     def process_item(self, item, spider):
#         return item

class JsonWriterPipeline:

    def __init__(self):
        self.data = []

    def process_item(self, item, spider):
        self.data.append(item)
        return item

    def close_spider(self, spider):
        with open(f"WOMAN-WEAR-{datetime.datetime.now().strftime('%Y-%m')}.json", 'w') as f:
            json.dump(self.data, f, indent=4)
