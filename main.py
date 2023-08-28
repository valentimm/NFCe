import cv2
import subprocess


window_name = 'QR Code Detector'
delay = 1

# Video capture object
cap = cv2.VideoCapture(1)  # iphone camera
qcd = cv2.QRCodeDetector()

qr_code_read = False  # Variável para ler apenas uma vez

while True:
    ret, frame = cap.read()

    if ret and not qr_code_read:
        ret_qr, decoded_info, points, _ = qcd.detectAndDecodeMulti(frame)
        if ret_qr:
            for url, p in zip(decoded_info, points):
                if url:
                    # print(url)
                    color = (0, 255, 0)
                    qr_code_read = True
                    
                    subprocess.run(["scrapy", "crawl", "nfcedata", "-a", f"url={url}"], cwd="nfceReader/nfceReader/spiders/")
                else:
                    color = (0, 0, 255)
                frame = cv2.polylines(frame, [p.astype(int)], True, color, 8)
        cv2.imshow(window_name, frame)

    key = cv2.waitKey(delay) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('r'):
        qr_code_read = False  # Reiniciar a leitura

cap.release()
cv2.destroyAllWindows()
