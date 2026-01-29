"""
Script OTIMIZADO para leitura de NFCe via webcam
Melhorias: Leitura via QReader (IA) + Processamento Async (Threading)
"""

import cv2
from qreader import QReader # Nova biblioteca
import subprocess
import csv
import os
import time
from datetime import datetime
import sys
import threading # Para não travar a webcam
import numpy as np

# Configurações
CAMERA_INDEX = 1  # Tente 0 se o 1 não abrir
RESET_DELAY = 3   # Diminuí o delay pois a leitura é mais rápida
CSV_FILE = "nfc_data.csv"

# Cores
COLOR_GREEN = (0, 255, 0)
COLOR_RED = (0, 0, 255)
COLOR_BLUE = (255, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_ORANGE = (0, 165, 255)

# Status global para feedback na tela sem travar
current_status = "Aguardando..."
status_color = COLOR_WHITE

def init_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(["Estabelecimento", "Produto", "Quantidade", "Unidade", "Valor_Total", "Desconto"])

def validate_nfce_url(url):
    if not url: return False
    # Algumas URLs de NFCe podem não ter 'fazenda' explicito dependendo do estado, 
    # mas 'http' é o mínimo. Ajuste conforme seu estado.
    return "http" in url.lower() and ("nfce" in url.lower() or "nfe" in url.lower())

def run_scrapy_thread(url):
    """Roda o Scrapy em uma thread separada para não travar a UI"""
    global current_status, status_color
    
    current_status = "Processando..."
    status_color = COLOR_ORANGE
    
    comando = f'scrapy crawl nfcedata -a url="{url}"'
    
    try:
        # Nota: shell=True pode ser inseguro em produção, mas ok para uso local
        result = subprocess.run(
            comando,
            cwd="nfceReader/", # Certifique-se que esta pasta existe
            shell=True,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            current_status = "Sucesso!"
            status_color = COLOR_GREEN
            print(f"[✓] Processado: {url[:30]}...")
        else:
            current_status = "Erro no Scrapy"
            status_color = COLOR_RED
            print(f"[✗] Erro Scrapy: {result.stderr}")
            
    except Exception as e:
        current_status = f"Erro: {str(e)[:15]}"
        status_color = COLOR_RED
        print(f"[✗] Exception: {e}")
    
    # Reseta o status após 3 segundos
    time.sleep(3)
    current_status = "Aguardando..."
    status_color = COLOR_WHITE

def draw_info_panel(frame, fps):
    global current_status, status_color
    
    # Fundo simples para o texto ficar legível
    cv2.rectangle(frame, (0, 0), (frame.shape[1], 80), (0, 0, 0), -1)
    
    # Status Principal
    cv2.putText(frame, f"STATUS: {current_status}", (20, 40), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)
    
    # Info secundária
    cv2.putText(frame, f"FPS: {int(fps)} | 'Q' Sair | 'S' Stats", (20, 70), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

def main():
    global current_status, status_color
    
    print("🚀 Iniciando QReader Engine...")
    
    # Inicializa o Detector (Modelo AI é baixado na primeira execução)
    qreader = QReader(model_size='s') 
    
    init_csv()
    
    cap = cv2.VideoCapture(CAMERA_INDEX)
    
    # Forçar resolução melhor (Webcams modernas suportam HD/FullHD)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    if not cap.isOpened():
        print(f"Erro na câmera {CAMERA_INDEX}. Tentando 0...")
        cap = cv2.VideoCapture(0)

    last_read_time = 0
    processing_queue = [] # Evitar processar o mesmo QR seguidamente
    
    prev_frame_time = 0
    new_frame_time = 0

    print("[✓] Câmera pronta.")

    while True:
        ret, frame = cap.read()
        if not ret: break

        # Cálculo de FPS
        new_frame_time = time.time()
        fps = 1/(new_frame_time-prev_frame_time)
        prev_frame_time = new_frame_time

        # --- DICA DE PERFORMANCE ---
        # O QReader é rápido, mas processar TODO frame pode pesar em PCs fracos.
        # Se ficar lento, processe apenas 1 a cada 3 frames.
        
        # Converte para RGB (QReader espera RGB, OpenCV usa BGR)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Detectar e Decodificar
        try:
            decoded_texts = qreader.detect_and_decode(image=rgb_frame)
        except Exception:
            decoded_texts = []

        # Se encontrou algo
        if decoded_texts and decoded_texts[0] is not None:
            for url in decoded_texts:
                if url:
                    # Desenha feedback visual (não temos as coordenadas exatas rect com QReader fácil, 
                    # então desenhamos uma borda na tela inteira ou apenas notificamos)
                    cv2.rectangle(frame, (0,0), (frame.shape[1], frame.shape[0]), COLOR_GREEN, 5)
                    
                    current_time = time.time()
                    
                    # Verifica delay e validade
                    if (current_time - last_read_time > RESET_DELAY) and validate_nfce_url(url):
                        print(f"\n[Detectado] {url}")
                        last_read_time = current_time
                        
                        # Inicia thread para não travar
                        t = threading.Thread(target=run_scrapy_thread, args=(url,))
                        t.daemon = True # Mata a thread se o programa fechar
                        t.start()
                    elif not validate_nfce_url(url):
                         current_status = "QR Code invalido (Nao e NFCe)"
                         status_color = COLOR_RED

        draw_info_panel(frame, fps)
        
        cv2.imshow("NFCe Super Reader", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'): break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()