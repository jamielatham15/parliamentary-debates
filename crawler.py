import re
import json

import scrapy
from scrapy import Request
from scrapy.crawler import CrawlerProcess, CrawlerRunner

from config import config
from dbmodels import Session, ParliamentarySession, Speech

from contextlib import contextmanager


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


class HansardSpider(scrapy.Spider):
    name = "hansard"

    start_urls = [
        "https://api.parliament.uk/historic-hansard/sittings/1806/mar/"
        # 'https://api.parliament.uk/historic-hansard/sittings/1800s',
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


class SpeechCrawler:
    def save_articles(self):
        process = CrawlerProcess()
        process.crawl(HansardSpider)
        process.start()


if __name__ == "__main__":
    speech_crawler = SpeechCrawler()
    speech_crawler.save_articles()
