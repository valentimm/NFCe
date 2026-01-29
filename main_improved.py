"""
NFCe SUPER READER - VERSÃO REFATORADA (POO)
Funcionalidades:
- Zoom Ajustável em Tempo Real (Teclas W e S)
- Super-Resolução (Upscale) e Sharpening
- Mira de Alta Visibilidade
- Leitura assíncrona via Scrapy
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
from typing import Tuple, Dict, Any
from qreader import QReader

# ================= CONFIGURAÇÕES =================

@dataclass
class Config:
    camera_index: int = 1  # 0 = Webcam, 1 = Externa
    csv_file: str = "nfc_data.csv"
    scrapy_folder: str = "nfceReader/"
    
    # Zoom e Mira
    initial_zoom: int = 300
    min_zoom: int = 100
    max_zoom: int = 900
    aim_tolerance_pct: float = 0.35
    reset_delay: int = 4
    
    # Processamento de Imagem
    upscale_factor: float = 3.0
    sharpen_strength: float = 1.5
    
    # Resolução da Câmera
    cam_width: int = 1920
    cam_height: int = 1080

@dataclass
class AppState:
    status: str = "Ajuste o Zoom (W / S)"
    color: Tuple[int, int, int] = (255, 255, 255)  # Branco
    is_processing: bool = False
    last_url: str = ""
    last_time: float = 0.0
    current_zoom: int = 300

# Cores (BGR para OpenCV)
COLORS = {
    'GREEN': (0, 255, 0),
    'RED': (0, 0, 255),
    'YELLOW': (0, 255, 255),
    'BLUE': (255, 200, 0),
    'GRAY': (128, 128, 128),
    'BLACK': (0, 0, 0),
    'WHITE': (255, 255, 255)
}

NFCE_PATTERN = re.compile(r'https?://.*(?:fazenda|sefaz|nfce|nfe|qrcode|decodificacao|portal).*', re.IGNORECASE)


class NFCeSuperReader:
    def __init__(self):
        self.cfg = Config()
        self.state = AppState(current_zoom=self.cfg.initial_zoom)
        self.qreader = QReader(model_size='l')
        
        self._init_csv()
        self._init_camera()

    def _init_csv(self):
        """Inicializa o arquivo CSV se não existir."""
        if not os.path.exists(self.cfg.csv_file):
            try:
                with open(self.cfg.csv_file, mode="w", newline="", encoding="utf-8-sig") as f:
                    writer = csv.writer(f, delimiter=';')
                    writer.writerow(["Estabelecimento", "Produto", "Quantidade", "Unidade", "Valor_Total", "Desconto"])
            except IOError as e:
                print(f"[Erro] Falha ao criar CSV: {e}")

    def _init_camera(self):
        """Configura a captura de vídeo."""
        print(f"[Sistema] Iniciando Câmera {self.cfg.camera_index}...")
        self.cap = cv2.VideoCapture(self.cfg.camera_index)
        if not self.cap.isOpened():
            raise RuntimeError(f"Não foi possível abrir a câmera {self.cfg.camera_index}")
        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.cfg.cam_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.cfg.cam_height)
        
        # Atualiza dimensões reais caso a câmera não suporte o solicitado
        self.real_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.real_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"[Sistema] Resolução Ativa: {self.real_w}x{self.real_h}")

    def _run_scrapy_thread(self, url: str):
        """Executa o Scrapy em uma thread separada para não travar o vídeo."""
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
            _, stderr = process.communicate(timeout=45)

            if process.returncode == 0:
                self.state.status = "SUCESSO! Nota Salva."
                self.state.color = COLORS['GREEN']
                print(f"[Sucesso] Processado: {url[:40]}...")
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
            self.state.status = "Ajuste o Zoom (W / S)"
            self.state.color = COLORS['WHITE']

    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Aplica filtros para melhorar detecção em imagens de baixa qualidade/pequenas."""
        # 1. Sharpening
        kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]]) * self.cfg.sharpen_strength
        sharpened = cv2.filter2D(image, -1, kernel)
        
        # 2. Contraste Adaptativo (CLAHE)
        # Convertemos para o espaço de cor LAB para trabalhar apenas na Luminosidade
        lab_image = cv2.cvtColor(sharpened, cv2.COLOR_BGR2LAB)
        
        # Separa os canais: L (Lightness), A (Green-Red), B (Blue-Yellow)
        l_channel, a_channel, b_channel = cv2.split(lab_image)
        
        # Aplica CLAHE apenas no canal de Luminosidade (L)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l_channel_eq = clahe.apply(l_channel)
        
        # Reúne os canais novamente
        enhanced = cv2.merge([l_channel_eq, a_channel, b_channel])
        
        # 3. Denoising e Conversão final
        enhanced_bgr = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        denoised = cv2.fastNlMeansDenoisingColored(enhanced_bgr, None, 10, 10, 7, 21)
        
        # 4. Super Resolução (Upscale)
        upscaled = cv2.resize(
            denoised, 
            None, 
            fx=self.cfg.upscale_factor, 
            fy=self.cfg.upscale_factor, 
            interpolation=cv2.INTER_CUBIC
        )
        return upscaled

    def _get_crop_coords(self) -> Tuple[int, int, int, int]:
        """Calcula coordenadas do quadrado de zoom centralizado."""
        cx, cy = self.real_w // 2, self.real_h // 2
        zoom = self.state.current_zoom
        
        x1 = max(0, cx - zoom // 2)
        y1 = max(0, cy - zoom // 2)
        x2 = min(self.real_w, cx + zoom // 2)
        y2 = min(self.real_h, cy + zoom // 2)
        return x1, y1, x2, y2

    def _is_centered(self, bbox: Tuple[float, float, float, float]) -> bool:
        """Verifica se o QR está no centro da mira."""
        x1, y1, x2, y2 = bbox
        qr_cx = x1 + (x2 - x1) / 2
        qr_cy = y1 + (y2 - y1) / 2
        
        # O centro da imagem cortada (crop) é sempre metade do tamanho do zoom
        center_crop = self.state.current_zoom * self.cfg.upscale_factor / 2
        tolerance = (self.state.current_zoom * self.cfg.upscale_factor) * self.cfg.aim_tolerance_pct
        
        dist = np.sqrt((qr_cx - center_crop)**2 + (qr_cy - center_crop)**2)
        return dist < tolerance

    def _process_detections(self, frame: np.ndarray, rgb_enhanced: np.ndarray, crop_coords: Tuple[int, int, int, int]):
        """Detecta, valida e desenha os resultados."""
        if self.state.is_processing:
            return

        try:
            detections = self.qreader.detect(image=rgb_enhanced)
            
            if detections and len(detections) > 0:
                print(f"[Debug] {len(detections)} QR code(s) detectado(s)")
            
            crop_x1, crop_y1, _, _ = crop_coords
            target_detection = None

            for detection in detections:
                bbox = detection.get('bbox_xyxy')
                if bbox is None: 
                    continue

                # Verifica centralização na imagem ampliada
                is_target = self._is_centered(bbox)
                
                # Traduz coordenadas do upscale para o frame original
                bx1, by1, bx2, by2 = map(lambda v: int(v / self.cfg.upscale_factor), bbox)
                
                orig_x1, orig_y1 = bx1 + crop_x1, by1 + crop_y1
                orig_x2, orig_y2 = bx2 + crop_x1, by2 + crop_y1

                color = COLORS['YELLOW'] if is_target else COLORS['GRAY']
                thickness = 3 if is_target else 1
                cv2.rectangle(frame, (orig_x1, orig_y1), (orig_x2, orig_y2), color, thickness)

                if is_target:
                    target_detection = detection

            # Se encontrou um alvo válido, tenta decodificar
            if target_detection:
                self._decode_target(rgb_enhanced, target_detection)

        except Exception as e:
            print(f"[Aviso] Erro na detecção: {e}")

    def _decode_target(self, image: np.ndarray, detection: Dict[str, Any]):
        """Decodifica o QR code alvo."""
        try:
            print("[Debug] Tentando decodificar QR centralizado...")
            decoded = self.qreader.decode(image=image, candidates=[detection])
            if decoded and decoded[0]:
                url = decoded[0]
                print(f"[Debug] QR decodificado: {url[:60]}...")
                self._handle_url(url)
            else:
                print("[Debug] Decodificação falhou - QR não legível")
        except Exception as e:
            print(f"[Aviso] Erro decode: {e}")

    def _handle_url(self, url: str):
        """Valida URL e inicia thread de download."""
        current_time = time.time()
        
        # Debounce: evita processar a mesma URL repetidamente em curto espaço de tempo
        is_new_url = url != self.state.last_url
        is_time_elapsed = (current_time - self.state.last_time > self.cfg.reset_delay)
        
        if is_time_elapsed or is_new_url:
            if NFCE_PATTERN.match(url):
                self.state.last_url = url
                self.state.last_time = current_time
                
                # Inicia thread
                t = threading.Thread(target=self._run_scrapy_thread, args=(url,))
                t.daemon = True
                t.start()
            else:
                self.state.status = "QR Code Inválido"
                self.state.color = COLORS['RED']

    def _draw_hud(self, frame: np.ndarray, crop_coords: Tuple[int, int, int, int]):
        """Desenha a interface gráfica (HUD)."""
        h, w = frame.shape[:2]
        cx, cy = w // 2, h // 2
        x1, y1, x2, y2 = crop_coords

        # 1. Caixa de Zoom
        cv2.rectangle(frame, (x1, y1), (x2, y2), COLORS['BLACK'], 4)
        cv2.rectangle(frame, (x1, y1), (x2, y2), COLORS['BLUE'], 2)
        
        # Texto Informativo
        info = f"ZOOM: {self.state.current_zoom}px | Upscale: {self.cfg.upscale_factor}x"
        cv2.putText(frame, info, (x1, y2 + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, COLORS['BLUE'], 2)

        # 2. Mira (Crosshair)
        gap = int(self.state.current_zoom * 0.15)
        tol_px = int(self.state.current_zoom * self.cfg.aim_tolerance_pct)
        
        # Círculo
        cv2.circle(frame, (cx, cy), tol_px, COLORS['BLACK'], 3)
        cv2.circle(frame, (cx, cy), tol_px, COLORS['WHITE'], 1)
        # Linhas
        cv2.line(frame, (cx - gap, cy), (cx + gap, cy), COLORS['YELLOW'], 2)
        cv2.line(frame, (cx, cy - gap), (cx, cy + gap), COLORS['YELLOW'], 2)

        # 3. Barra de Status
        cv2.rectangle(frame, (0, 0), (w, 60), COLORS['BLACK'], -1)
        cv2.putText(frame, self.state.status, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, self.state.color, 2)

        if self.state.is_processing:
            cv2.putText(frame, "PROCESSANDO...", (w - 250, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, COLORS['YELLOW'], 2)
        print(f"[Config] Zoom inicial: {self.state.current_zoom}px | Min: {self.cfg.min_zoom} | Max: {self.cfg.max_zoom}")
        print(f"[Config] Upscale: {self.cfg.upscale_factor}x | Sharpening: {self.cfg.sharpen_strength}")
        print("[Dica] Use 'W' para afastar (menos zoom) e 'S' para aproximar (mais zoom)")
        
    def run(self):
        """Loop principal da aplicação."""
        print("[Sistema] Loop iniciado. Pressione 'Q' para sair.")
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("[Erro] Falha ao capturar frame")
                break

            # Inputs
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'): 
                break
            if key in [ord('w'), ord('W')]:
                self.state.current_zoom = min(self.state.current_zoom + 20, self.cfg.max_zoom)
            if key in [ord('s'), ord('S')]:
                self.state.current_zoom = max(self.state.current_zoom - 20, self.cfg.min_zoom)

            # Preparação da Imagem
            x1, y1, x2, y2 = self._get_crop_coords()
            cropped = frame[y1:y2, x1:x2]
            
            if cropped.size > 0:
                enhanced = self._preprocess_image(cropped)
                rgb_enhanced = cv2.cvtColor(enhanced, cv2.COLOR_BGR2RGB)
                
                # Detecção e Lógica
                self._process_detections(frame, rgb_enhanced, (x1, y1, x2, y2))
            
            # Desenha HUD
            self._draw_hud(frame, (x1, y1, x2, y2))
            
            cv2.imshow("NFCe Super Reader Pro", frame)

        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    try:
        reader = NFCeSuperReader()
        reader.run()
    except Exception as e:
        print(f"[Fatal] Erro ao iniciar aplicação: {e}")