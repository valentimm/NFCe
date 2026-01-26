import scrapy

class NfcedataSpider(scrapy.Spider):
    name = "nfcedata"
    allowed_domains = ["www.fazenda.pr.gov.br"]

    custom_settings = {
        "ROBOTSTXT_OBEY": False, #
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", #
        "FEEDS": {
            "../nfc_data.csv": {
                "format": "csv",
                "encoding": "utf-8-sig",
                "item_export_kwargs": {
                    "include_headers_line": False, 
                    "delimiter": ";",             
                },
                "overwrite": False,
            }
        },
        # Definição da ordem das colunas no CSV
        "FEED_EXPORT_FIELDS": ["local", "name", "quantidade", "unidade", "valor", "desconto"],
    }

    def start_requests(self):
        url = getattr(self, "url", None)
        if url:
            yield scrapy.Request(url, callback=self.parse, dont_filter=True)

    def parse(self, response):
        estabelecimento = response.css("div.txtTopo::text").get()
        if not estabelecimento:
            estabelecimento = response.css("#u20::text").get() 

        items = response.css("tr[id^='Item +']")
        
        for item in items:
            name = item.css("td span.txtTit2::text").get()
            qtd = item.css("td span.Rqtd::text").get()
            un = item.css("td span.RUN::text").get()
            valor = item.css("td span.valor::text").get()
            
            # Lógica de Desconto:
            # Captura o texto do desconto usando a classe .totalNumb
            raw_desconto = item.css("span.totalNumb::text").get()
            desconto_final = ""

            if raw_desconto:
                # Limpa o texto (remove 'Vlr. Desc.:', espaços e converte para número)
                clean_desc = raw_desconto.replace("Vlr. Desc.:", "").strip()
                if clean_desc and clean_desc != "0,00":
                    # Adiciona o sinal de negativo antes do valor
                    desconto_final = f"-{clean_desc}"

            yield {
                "local": estabelecimento.strip() if estabelecimento else "Nao identificado",
                "name": name.strip() if name else "",
                "quantidade": qtd.strip().replace("Qtde.:", "").strip() if qtd else "",
                "unidade": un.strip().replace("UN:", "").strip() if un else "",
                "valor": valor.strip() if valor else "",
                "desconto": desconto_final
            }