import cv2
from pyzbar import pyzbar
import subprocess
import csv
import os
import time

# Configurações
cap = cv2.VideoCapture(1) 
reset_delay = 5 
last_read_time = 0
csv_file = "nfc_data.csv"

def init_csv():
    # Cria o arquivo com cabeçalho se ele não existir
    if not os.path.exists(csv_file):
        with open(csv_file, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=';')
            # Nova coluna "Desconto" adicionada ao final
            writer.writerow(["Estabelecimento", "Produto", "Quantidade", "Unidade", "Valor_Total", "Desconto"])
        print("[*] Planilha inicializada com a coluna Desconto.")

init_csv()
print("Iniciando leitor... Pressione 'q' para sair.")

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    qrcodes = pyzbar.decode(frame)
    current_time = time.time()

    for qrcode in qrcodes:
        url = qrcode.data.decode('utf-8')
        
        if current_time - last_read_time > reset_delay:
            print(f"[+] Lendo Nota Fiscal...")
            last_read_time = current_time

            (x, y, w, h) = qrcode.rect
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 4)

            # Proteção da URL com aspas para o Windows não travar no caractere '|'
            comando = f'scrapy crawl nfcedata -a url="{url}"'
            
            subprocess.Popen(
                comando,
                cwd="nfceReader/",
                shell=True
            )

    cv2.imshow("Leitor NFCe", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()