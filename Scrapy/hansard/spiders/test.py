import scrapy
from dateutil.parser import parse

class HansardSpider(scrapy.Spider):
    name = "test"
    
    def start_requests(self):
        urls = [
            'https://api.parliament.uk/historic-hansard/sittings/1800s',
            'https://api.parliament.uk/historic-hansard/sittings/1810s',
            'https://api.parliament.uk/historic-hansard/sittings/1820s',
            'https://api.parliament.uk/historic-hansard/sittings/1830s',
            'https://api.parliament.uk/historic-hansard/sittings/1840s',            
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        year_pages = list()
        for i in range(0,20,1):
            page = response.xpath('/html/body/div[2]/div[1]/table/tbody/tr[3]/td[' + str(i) + ']/a/text()').get()
            if not page:
                continue
            else:
                year_pages.append("https://api.parliament.uk/historic-hansard/sittings/" + page)
        print(year_pages)
            


        # page = response.url.split("/")[-2]
        # filename = 'quotes-%s.html' % page
        # with open(filename, 'wb') as f:
        #     f.write(response.body)

    
        # For the records we want to extract
        # page_date = parse(' '.join(response.url.split("/")[-4:-1]))
        # page_date = page_date.strftime(format='%Y%m%d')
        # page_title = response.url.split("/")[-1]