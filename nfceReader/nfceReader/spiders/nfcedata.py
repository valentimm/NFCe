import scrapy

class NfcedataSpider(scrapy.Spider):
    name = "nfcedata"
    allowed_domains = ["www.fazenda.pr.gov.br"]

    # Configurações personalizadas
    custom_settings = {
        'FEEDS': {
            '../../../Items.csv': {'format': 'csv'},
        }
    }
    
    def start_requests(self):
        url = getattr(self, 'url', None)
        if url:
            yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        # Extrai os dados da página
        names = response.css("td span.txtTit2::text").getall()
        valores = response.css("td span.valor::text").getall()

        # Itera pelos dados e gera os itens
        for name, valor in zip(names, valores):
            yield {
                'name': name,
                'valor': valor,
            }
