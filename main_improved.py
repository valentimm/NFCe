"""
NFCe READER - VERSÃO FULL SCREEN (SEM ZOOM)
Funcionalidades:
- Leitura em Tela Cheia (Detecta em qualquer lugar)
- Filtros de realce (Nitidez/Contraste) automáticos
- Integração com Scrapy
"""

import cv2
import numpy as np
import subprocess
import csv
import os
import time
import threading
import re
from dataclasses import dataclass
from typing import Tuple, Dict, Any, Optional
from qreader import QReader

# ================= CONFIGURAÇÕES =================

@dataclass
class Config:
    camera_index: int = 1  # 0 = Webcam Integrada, 1 = USB/Externa
    csv_file: str = "nfc_data.csv"
    scrapy_folder: str = "nfceReader/"
    
    # Delay para evitar leituras duplicadas (em segundos)
    reset_delay: int = 4
    
    # Processamento de Imagem (Apenas realce, sem upscale)
    sharpen_strength: float = 1.0
    
    # Resolução da Câmera
    cam_width: int = 1920
    cam_height: int = 1080

@dataclass
class AppState:
    status: str = "Aguardando QR Code..."
    color: Tuple[int, int, int] = (0, 255, 0) # Verde inicial
    is_processing: bool = False
    last_url: str = ""
    last_time: float = 0.0

# Cores (BGR)
COLORS = {
    'GREEN': (0, 255, 0),
    'RED': (0, 0, 255),
    'BLUE': (255, 200, 0),
    'BLACK': (0, 0, 0),
    'WHITE': (255, 255, 255)
}

NFCE_PATTERN = re.compile(r'https?://.*(?:fazenda|sefaz|nfce|nfe|qrcode|decodificacao|portal).*', re.IGNORECASE)

class NFCeReader:
    def __init__(self):
        self.cfg = Config()
        self.state = AppState()
        # model_size='l' é mais preciso, mas se ficar lento, troque por 'n' ou 's'
        self.qreader = QReader(model_size='l') 
        
        self._init_csv()
        self._init_camera()

    def _init_csv(self):
        if not os.path.exists(self.cfg.csv_file):
            try:
                with open(self.cfg.csv_file, mode="w", newline="", encoding="utf-8-sig") as f:
                    writer = csv.writer(f, delimiter=';')
                    writer.writerow(["Estabelecimento", "Produto", "Quantidade", "Unidade", "Valor_Total", "Desconto"])
            except IOError as e:
                print(f"[Erro] Falha ao criar CSV: {e}")

    def _init_camera(self):
        print(f"[Sistema] Iniciando Câmera {self.cfg.camera_index}...")
        self.cap = cv2.VideoCapture(self.cfg.camera_index)
        if not self.cap.isOpened():
            raise RuntimeError(f"Não foi possível abrir a câmera {self.cfg.camera_index}")
        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.cfg.cam_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.cfg.cam_height)
        
        w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"[Sistema] Resolução: {w}x{h}")

    def _run_scrapy_thread(self, url: str):
        self.state.is_processing = True
        self.state.status = "Baixando dados..."
        self.state.color = COLORS['BLUE']

        comando = f'scrapy crawl nfcedata -a url="{url}"'

        try:
            process = subprocess.Popen(
                comando,
                cwd=self.cfg.scrapy_folder,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            # Aguarda um pouco mais, pois a internet pode oscilar
            _, stderr = process.communicate(timeout=45)

            if process.returncode == 0:
                self.state.status = "NOTA SALVA!"
                self.state.color = COLORS['GREEN']
                print(f"[Sucesso] URL salva.")
            else:
                self.state.status = "Erro no Scrapy"
                self.state.color = COLORS['RED']
                print(f"[Erro Scrapy] {stderr[:100]}")

        except subprocess.TimeoutExpired:
            self.state.status = "Timeout (45s)"
            self.state.color = COLORS['RED']
        except Exception as e:
            self.state.status = f"Erro: {str(e)[:15]}"
            self.state.color = COLORS['RED']
        finally:
            time.sleep(2)
            self.state.is_processing = False
            self.state.status = "Aguardando QR Code..."
            self.state.color = COLORS['GREEN']

    def _enhance_frame(self, image: np.ndarray) -> np.ndarray:
        """Aplica apenas nitidez e contraste. Sem upscale pesado."""
        # 1. Sharpening leve
        kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]]) * self.cfg.sharpen_strength
        sharpened = cv2.filter2D(image, -1, kernel)
        
        # 2. Contraste (CLAHE) apenas no canal de luminosidade
        lab_image = cv2.cvtColor(sharpened, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab_image)
        
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l_channel_eq = clahe.apply(l_channel)
        
        enhanced = cv2.merge([l_channel_eq, a_channel, b_channel])
        return cv2.cvtColor(enhanced, cv2.COLOR_LAB2RGB) # Retorna RGB para o QReader

    def _process_frame(self, frame: np.ndarray):
        """Processa o frame inteiro."""
        if self.state.is_processing:
            return

        # Prepara imagem (filtro + converte RGB)
        rgb_frame = self._enhance_frame(frame)

        try:
            # Detecta no frame inteiro
            detections = self.qreader.detect(image=rgb_frame)
            
            for detection in detections:
                bbox = detection.get('bbox_xyxy')
                if bbox is None: 
                    continue

                x1, y1, x2, y2 = map(int, bbox)
                
                # Desenha o quadrado
                cv2.rectangle(frame, (x1, y1), (x2, y2), self.state.color, 3)
                
                # Tenta decodificar este QR específico
                self._decode_and_act(rgb_frame, detection)
                
        except Exception as e:
            print(f"[Aviso] Erro loop: {e}")

    def _decode_and_act(self, image: np.ndarray, detection: Dict[str, Any]):
        try:
            decoded = self.qreader.decode(image=image, candidates=[detection])
            if decoded and decoded[0]:
                url = decoded[0]
                self._handle_url(url)
        except Exception:
            pass

    def _handle_url(self, url: str):
        current_time = time.time()
        is_new = url != self.state.last_url
        is_time = (current_time - self.state.last_time > self.cfg.reset_delay)
        
        if is_time or is_new:
            if NFCE_PATTERN.match(url):
                print(f"[QR Detectado] {url}")
                self.state.last_url = url
                self.state.last_time = current_time
                
                t = threading.Thread(target=self._run_scrapy_thread, args=(url,))
                t.daemon = True
                t.start()
            else:
                self.state.status = "QR Code Inválido"
                self.state.color = COLORS['RED']

    def _draw_hud(self, frame: np.ndarray):
        h, w = frame.shape[:2]
        
        # Barra de fundo
        cv2.rectangle(frame, (0, 0), (w, 50), COLORS['BLACK'], -1)
        
        # Texto Status
        cv2.putText(frame, self.state.status, (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 
                   1.0, self.state.color, 2)
        
        if self.state.is_processing:
            cv2.putText(frame, "PROCESSANDO...", (w - 250, 35), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, COLORS['BLUE'], 2)

    def run(self):
        print("[Sistema] Leitura Full-Screen iniciada. 'Q' para sair.")
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("[Erro] Falha na câmera")
                break

            if (cv2.waitKey(1) & 0xFF) == ord('q'):
                break

            self._process_frame(frame)
            self._draw_hud(frame)
            
            cv2.imshow("NFCe Reader", frame)

        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    try:
        reader = NFCeReader()
        reader.run()
    except Exception as e:
        print(f"[Fatal] {e}")