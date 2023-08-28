import scrapy


class NfcedataSpider(scrapy.Spider):
    name = "nfcedata"
    allowed_domains = ["www.fazenda.pr.gov.br"]
    start_urls = ["https://www.fazenda.pr.gov.br"]

    def parse(self, response):
        pass
