import json
import re
from contextlib import contextmanager

import scrapy
#from newspaper import fulltext
from bs4 import BeautifulSoup
from bs4.element import Comment
from scrapy import Request
from scrapy.crawler import CrawlerProcess, CrawlerRunner

from config import config
from dbmodels import Session, ParliamentarySession, Speech


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()

class SessionSpider(scrapy.Spider):
    name = "parliamentary_sessions"
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:73.0) Gecko/20100101 Firefox/73.0',
    }

    start_urls = [
        'https://api.parliament.uk/historic-hansard/sittings/1800s',
        # 'https://api.parliament.uk/historic-hansard/sittings/1810s',
        # 'https://api.parliament.uk/historic-hansard/sittings/1820s',
        # 'https://api.parliament.uk/historic-hansard/sittings/1830s',
        # 'https://api.parliament.uk/historic-hansard/sittings/1840s'
    ]

    def parse(self, response):
        # follow links to year pages
        for page in response.xpath(
            "/html/body/div[2]/div[1]/table/tbody/tr[3]/td[*]/a/@href"
        ).getall():
            yield response.follow(page, self.parse)

        if len(response.xpath("//*[contains(@href, '.js')]/@href")) != 0:
            meta = response.xpath("//*[contains(@href, '.js')]/@href")
            yield response.follow(meta[0], self.parse_metadata)

    def parse_metadata(self, response):
        body = json.loads(response.body)
        for json_record in body:
            chamber = [key for key in json_record.keys()][0]
            if "commons" in chamber:
                response_url = response.url.replace("sittings", "commons")
            if "lords" in chamber:
                response_url = response.url.replace("sittings", "lords")
            for section in json_record[chamber]["top_level_sections"]:
                url = response_url.replace(".js", "/" + section["section"]["slug"])
                section["section"].update({"url": url})
            self.db_insert(json_record, chamber)

    def db_insert(self, json_record, chamber):
        with session_scope() as session:
            js = json_record.get(chamber)
            parliament_row = ParliamentarySession(
                hansard_sitting_id=js["id"],
                chamber=chamber,
                date=js["top_level_sections"][0]["section"]["date"],
                year=js["year"],
            )
            session.add(parliament_row)
            session.flush()
            session.refresh(parliament_row)

            for j in js["top_level_sections"]:
                speech_row = Speech(
                    hansard_speech_id=j["section"]["id"],
                    title=j["section"]["slug"],
                    speakers=None,
                    full_text=None,
                    url=j["section"]["url"],
                    parliamentary_session_id=parliament_row.id,
                )
                session.add(speech_row)

def next_url_gen():
    with session_scope() as session:
        urls = session.query(Speech.id, Speech.url).filter(Speech.full_text == None)
        url_list = [r for r in urls]
        for next_url in url_list:
            yield next_url

def tag_visible(element):
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True

def text_from_html(body):
    soup = BeautifulSoup(body, 'html.parser')
    for el in ['footer', 'header', 'section-navigation']:
        soup.find('div', id=el).decompose()
    texts = soup.findAll(text=True)
    visible_texts = filter(tag_visible, texts)  
    return u" ".join(t.strip() for t in visible_texts)

class SpeechSpider(scrapy.Spider):
    name = "parliamentary_speeches"
    url = next_url_gen()
    start_urls = []
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:73.0) Gecko/20100101 Firefox/73.0',
    }

    def start_requests(self):
        start_url = next(self.url)
        request = Request(start_url[1],
                         dont_filter=True, 
                         callback=self.parse, 
                         errback=self.error_handler, 
                         cb_kwargs={'PK': start_url[0]})
        yield request

    def parse(self, response, **cb_kwargs):
        text = text_from_html(response.body)
        with session_scope() as session:
            row = session.query(Speech).filter(
            Speech.id == cb_kwargs['PK']).first()
            row.full_text = text
            session.add(row)
        next_url = next(self.url)
        try:
            yield Request(next_url[1], 
                          dont_filter=True, 
                          callback=self.parse, 
                          errback=self.error_handler, 
                          cb_kwargs={'PK': next_url[0]})
        except StopIteration:
             self.crawler.engine.close_spider(self, reason='finished')

    def error_handler(self, failure):
        print(failure.value)
        next_url = next(self.url)
        yield Request(next_url[1], 
                      dont_filter=True, 
                      callback=self.parse, 
                      errback=self.error_handler, 
                      cb_kwargs={'PK': next_url[0]})
        



    

    # def save_record(self, response):
    #     page_date = parse(' '.join(re.split('/|[.]', response.url)[-4:-1]))
    #     page_date = page_date.strftime(format='%Y%m%d')
    #     page_title = re.split('/|[.]', response.url)[-1]
    #     filename = f'data/records/session-{page_date}-{page_title}.html'
    #     with open(filename, 'wb') as f:
    #         f.write(response.body)

    # def save_metadata(self, response, body):
    #     # body = json.loads(response.body)
    #     page_date = parse(' '.join(re.split('/|[.]', response.url)[-4:-1]))
    #     page_date = page_date.strftime(format='%Y%m%d')
    #     filename = f'data/metadata/session-{page_date}.json'
    #     breakpoint()
    #     with open(filename, 'a', encoding='utf-8') as f:
    #         for item in body:
    #             json.dump(item, f)
    #             f.write('\n')


class CrawlerRunner:
    def start(self, spider):
        process = CrawlerProcess()
        process.crawl(spider)
        process.start()


if __name__ == "__main__":
    # session_crawler = CrawlerRunner()
    # session_crawler.start(SessionSpider)
    speech_crawler = CrawlerRunner()
    speech_crawler.start(SpeechSpider)
