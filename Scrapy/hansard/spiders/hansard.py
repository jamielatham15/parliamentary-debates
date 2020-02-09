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
        body = json.loads(response.body)
        page_date = parse(' '.join(re.split('/|[.]', response.url)[-4:-1]))
        page_date = page_date.strftime(format='%Y')
        filename = 'data/session-%s.json' % page_date
        with open(filename, 'a', encoding='utf-8') as f:
            json.dump(body[0], f)
            f.write('\n')