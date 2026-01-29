"""
Script SUPER OTIMIZADO para NFCes PEQUENAS
Melhorias: Modelo AI 'Large' + Resolução 1080p + Zoom Digital Central (Crop)
"""

import cv2
from qreader import QReader
import subprocess
import csv
import os
import time
import threading
import numpy as np

# --- Configurações ---
CAMERA_INDEX = 1       # Tente 0 ou 1
RESET_DELAY = 3        # Delay para não ler a mesma nota repetidamente
CSV_FILE = "nfc_data.csv"
# Tamanho da área de "zoom" no centro da tela (em pixels)
CROP_SIZE = 600        

# --- Cores ---
COLOR_GREEN = (0, 255, 0)
COLOR_RED = (0, 0, 255)
COLOR_BLUE = (255, 255, 0) # Ciano para a área de zoom
COLOR_WHITE = (255, 255, 255)
COLOR_ORANGE = (0, 165, 255)

# --- Variáveis Globais de Estado ---
current_status = "Aguardando QR Code na area azul..."
status_color = COLOR_WHITE
is_processing = False # Trava para não tentar processar dois ao mesmo tempo

# ================= FUNÇÕES AUXILIARES =================

def init_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(["Estabelecimento", "Produto", "Quantidade", "Unidade", "Valor_Total", "Desconto"])

def validate_nfce_url(url):
    if not url or len(url) < 20: return False
    url_lower = url.lower()
    # Validação básica de URL de nota fiscal
    return "http" in url_lower and ("nfce" in url_lower or "nfe" in url_lower or "fazenda" in url_lower)

def run_scrapy_thread(url):
    """Roda o Scrapy sem travar a câmera"""
    global current_status, status_color, is_processing
    
    is_processing = True
    current_status = "Processando NFCe..."
    status_color = COLOR_ORANGE
    
    # Substitua 'python' pelo caminho do seu venv se necessário, ex: 'venv/Scripts/python'
    comando = f'scrapy crawl nfcedata -a url="{url}"'
    
    try:
        print(f"[->] Iniciando Scrapy para: {url[:40]}...")
        # Usando subprocess.Popen para melhor controle em Windows
        process = subprocess.Popen(
            comando,
            cwd="nfceReader/",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True # Importante para ler como texto e não bytes
        )
        
        stdout, stderr = process.communicate(timeout=45) # Timeout maior
        
        if process.returncode == 0 and "ERROR" not in stdout:
            current_status = "Sucesso! Nota salva."
            status_color = COLOR_GREEN
            print(f"[✓] Scrapy finalizado com sucesso.")
        else:
            current_status = "Erro na extracao (Scrapy)"
            status_color = COLOR_RED
            print(f"[X] Erro Scrapy. Exit code: {process.returncode}")
            if stderr: print(f"Stderr: {stderr[:200]}...")

    except subprocess.TimeoutExpired:
        process.kill()
        current_status = "Erro: Timeout (>45s)"
        status_color = COLOR_RED
        print("[X] Timeout no Scrapy")
    except Exception as e:
        current_status = f"Erro sistema: {str(e)[:20]}"
        status_color = COLOR_RED
        print(f"[X] Exceção: {e}")
    finally:
        time.sleep(2)
        current_status = "Aguardando QR Code na area azul..."
        status_color = COLOR_WHITE
        is_processing = False

def draw_interface(frame, fps, crop_rect):
    """Desenha as informações e a área de zoom na tela"""
    h, w, _ = frame.shape
    
    # 1. Desenha o retângulo da área de zoom (onde o usuário deve mirar)
    cv2.rectangle(frame, (crop_rect[0], crop_rect[1]), (crop_rect[2], crop_rect[3]), COLOR_BLUE, 2)
    cv2.putText(frame, "AREA DE LEITURA (ZOOM)", (crop_rect[0], crop_rect[1]-10), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, COLOR_BLUE, 2)

    # 2. Barra de Status Superior
    cv2.rectangle(frame, (0, 0), (w, 60), (0, 0, 0), -1)
    cv2.putText(frame, f"STATUS: {current_status}", (20, 35), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
    
    # 3. Info de FPS e Ajuda
    cv2.putText(frame, f"FPS: {int(fps)} | Resolucao: {w}x{h} | 'Q' para Sair", (20, h - 20), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, COLOR_WHITE, 2, cv2.LINE_AA)
    if is_processing:
         cv2.putText(frame, "PROCESSANDO... AGUARDE", (w - 300, h - 20), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, COLOR_ORANGE, 2, cv2.LINE_AA)

# ================= LOOP PRINCIPAL =================

def main():
    global current_status, status_color, is_processing
    
    # MUDANÇA 1: Usando o modelo 'l' (Large) para maior precisão em códigos difíceis
    print("🚀 Carregando modelo de IA 'Large' (pode demorar um pouco na 1ª vez)...")
    qreader = QReader(model_size='l') 
    print("[✓] Modelo carregado.")

    init_csv()
    
    cap = cv2.VideoCapture(CAMERA_INDEX)
    
    # MUDANÇA 2: Tentando forçar FULL HD (1080p)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    
    # Verifica a resolução real que a câmera conseguiu pegar
    real_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    real_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"[i] Resolução da câmera definida para: {real_w}x{real_h}")
    
    if real_w < 1280:
        print("[!] AVISO: Sua câmera não suporta alta resolução. Códigos pequenos serão difíceis.")

    if not cap.isOpened():
        print(f"Erro na câmera {CAMERA_INDEX}. Verifique a conexão.")
        return

    last_read_time = 0
    prev_frame_time = 0
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret: break
        
        frame_count += 1
        h, w, _ = frame.shape

        # Cálculo de FPS
        new_frame_time = time.time()
        fps = 1/(new_frame_time-prev_frame_time) if prev_frame_time > 0 else 0
        prev_frame_time = new_frame_time

        # MUDANÇA 3: CÁLCULO DO ZOOM DIGITAL (CROP)
        # Definir coordenadas para cortar o centro da imagem
        center_x, center_y = w // 2, h // 2
        x1 = max(0, center_x - CROP_SIZE // 2)
        y1 = max(0, center_y - CROP_SIZE // 2)
        x2 = min(w, center_x + CROP_SIZE // 2)
        y2 = min(h, center_y + CROP_SIZE // 2)
        crop_rect = (x1, y1, x2, y2)
        
        # Criar a imagem "zoomada" cortando o frame original
        cropped_frame = frame[y1:y2, x1:x2]
        
        decoded_text = None
        
        # Otimização: Não roda a IA em todo frame se estiver processando ou se o FPS estiver baixo
        # Roda a cada 2 frames para aliviar a CPU
        if not is_processing and frame_count % 2 == 0:
            # Converter o CROP para RGB para o QReader
            rgb_crop = cv2.cvtColor(cropped_frame, cv2.COLOR_BGR2RGB)
            try:
                # Passamos apenas a imagem cortada (zoom) para a IA
                decoded = qreader.detect_and_decode(image=rgb_crop)
                if decoded and decoded[0] is not None:
                    decoded_text = decoded[0]
            except Exception as e:
                print(f"Erro na detecção: {e}")

        # Lógica de detecção bem sucedida
        if decoded_text:
            current_time = time.time()
            if (current_time - last_read_time > RESET_DELAY):
                
                if validate_nfce_url(decoded_text):
                    # Feedback visual imediato
                    cv2.rectangle(frame, (x1, y1), (x2, y2), COLOR_GREEN, 3)
                    
                    print(f"\n[>>>] URL Detectada: {decoded_text}")
                    last_read_time = current_time
                    
                    # Inicia thread do Scrapy
                    t = threading.Thread(target=run_scrapy_thread, args=(decoded_text,))
                    t.daemon = True
                    t.start()
                else:
                     current_status = "QR Code lido, mas nao e NFCe valida."
                     status_color = COLOR_RED

        # Desenha a interface final no frame original
        draw_interface(frame, fps, crop_rect)
        
        # Opcional: Mostrar o que a IA está vendo (o zoom) em outra janela para debug
        # cv2.imshow("Visao da IA (Zoom)", cropped_frame)
        
        cv2.imshow("Leitor NFCe Otimizado", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27: # 'q' ou ESC
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()