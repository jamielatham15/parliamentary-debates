import scrapy
from scrapy import Request
from dateutil.parser import parse
import re
import json

class HansardSpider(scrapy.Spider):
    name = "hansard"

    start_urls = [
        'https://api.parliament.uk/historic-hansard/sittings/1800s',
        'https://api.parliament.uk/historic-hansard/sittings/1810s',
        'https://api.parliament.uk/historic-hansard/sittings/1820s',
        'https://api.parliament.uk/historic-hansard/sittings/1830s',
        'https://api.parliament.uk/historic-hansard/sittings/1840s'
    ]

    def parse(self, response):
        # follow links to year pages
        for page in response.xpath("/html/body/div[2]/div[1]/table/tbody/tr[3]/td[*]/a/@href").getall():
            yield response.follow(page, self.parse)

        if len(response.xpath("//*[contains(@href, '.js')]/@href")) != 0:
            meta = response.xpath("//*[contains(@href, '.js')]/@href")
            yield response.follow(meta[0], self.parse_metadata)

    def parse_metadata(self, response):
        # the response contains two json objects, one commons, one lords
        body = json.loads(response.body)
        # yield response.follow(meta[0], self.save_metadata)
        self.save_metadata(response, body)
        #house_keys = [house_key for house_dict in body for house_key in house_dict]
        for item in body:
            if 'house_of_commons_sitting' in item.keys():
                record_url = response.url.replace('sittings', 'commons')
                for section in item['house_of_commons_sitting']['top_level_sections']:
                    record_url = record_url.replace('.js', '/' + section['section']['slug'])
                    yield response.follow(record_url, self.save_record)

            if 'house_of_lords_sitting' in item.keys():
                record_url = response.url.replace('sittings', 'lords')
                for section in item['house_of_lords_sitting']['top_level_sections']:
                    record_url = record_url.replace('.js', '/' + section['section']['slug'])
                    yield response.follow(record_url, self.save_record)

    def save_record(self, response):
        page_date = parse(' '.join(re.split('/|[.]', response.url)[-4:-1]))
        page_date = page_date.strftime(format='%Y%m%d')
        page_title = re.split('/|[.]', response.url)[-1]
        filename = f'data/records/session-{page_date}-{page_title}.html'
        with open(filename, 'wb') as f:
            f.write(response.body)


    def save_metadata(self, response, body):
        # body = json.loads(response.body)
        page_date = parse(' '.join(re.split('/|[.]', response.url)[-4:-1]))
        page_date = page_date.strftime(format='%Y%m%d')
        filename = f'data/metadata/session-{page_date}.json'
        with open(filename, 'a', encoding='utf-8') as f:
            for item in body:
                json.dump(item, f)
                f.write('\n')