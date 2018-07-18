# -*- coding: utf-8 -*-

import scrapy

class VrsSpider(scrapy.Spider):
    name = 'vrs-spider'
    start_urls = ['https://virtualracingschool.appspot.com/#/DataPacks']

    def parse(self, response):

        print(response.body)

        for title in response.css('h2.entry-title'):
            yield {'title': title.css('a ::text').extract_first()}

        for next_page in response.css('div.prev-post > a'):
            yield response.follow(next_page, self.parse)