import scrapy

class NfcedataSpider(scrapy.Spider):
    name = "nfcedata"
    allowed_domains = ["www.fazenda.pr.gov.br"]
    start_urls = ["http://www.fazenda.pr.gov.br/nfce/qrcode?p=41230801438784001098650080002284341220330512|2|1|1|f730aa13ef866b8f09342adbf4c545ea001e4dd5"]

    def parse(self, response):
        names = response.css("td span.txtTit2::text").getall()
        valores = response.css("td span.valor::text").getall()

        for name, valor in zip(names, valores):
            data = {
                'name': name,
                'valor': valor,
            }

            yield data
