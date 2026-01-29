"""
NFCe SUPER READER - VERSÃO ZOOM DINÂMICO
Funcionalidades:
- Zoom Ajustável em Tempo Real (Teclas W e S)
- Super-Resolução (Upscale 2x na área de foco)
- Mira de Alta Visibilidade
- Leitura via IA (QReader Large)
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

# ================= CONFIGURAÇÕES =================
CAMERA_INDEX = 1        # 0 = Webcam Padrão, 1 = Externa
CSV_FILE = "nfc_data.csv"
SCRAPY_FOLDER = "nfceReader/" 

# Ajustes Iniciais
INITIAL_ZOOM = 300      # Tamanho inicial do quadrado (menor = mais zoom)
MIN_ZOOM = 100          # Tamanho mínimo (máximo zoom) - reduzido para QR pequenos
MAX_ZOOM = 900          # Tamanho máximo (mínimo zoom)
AIM_TOLERANCE_PCT = 0.35 # Tolerância da mira (35% do tamanho do zoom atual)
RESET_DELAY = 4

# Configurações de processamento de imagem
UPSCALE_FACTOR = 3.0    # Aumentado de 2.0 para 3.0 (melhor para QR pequenos)
SHARPEN_STRENGTH = 1.5  # Força do sharpening         

# Regex NFCe
NFCE_PATTERN = re.compile(r'https?://.*(?:fazenda|sefaz|nfce|nfe|qrcode|decodificacao|portal).*', re.IGNORECASE)

# Cores
VALOR_VERDE = (0, 255, 0)
VALOR_VERMELHO = (0, 0, 255)
VALOR_AMARELO = (0, 255, 255)
VALOR_AZUL = (255, 200, 0)
VALOR_CINZA = (128, 128, 128)
VALOR_PRETO = (0, 0, 0)
VALOR_BRANCO = (255, 255, 255)

# ================= ESTADO GLOBAL =================
app_state = {
    "status": "Ajuste o Zoom (W / S)",
    "color": VALOR_BRANCO,
    "is_processing": False,
    "last_url": "",
    "last_time": 0,
    "current_zoom": INITIAL_ZOOM
}

# ================= FUNÇÕES AUXILIARES =================

def init_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(["Estabelecimento", "Produto", "Quantidade", "Unidade", "Valor_Total", "Desconto"])

def run_scrapy_thread(url):
    app_state["is_processing"] = True
    app_state["status"] = "Baixando dados..."
    app_state["color"] = VALOR_AZUL
    
    comando = f'scrapy crawl nfcedata -a url="{url}"'
    
    try:
        process = subprocess.Popen(
            comando, 
            cwd=SCRAPY_FOLDER, 
            shell=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True
        )
        stdout, stderr = process.communicate(timeout=45)
        
        if process.returncode == 0:
            app_state["status"] = "SUCESSO! Nota Salva."
            app_state["color"] = VALOR_VERDE
            print(f"[Sucesso] NFCe processada: {url[:50]}...")
        else:
            app_state["status"] = "Erro no Scrapy"
            app_state["color"] = VALOR_VERMELHO
            print(f"[Erro] Scrapy falhou: {stderr[:100]}")

    except subprocess.TimeoutExpired:
        app_state["status"] = "Timeout (45s)"
        app_state["color"] = VALOR_VERMELHO
        print("[Erro] Timeout ao processar NFCe")
    except Exception as e:
        app_state["status"] = f"Erro: {str(e)[:15]}"
        app_state["color"] = VALOR_VERMELHO
        print(f"[Erro] Exceção: {e}")
        
    finally:
        time.sleep(2)
        app_state["is_processing"] = False
        app_state["status"] = "Ajuste o Zoom (W / S)"
        app_state["color"] = VALOR_BRANCO

def is_centered(bbox, crop_size):
    """Verifica se o QR está no centro (proporcional ao zoom atual)"""
    if bbox is None: return False
    x1, y1, x2, y2 = bbox
    qr_cx, qr_cy = x1 + (x2 - x1) / 2, y1 + (y2 - y1) / 2
    center = crop_size / 2
    
    # A tolerância muda conforme o zoom (mais zoom = precisa ser mais preciso)
    tolerance = crop_size * AIM_TOLERANCE_PCT
    dist = np.sqrt((qr_cx - center)**2 + (qr_cy - center)**2)
    return dist < tolerance

def preprocess_for_small_qr(image):
    """Aplica processamento avançado para melhorar detecção de QR codes pequenos"""
    # 1. Sharpening (realçar bordas)
    kernel_sharpen = np.array([
        [-1, -1, -1],
        [-1,  9, -1],
        [-1, -1, -1]
    ]) * SHARPEN_STRENGTH
    sharpened = cv2.filter2D(image, -1, kernel_sharpen)
    
    # 2. Ajuste de contraste adaptativo (CLAHE)
    lab = cv2.cvtColor(sharpened, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    enhanced = cv2.merge([l, a, b])
    enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
    
    # 3. Denoising leve (reduz ruído sem borrar)
    denoised = cv2.fastNlMeansDenoisingColored(enhanced, None, 10, 10, 7, 21)
    
    return denoised

def draw_hud(frame, crop_coords):
    h, w = frame.shape[:2]
    cx_frame, cy_frame = w // 2, h // 2
    x1, y1, x2, y2 = crop_coords
    
    # 1. Desenha a área do Zoom Dinâmico
    cv2.rectangle(frame, (x1, y1), (x2, y2), VALOR_PRETO, 4) 
    cv2.rectangle(frame, (x1, y1), (x2, y2), VALOR_AZUL, 2)
    
    # Texto de Instrução
    info_zoom = f"ZOOM: {app_state['current_zoom']}px (W/S) | Upscale: {UPSCALE_FACTOR}x"
    cv2.putText(frame, info_zoom, (x1, y2 + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, VALOR_AZUL, 2)

    # 2. MIRA (CROSSHAIR)
    # A mira se adapta visualmente ao tamanho da caixa
    gap = int(app_state['current_zoom'] * 0.15) 
    tolerance_px = int(app_state['current_zoom'] * AIM_TOLERANCE_PCT)
    
    # Círculo de Tolerância
    cv2.circle(frame, (cx_frame, cy_frame), tolerance_px, VALOR_PRETO, 3)
    cv2.circle(frame, (cx_frame, cy_frame), tolerance_px, VALOR_BRANCO, 1)

    # Cruz
    cv2.line(frame, (cx_frame - gap, cy_frame), (cx_frame + gap, cy_frame), VALOR_AMARELO, 2)
    cv2.line(frame, (cx_frame, cy_frame - gap), (cx_frame, cy_frame + gap), VALOR_AMARELO, 2)

    # 3. Painel de Status
    cv2.rectangle(frame, (0, 0), (w, 60), VALOR_PRETO, -1)
    cv2.putText(frame, app_state["status"], (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, app_state["color"], 2)
    
    if app_state["is_processing"]:
        cv2.putText(frame, "PROCESSANDO...", (w - 250, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, VALOR_AMARELO, 2)

# ================= MAIN =================

def main():
    print("\n[Sistema] Carregando IA...")
    qreader = QReader(model_size='l') 
    init_csv()
    
    cap = cv2.VideoCapture(CAMERA_INDEX)
    
    if not cap.isOpened():
        print(f"[Erro] Não foi possível abrir a câmera {CAMERA_INDEX}")
        return
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    
    real_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    real_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"[Sistema] Camera: {real_w}x{real_h}")
    print(f"[Config] Upscale: {UPSCALE_FACTOR}x | Sharpening: {SHARPEN_STRENGTH}")
    print(f"[Config] Zoom inicial: {INITIAL_ZOOM}px | Min: {MIN_ZOOM}px | Max: {MAX_ZOOM}px")
    print("[DICA] Use 'S' para diminuir a caixa (mais zoom) e 'W' para aumentar.")
    print("[DICA] Use 'Q' para sair")
    print("[INFO] Para QR codes muito pequenos, use zoom mínimo (100px) e aproxime a câmera")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[Erro] Falha ao capturar frame da câmera")
            break
        
        # --- 1. CONTROLE DE ZOOM (Teclado) ---
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'): break
        
        # 'w' aumenta o quadrado (Menos zoom)
        if key == ord('w') or key == ord('W'):
            app_state['current_zoom'] = min(app_state['current_zoom'] + 20, MAX_ZOOM)
        
        # 's' diminui o quadrado (Mais zoom no QR code)
        elif key == ord('s') or key == ord('S'):
            app_state['current_zoom'] = max(app_state['current_zoom'] - 20, MIN_ZOOM)

        # --- 2. PREPARAR IMAGEM (Crop + Pré-processamento + Super-Resolução) ---
        zoom_sz = app_state['current_zoom']
        cy, cx = real_h // 2, real_w // 2
        
        crop_x1 = max(0, cx - zoom_sz // 2)
        crop_y1 = max(0, cy - zoom_sz // 2)
        crop_x2 = min(real_w, cx + zoom_sz // 2)
        crop_y2 = min(real_h, cy + zoom_sz // 2)
        
        cropped_frame = frame[crop_y1:crop_y2, crop_x1:crop_x2]
        
        # Aplicar pré-processamento para QR codes pequenos
        processed_frame = preprocess_for_small_qr(cropped_frame)
        
        # SUPER-RESOLUÇÃO: Ampliar 3x para melhorar pixels pequenos
        enhanced_frame = cv2.resize(
            processed_frame, 
            None, 
            fx=UPSCALE_FACTOR, 
            fy=UPSCALE_FACTOR, 
            interpolation=cv2.INTER_CUBIC
        )
        rgb_enhanced = cv2.cvtColor(enhanced_frame, cv2.COLOR_BGR2RGB)
        
        # --- 3. DETECÇÃO ---
        target_detection = None
        
        if not app_state["is_processing"]:
            try:
                # Detecta na imagem ampliada
                detections = qreader.detect(image=rgb_enhanced)
                
                for detection in detections:
                    bbox = detection.get('bbox_xyxy')
                    if bbox is None: continue
                    
                    # Ajustar coordenadas de volta ao tamanho original do crop
                    bx1, by1, bx2, by2 = map(lambda v: int(v / UPSCALE_FACTOR), bbox)
                    
                    # Calcular posição real na tela cheia para desenhar
                    orig_x1, orig_y1 = bx1 + crop_x1, by1 + crop_y1
                    orig_x2, orig_y2 = bx2 + crop_x1, by2 + crop_y1
                    
                    # Verifica se está na mira (baseado no tamanho do zoom atual)
                    if is_centered((bx1, by1, bx2, by2), zoom_sz):
                        target_detection = detection # Passamos a detecção original (ampliada)
                        cv2.rectangle(frame, (orig_x1, orig_y1), (orig_x2, orig_y2), VALOR_AMARELO, 3)
                    else:
                        cv2.rectangle(frame, (orig_x1, orig_y1), (orig_x2, orig_y2), VALOR_CINZA, 1)
                        
            except Exception as e:
                print(f"[Aviso] Erro na detecção: {e}")

        # --- 4. DECODIFICAÇÃO ---
        if target_detection:
            try:
                # Decodifica usando a imagem ampliada (Super Resolução)
                decoded = qreader.decode(image=rgb_enhanced, candidates=[target_detection])
                
                if decoded and decoded[0]:
                    url = decoded[0]
                    current_time = time.time()
                    
                    if (current_time - app_state["last_time"] > RESET_DELAY) or (url != app_state["last_url"]):
                        if NFCE_PATTERN.match(url):
                            app_state["last_url"] = url
                            app_state["last_time"] = current_time
                            t = threading.Thread(target=run_scrapy_thread, args=(url,))
                            t.daemon = True
                            t.start()
                        else:
                            app_state["status"] = "QR Code invalido"
                            app_state["color"] = VALOR_VERMELHO
            except Exception as e:
                print(f"[Aviso] Erro na decodificação: {e}")

        draw_hud(frame, (crop_x1, crop_y1, crop_x2, crop_y2))
        cv2.imshow("NFCe Super Zoom", frame)

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()