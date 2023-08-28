import scrapy

class NfcedataSpider(scrapy.Spider):
    name = "nfcedata"
    allowed_domains = ["www.fazenda.pr.gov.br"]

    custom_settings = {
        'FEEDS': {
            'products.json': {'format': 'json'},
        }
    }
    
    def start_requests(self):
        url = getattr(self, 'url', None)
        if url:
            yield scrapy.Request(url, self.parse)

    def parse(self, response):
        names = response.css("td span.txtTit2::text").getall()
        valores = response.css("td span.valor::text").getall()

        for name, valor in zip(names, valores):
            data = {
                'name': name,
                'valor': valor,
            }

            yield data

