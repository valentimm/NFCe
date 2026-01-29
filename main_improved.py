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
    
    # Processamento de Imagem Avançado
    sharpen_strength: float = 2.0  # Mais agressivo
    use_adaptive_processing: bool = True
    use_multiscale_detection: bool = True
    scales: Tuple[float, ...] = (0.5, 0.75, 1.0, 1.25, 1.5, 2.0)  # Escalas para QR pequenos
    use_upscaling: bool = True  # Upscale para cédulas pequenas
    upscale_factor: float = 2.0  # 2x upscaling para cores pequenas
    
    # Resolução da Câmera
    cam_width: int = 1920
    cam_height: int = 1080
    
    # Performance
    fps_target: int = 30  # FPS alvo da câmera

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
        self.cap = cv2.VideoCapture(self.cfg.camera_index, cv2.CAP_DSHOW)  # DirectShow no Windows
        if not self.cap.isOpened():
            raise RuntimeError(f"Não foi possível abrir a câmera {self.cfg.camera_index}")
        
        # Configurações otimizadas
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.cfg.cam_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.cfg.cam_height)
        self.cap.set(cv2.CAP_PROP_FPS, self.cfg.fps_target)
        self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)  # Autofoco ativo
        self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)  # Auto-exposição
        
        w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        print(f"[Sistema] Resolução: {w}x{h} @ {fps}fps")

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
        """Aplica processamento avançado para detectar QR codes muito pequenos."""
        # 0. Upscaling para QR codes muito pequenos
        if self.cfg.use_upscaling:
            h, w = image.shape[:2]
            image = cv2.resize(image, (int(w * self.cfg.upscale_factor), int(h * self.cfg.upscale_factor)),
                             interpolation=cv2.INTER_CUBIC)
        
        # 1. Reduzir ruído mantendo bordas (mais agressivo)
        denoised = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
        
        # 2. Sharpening super agressivo
        kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]]) * self.cfg.sharpen_strength
        sharpened = cv2.filter2D(denoised, -1, kernel)
        
        # 3. Mórphological operations para fortalecer bordas
        kernel_morph = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        morph = cv2.morphologyEx(sharpened, cv2.MORPH_CLOSE, kernel_morph, iterations=1)
        morph = cv2.morphologyEx(morph, cv2.MORPH_OPEN, kernel_morph, iterations=1)
        
        # 4. Equalização adaptativa (CLAHE) em LAB
        lab_image = cv2.cvtColor(morph, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab_image)
        
        clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8))  # Más agressivo
        l_channel_eq = clahe.apply(l_channel)
        
        enhanced = cv2.merge([l_channel_eq, a_channel, b_channel])
        rgb_enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2RGB)
        
        # 5. Unsharp mask duplo para realçar detalhes
        gaussian1 = cv2.GaussianBlur(rgb_enhanced, (0, 0), 1.0)
        unsharp1 = cv2.addWeighted(rgb_enhanced, 2.0, gaussian1, -1.0, 0)
        
        gaussian2 = cv2.GaussianBlur(unsharp1, (0, 0), 2.0)
        unsharp2 = cv2.addWeighted(unsharp1, 1.5, gaussian2, -0.5, 0)
        
        # 6. Contrast stretching (normalização de contraste)
        p2, p98 = np.percentile(unsharp2, (2, 98))
        if p98 - p2 > 0:
            final = np.clip((unsharp2 - p2) * 255 / (p98 - p2), 0, 255).astype(np.uint8)
        else:
            final = unsharp2.astype(np.uint8)
        
        return final

    def _process_frame(self, frame: np.ndarray):
        """Processa o frame com detecção em múltiplas escalas (inclui QR muito pequenos)."""
        if self.state.is_processing:
            return

        # Prepara imagem base
        rgb_frame = self._enhance_frame(frame)
        all_detections = []

        try:
            if self.cfg.use_multiscale_detection:
                # Detecta em múltiplas escalas para melhor cobertura (especial para pequenos)
                for scale in self.cfg.scales:
                    try:
                        if scale != 1.0:
                            h, w = rgb_frame.shape[:2]
                            scaled = cv2.resize(rgb_frame, (int(w * scale), int(h * scale)), 
                                              interpolation=cv2.INTER_CUBIC if scale > 1 else cv2.INTER_AREA)
                            detections = self.qreader.detect(image=scaled)
                            
                            # Ajustar coordenadas de volta para escala original
                            for det in detections:
                                if det.get('bbox_xyxy') is not None:
                                    bbox = det['bbox_xyxy']
                                    det['bbox_xyxy'] = tuple(coord / scale for coord in bbox)
                                    det['scale'] = scale
                                    det['confidence'] = det.get('confidence', 1.0)
                                    all_detections.append(det)
                        else:
                            detections = self.qreader.detect(image=rgb_frame)
                            for det in detections:
                                det['scale'] = 1.0
                                det['confidence'] = det.get('confidence', 1.0)
                                all_detections.append(det)
                    except Exception as e:
                        print(f"[Aviso] Escala {scale}: {e}")
                        continue
            else:
                # Detecção simples na escala original
                detections = self.qreader.detect(image=rgb_frame)
                all_detections = detections
            
            # Remover duplicatas (QR codes detectados em múltiplas escalas)
            unique_detections = self._remove_duplicate_detections(all_detections)
            
            # Processar cada detecção única
            for detection in unique_detections:
                bbox = detection.get('bbox_xyxy')
                if bbox is None: 
                    continue

                x1, y1, x2, y2 = map(int, bbox)
                scale = detection.get('scale', 1.0)
                confidence = detection.get('confidence', 1.0)
                
                # Desenha retângulo com cor baseada na escala
                if scale < 1.0:
                    color = COLORS['RED']  # Vermelho para escalas pequenas
                elif scale == 1.0:
                    color = COLORS['GREEN']  # Verde para escala original
                else:
                    color = COLORS['BLUE']  # Azul para escalas grandes
                
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
                
                # Mostrar escala e confiança de detecção
                info = f"{scale:.2f}x | {int(confidence*100)}%"
                cv2.putText(frame, info, (x1, y1-10), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                
                # Tenta decodificar com múltiplas técnicas
                self._decode_and_act(rgb_frame, detection, frame)
                
        except Exception as e:
            print(f"[Aviso] Erro no processamento: {e}")
    
    def _remove_duplicate_detections(self, detections: list) -> list:
        """Remove detecções duplicadas usando IoU (Intersection over Union)."""
        if len(detections) <= 1:
            return detections
        
        unique = []
        for det in detections:
            bbox1 = det.get('bbox_xyxy')
            if bbox1 is None:
                continue
            
            is_duplicate = False
            for unique_det in unique:
                bbox2 = unique_det.get('bbox_xyxy')
                if bbox2 is None:
                    continue
                
                # Calcular IoU
                iou = self._calculate_iou(bbox1, bbox2)
                if iou > 0.5:  # 50% de sobreposição = duplicata
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique.append(det)
        
        return unique
    
    def _calculate_iou(self, bbox1: tuple, bbox2: tuple) -> float:
        """Calcula Intersection over Union entre dois bounding boxes."""
        x1_1, y1_1, x2_1, y2_1 = bbox1
        x1_2, y1_2, x2_2, y2_2 = bbox2
        
        # Área de interseção
        x1_i = max(x1_1, x1_2)
        y1_i = max(y1_1, y1_2)
        x2_i = min(x2_1, x2_2)
        y2_i = min(y2_1, y2_2)
        
        if x2_i < x1_i or y2_i < y1_i:
            return 0.0
        
        intersection = (x2_i - x1_i) * (y2_i - y1_i)
        
        # Área de união
        area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
        area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0.0

    def _decode_and_act(self, image: np.ndarray, detection: Dict[str, Any], display_frame: np.ndarray):
        """Tenta decodificar QR code com múltiplas técnicas (otimizado para pequenos)."""
        decoded_text = None
        
        try:
            # Tentativa 1: Decodificação direta
            decoded = self.qreader.decode(image=image, candidates=[detection])
            if decoded and decoded[0]:
                decoded_text = decoded[0]
        except Exception as e:
            pass
        
        # Tentativa 2: Se falhou, tentar com recorte, expansão e processamento extra
        if not decoded_text:
            try:
                bbox = detection.get('bbox_xyxy')
                if bbox:
                    x1, y1, x2, y2 = map(int, bbox)
                    
                    # Expandir área do QR em 30% para pegar bordas (maior margem para pequenos)
                    margin = 0.3
                    h, w = image.shape[:2]
                    w_bbox = x2 - x1
                    h_bbox = y2 - y1
                    
                    x1_exp = max(0, int(x1 - w_bbox * margin))
                    y1_exp = max(0, int(y1 - h_bbox * margin))
                    x2_exp = min(w, int(x2 + w_bbox * margin))
                    y2_exp = min(h, int(y2 + h_bbox * margin))
                    
                    # Recortar região
                    cropped = image[y1_exp:y2_exp, x1_exp:x2_exp]
                    
                    if cropped.size > 0:
                        # Tentar múltiplas binarizações
                        binary_methods = [
                            # Método 1: Binarização adaptativa Gaussiana
                            cv2.adaptiveThreshold(
                                cv2.cvtColor(cropped, cv2.COLOR_RGB2GRAY), 255, 
                                cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
                            ),
                            # Método 2: Binarização adaptativa Média
                            cv2.adaptiveThreshold(
                                cv2.cvtColor(cropped, cv2.COLOR_RGB2GRAY), 255, 
                                cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 2
                            ),
                            # Método 3: Otsu
                            cv2.threshold(cv2.cvtColor(cropped, cv2.COLOR_RGB2GRAY), 0, 255, 
                                        cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1],
                        ]
                        
                        for binary in binary_methods:
                            rgb_binary = cv2.cvtColor(binary, cv2.COLOR_GRAY2RGB)
                            
                            try:
                                decoded = self.qreader.detect_and_decode(image=rgb_binary)
                                if decoded and len(decoded) > 0 and decoded[0]:
                                    decoded_text = decoded[0]
                                    break
                            except:
                                continue
                        
            except Exception as e:
                pass
        
        # Tentativa 3: Inverter cores se ainda não decodificou (caso inverso branco/preto)
        if not decoded_text:
            try:
                bbox = detection.get('bbox_xyxy')
                if bbox:
                    x1, y1, x2, y2 = map(int, bbox)
                    margin = 0.3
                    h, w = image.shape[:2]
                    w_bbox = x2 - x1
                    h_bbox = y2 - y1
                    
                    x1_exp = max(0, int(x1 - w_bbox * margin))
                    y1_exp = max(0, int(y1 - h_bbox * margin))
                    x2_exp = min(w, int(x2 + w_bbox * margin))
                    y2_exp = min(h, int(y2 + h_bbox * margin))
                    
                    cropped = image[y1_exp:y2_exp, x1_exp:x2_exp]
                    
                    if cropped.size > 0:
                        # Inverter e tentar novamente
                        inverted = cv2.bitwise_not(cropped)
                        decoded = self.qreader.detect_and_decode(image=inverted)
                        if decoded and len(decoded) > 0 and decoded[0]:
                            decoded_text = decoded[0]
            except:
                pass
        
        # Se conseguiu decodificar, processar URL
        if decoded_text:
            # Feedback visual de sucesso
            bbox = detection.get('bbox_xyxy')
            if bbox:
                x1, y1, x2, y2 = map(int, bbox)
                cv2.putText(display_frame, "LIDO! ✓", (x1, y2+25), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.8, COLORS['GREEN'], 2)
            
            self._handle_url(decoded_text)

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
        
        # Barra superior expandida
        cv2.rectangle(frame, (0, 0), (w, 60), COLORS['BLACK'], -1)
        
        # Texto Status
        cv2.putText(frame, self.state.status, (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 
                   0.9, self.state.color, 2)
        
        # Info de detecção
        info = f"Multi-Scale: {'ON' if self.cfg.use_multiscale_detection else 'OFF'} | FPS: {int(self.cap.get(cv2.CAP_PROP_FPS))}"
        cv2.putText(frame, info, (20, 55), cv2.FONT_HERSHEY_SIMPLEX, 
                   0.4, COLORS['WHITE'], 1)
        
        if self.state.is_processing:
            cv2.putText(frame, "PROCESSANDO...", (w - 250, 35), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, COLORS['BLUE'], 2)
        
        # Legenda de cores (canto inferior direito)
        legend_y = h - 40
        cv2.putText(frame, "Verde: 1.0x | Azul: Outras escalas", (w - 350, legend_y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLORS['WHITE'], 1)

    def run(self):
        print("[Sistema] NFCe Reader OTIMIZADO para QR PEQUENOS!")
        print("[Config] Multi-Scale:", "ATIVO" if self.cfg.use_multiscale_detection else "INATIVO")
        print("[Config] Escalas:", self.cfg.scales)
        print("[Config] Upscaling:", "ATIVO (2x)" if self.cfg.use_upscaling else "INATIVO")
        print("[Config] Sharpening:", self.cfg.sharpen_strength)
        print("[Dica] Pressione 'Q' para sair")
        print("=" * 60)
        
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