# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

import redis

class IppoolPipeline(object):
    def process_item(self, item, spider):
        print(dict(item))
        return item
        
