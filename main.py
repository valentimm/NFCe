import cv2
import subprocess
import csv
import time

window_name = "QR Code Detector"
delay = 1
reset_delay = 5  # Tempo em segundos para permitir a leitura de um novo QR code

# Video capture object
cap = cv2.VideoCapture(1)  # Ajuste para sua câmera
qcd = cv2.QRCodeDetector()

qr_code_read = False  # Variável para ler apenas uma vez
last_read_time = 0  # Timestamp da última leitura de QR code


def clean_csv(file_path):
    # Abrir o arquivo CSV para leitura
    with open(file_path, mode="r", newline="", encoding="utf-8") as infile:
        reader = csv.reader(infile)
        # Criar uma lista de linhas que não contenham 'name,valor'
        rows = [row for row in reader if "name,valor" not in ",".join(row)]

    # Abrir o arquivo CSV para escrita
    with open(file_path, mode="w", newline="", encoding="utf-8") as outfile:
        writer = csv.writer(outfile)
        writer.writerows(rows)


# Caminho do arquivo CSV
csv_file = "nfc_data.csv"

while True:
    ret, frame = cap.read()

    if ret:
        current_time = time.time()
        if not qr_code_read or (current_time - last_read_time > reset_delay):
            ret_qr, decoded_info, points, _ = qcd.detectAndDecodeMulti(frame)
            if ret_qr:
                for url, p in zip(decoded_info, points):
                    if url:
                        color = (0, 255, 0)
                        qr_code_read = True
                        last_read_time = current_time
                        cv2.putText(
                            frame,
                            "QR Code lido!",
                            (50, 50),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1,
                            (0, 255, 0),
                            2,
                            cv2.LINE_AA,
                        )
                        subprocess.run(
                            ["scrapy", "crawl", "nfcedata", "-a", f"url={url}"],
                            cwd="nfceReader/nfceReader/spiders/",
                        )
                    else:
                        color = (0, 0, 255)
                    frame = cv2.polylines(frame, [p.astype(int)], True, color, 8)
            cv2.imshow(window_name, frame)

    key = cv2.waitKey(delay) & 0xFF
    if key == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()

# Limpar o arquivo CSV após terminar a leitura dos QR codes
clean_csv(csv_file)
