"""
NFCe SUPER READER - VERSÃO FINAL (ALTA VISIBILIDADE)
Funcionalidades:
- Leitura via IA (QReader Large)
- Zoom Digital (Crop)
- Mira de Alta Visibilidade (Contraste Preto/Colorido)
- Validação de URL (Regex)
- Processamento em Background (Threading)
"""

import cv2
from qreader import QReader
import numpy as np
import subprocess
import csv
import os
import time
import threading
import re
import sys

# ================= CONFIGURAÇÕES =================
CAMERA_INDEX = 1        # 0 = Webcam Padrão, 1 = Externa/Iriun
CSV_FILE = "nfc_data.csv"
SCRAPY_FOLDER = "nfceReader/"  # Pasta onde está o seu projeto Scrapy

# Ajustes de Leitura
ZOOM_SIZE = 600         # Tamanho do recorte central (Zoom Digital)
AIM_TOLERANCE = 80      # Raio da mira em pixels (quanto menor, mais preciso tem que ser)
RESET_DELAY = 4         # Segundos para esperar antes de ler a mesma nota

# Regex para validar se é Nota Fiscal
NFCE_PATTERN = re.compile(r'https?://.*(?:fazenda|sefaz|nfce|nfe|qrcode|decodificacao|portal).*', re.IGNORECASE)

# Cores (BGR)
VALOR_VERDE = (0, 255, 0)
VALOR_VERMELHO = (0, 0, 255)
VALOR_AMARELO = (0, 255, 255)
VALOR_CINZA = (100, 100, 100)
VALOR_AZUL = (255, 200, 0)
VALOR_PRETO = (0, 0, 0)
VALOR_BRANCO = (255, 255, 255)

# ================= ESTADO GLOBAL =================
app_state = {
    "status": "Aguardando nota na mira...",
    "color": VALOR_BRANCO,
    "is_processing": False,
    "last_url": "",
    "last_time": 0
}

# ================= FUNÇÕES AUXILIARES =================

def init_csv():
    """Cria o CSV se não existir"""
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(["Estabelecimento", "Produto", "Quantidade", "Unidade", "Valor_Total", "Desconto"])
        print(f"[Sistema] Arquivo {CSV_FILE} criado.")

def run_scrapy_thread(url):
    """Executa o spider em segundo plano"""
    app_state["is_processing"] = True
    app_state["status"] = "Baixando dados..."
    app_state["color"] = VALOR_AZUL
    
    comando = f'scrapy crawl nfcedata -a url="{url}"'
    
    try:
        # Executa o Scrapy
        process = subprocess.Popen(
            comando,
            cwd=SCRAPY_FOLDER,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Aguarda conclusão (timeout de 45s)
        stdout, stderr = process.communicate(timeout=45)
        
        if process.returncode == 0:
            app_state["status"] = "SUCESSO! Nota Salva."
            app_state["color"] = VALOR_VERDE
            print(f"[Sucesso] URL Processada: {url}")
        else:
            app_state["status"] = "Erro no Scrapy"
            app_state["color"] = VALOR_VERMELHO
            print(f"[Erro] Falha no Scrapy. Stderr: {stderr[:100]}")

    except Exception as e:
        app_state["status"] = f"Erro Sistema: {str(e)[:15]}"
        app_state["color"] = VALOR_VERMELHO
        print(f"[Exception] {e}")
        
    finally:
        time.sleep(2) # Tempo para ler a mensagem de sucesso
        app_state["is_processing"] = False
        app_state["status"] = "Aguardando nota na mira..."
        app_state["color"] = VALOR_BRANCO

def is_centered(bbox, crop_w, crop_h):
    """Verifica se o QR Code está no centro da área de zoom"""
    if bbox is None: return False
    
    x1, y1, x2, y2 = bbox
    qr_cx = x1 + (x2 - x1) / 2
    qr_cy = y1 + (y2 - y1) / 2
    
    center_x, center_y = crop_w / 2, crop_h / 2
    
    # Distância Euclidiana
    dist = np.sqrt((qr_cx - center_x)**2 + (qr_cy - center_y)**2)
    return dist < AIM_TOLERANCE

def draw_hud(frame, crop_coords):
    """Desenha a interface gráfica (HUD) com Mira de Alta Visibilidade"""
    h, w = frame.shape[:2]
    cx_frame, cy_frame = w // 2, h // 2
    
    # 1. Desenha a área do Zoom (Retângulo Azul)
    x1, y1, x2, y2 = crop_coords
    # Borda preta grossa para contraste
    cv2.rectangle(frame, (x1, y1), (x2, y2), VALOR_PRETO, 4) 
    # Borda azul fina por cima
    cv2.rectangle(frame, (x1, y1), (x2, y2), VALOR_AZUL, 2)
    
    # Texto com fundo preto para leitura fácil
    cv2.putText(frame, "AREA DE ZOOM", (x1, y1 - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.6, VALOR_PRETO, 4)
    cv2.putText(frame, "AREA DE ZOOM", (x1, y1 - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.6, VALOR_AZUL, 2)

    # 2. MIRA (CROSSHAIR) - ALTA VISIBILIDADE
    # Aumentamos o tamanho (gap) e a espessura
    gap = 60 
    
    # --- Círculo de Tolerância ---
    # Fundo Preto (Espessura 4)
    cv2.circle(frame, (cx_frame, cy_frame), AIM_TOLERANCE, VALOR_PRETO, 4)
    # Frente Branca (Espessura 2)
    cv2.circle(frame, (cx_frame, cy_frame), AIM_TOLERANCE, VALOR_BRANCO, 2)

    # --- Cruz Central ---
    # Horizontal (Fundo Preto)
    cv2.line(frame, (cx_frame - gap, cy_frame), (cx_frame + gap, cy_frame), VALOR_PRETO, 6)
    # Horizontal (Frente Amarela)
    cv2.line(frame, (cx_frame - gap, cy_frame), (cx_frame + gap, cy_frame), VALOR_AMARELO, 2)
    
    # Vertical (Fundo Preto)
    cv2.line(frame, (cx_frame, cy_frame - gap), (cx_frame, cy_frame + gap), VALOR_PRETO, 6)
    # Vertical (Frente Amarela)
    cv2.line(frame, (cx_frame, cy_frame - gap), (cx_frame, cy_frame + gap), VALOR_AMARELO, 2)

    # 3. Painel de Status
    # Fundo do painel
    cv2.rectangle(frame, (0, 0), (w, 60), VALOR_PRETO, -1)
    
    # Texto Status
    cv2.putText(frame, app_state["status"], (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, app_state["color"], 2)
    
    if app_state["is_processing"]:
        cv2.putText(frame, "PROCESSANDO...", (w - 250, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, VALOR_AMARELO, 2)

# ================= MAIN =================

def main():
    print("\n[Sistema] Inicializando QReader Large (Pode demorar uns segundos)...")
    # Carrega o modelo Large (Mais lento, porém muito mais preciso)
    qreader = QReader(model_size='l') 
    
    init_csv()
    
    print(f"[Sistema] Abrindo câmera {CAMERA_INDEX} em Full HD...")
    cap = cv2.VideoCapture(CAMERA_INDEX)
    
    # Força Full HD
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    
    # Verifica resolução real obtida
    real_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    real_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"[Sistema] Resolução ativa: {real_w}x{real_h}")

    if not cap.isOpened():
        print("[Erro] Não foi possível abrir a câmera.")
        return

    while True:
        ret, frame = cap.read()
        if not ret: break
        
        # --- LÓGICA DE ZOOM DIGITAL (CROP) ---
        # Cortamos o centro da imagem para a IA analisar apenas aquilo
        cy, cx = real_h // 2, real_w // 2
        crop_x1 = max(0, cx - ZOOM_SIZE // 2)
        crop_y1 = max(0, cy - ZOOM_SIZE // 2)
        crop_x2 = min(real_w, cx + ZOOM_SIZE // 2)
        crop_y2 = min(real_h, cy + ZOOM_SIZE // 2)
        
        cropped_frame = frame[crop_y1:crop_y2, crop_x1:crop_x2]
        rgb_crop = cv2.cvtColor(cropped_frame, cv2.COLOR_BGR2RGB)
        
        # --- 1. DETECÇÃO (Apenas localizar, não decodificar ainda) ---
        # Só rodamos a IA se não estivermos processando algo
        target_detection = None
        
        if not app_state["is_processing"]:
            try:
                # Detecta QR codes dentro do CROP
                detections = qreader.detect(image=rgb_crop)
                
                for detection in detections:
                    bbox = detection.get('bbox_xyxy')
                    if bbox is None: continue
                    
                    bx1, by1, bx2, by2 = map(int, bbox)
                    
                    # Converte coordenadas do Crop para o Frame Original (para desenho)
                    orig_x1, orig_y1 = bx1 + crop_x1, by1 + crop_y1
                    orig_x2, orig_y2 = bx2 + crop_x1, by2 + crop_y1
                    
                    # Verifica se está na mira
                    if is_centered((bx1, by1, bx2, by2), ZOOM_SIZE, ZOOM_SIZE):
                        # NA MIRA!
                        target_detection = detection
                        cv2.rectangle(frame, (orig_x1, orig_y1), (orig_x2, orig_y2), VALOR_AMARELO, 3)
                    else:
                        # FORA DA MIRA (Cinza)
                        cv2.rectangle(frame, (orig_x1, orig_y1), (orig_x2, orig_y2), VALOR_CINZA, 1)
                        
            except Exception as e:
                print(f"Erro detect: {e}")

        # --- 2. DECODIFICAÇÃO E VALIDAÇÃO ---
        if target_detection:
            try:
                # Decodifica APENAS o QR code que estava na mira
                decoded = qreader.decode(image=rgb_crop, candidates=[target_detection])
                
                if decoded and decoded[0]:
                    url = decoded[0]
                    current_time = time.time()
                    
                    # Verifica Delay
                    if (current_time - app_state["last_time"] > RESET_DELAY) or (url != app_state["last_url"]):
                        
                        # Verifica Regex (Segurança contra QR code errado)
                        if NFCE_PATTERN.match(url):
                            app_state["last_url"] = url
                            app_state["last_time"] = current_time
                            
                            # Dispara Thread
                            t = threading.Thread(target=run_scrapy_thread, args=(url,))
                            t.daemon = True
                            t.start()
                        else:
                            app_state["status"] = "QR Code invalido (Nao e NFCe)"
                            app_state["color"] = VALOR_VERMELHO
                            
            except Exception as e:
                print(f"Erro decode: {e}")

        # Desenha HUD
        draw_hud(frame, (crop_x1, crop_y1, crop_x2, crop_y2))
        
        cv2.imshow("NFCe Scanner Pro", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()