"""
Script melhorado para leitura de NFCe via webcam
Mantém compatibilidade com o script original, mas com melhorias
"""

import cv2
from pyzbar import pyzbar
import subprocess
import csv
import os
import time
from datetime import datetime
import sys

# Configurações
CAMERA_INDEX = 1  # Índice da câmera (0 para webcam padrão, 1 para Iriun)
RESET_DELAY = 5  # Tempo de espera entre leituras em segundos
CSV_FILE = "nfc_data.csv"

# Cores para interface (BGR)
COLOR_GREEN = (0, 255, 0)
COLOR_RED = (0, 0, 255)
COLOR_BLUE = (255, 0, 0)
COLOR_WHITE = (255, 255, 255)


def init_csv():
    """Inicializa o arquivo CSV se ele não existir"""
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(["Estabelecimento", "Produto", "Quantidade", "Unidade", "Valor_Total", "Desconto"])
        print(f"[✓] Planilha inicializada: {CSV_FILE}")
    else:
        print(f"[✓] Usando planilha existente: {CSV_FILE}")


def validate_nfce_url(url):
    """Valida se a URL é de uma NFCe válida"""
    required_keywords = ['fazenda', 'nfce']
    return all(keyword in url.lower() for keyword in required_keywords)


def process_nfce(url):
    """Processa uma NFCe via Scrapy"""
    if not validate_nfce_url(url):
        print(f"[✗] URL inválida: {url}")
        return False
    
    print(f"[→] Processando NFCe...")
    
    # Comando Scrapy com proteção para Windows
    comando = f'scrapy crawl nfcedata -a url="{url}"'
    
    try:
        # Executar Scrapy
        result = subprocess.Popen(
            comando,
            cwd="nfceReader/",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Aguardar conclusão com timeout
        stdout, stderr = result.communicate(timeout=30)
        
        if result.returncode == 0:
            print(f"[✓] NFCe processada com sucesso!")
            return True
        else:
            print(f"[✗] Erro ao processar NFCe")
            if stderr:
                print(f"    Detalhes: {stderr.decode('utf-8', errors='ignore')}")
            return False
            
    except subprocess.TimeoutExpired:
        result.kill()
        print(f"[✗] Timeout ao processar NFCe (>30s)")
        return False
    except Exception as e:
        print(f"[✗] Erro: {str(e)}")
        return False


def draw_info_panel(frame, last_scan_time, total_scans):
    """Desenha painel de informações na tela"""
    height, width = frame.shape[:2]
    
    # Fundo semi-transparente
    overlay = frame.copy()
    cv2.rectangle(overlay, (10, 10), (width - 10, 120), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
    
    # Textos informativos
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(frame, "NFCe Reader - Webcam Mode", (20, 35), font, 0.7, COLOR_WHITE, 2)
    cv2.putText(frame, f"Escaneamentos: {total_scans}", (20, 65), font, 0.5, COLOR_GREEN, 1)
    
    if last_scan_time:
        time_since = int(time.time() - last_scan_time)
        cv2.putText(frame, f"Ultimo scan: {time_since}s atras", (20, 90), font, 0.5, COLOR_BLUE, 1)
    
    cv2.putText(frame, "Pressione 'Q' para sair | 'S' para stats", (20, 110), font, 0.4, COLOR_WHITE, 1)


def show_stats():
    """Exibe estatísticas dos dados processados"""
    if not os.path.exists(CSV_FILE):
        print("\n[!] Nenhum dado encontrado ainda.")
        return
    
    with open(CSV_FILE, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=';')
        data = list(reader)
    
    if not data:
        print("\n[!] Nenhum dado processado ainda.")
        return
    
    # Calcular estatísticas
    total_items = len(data)
    estabelecimentos = set()
    total_valor = 0
    total_desconto = 0
    
    for row in data:
        estabelecimentos.add(row.get('Estabelecimento', ''))
        
        # Processar valor
        try:
            valor_str = row.get('Valor_Total', '0').replace('.', '').replace(',', '.')
            total_valor += float(valor_str) if valor_str else 0
        except:
            pass
        
        # Processar desconto
        try:
            desconto_str = row.get('Desconto', '0').replace('-', '').replace('.', '').replace(',', '.')
            total_desconto += float(desconto_str) if desconto_str else 0
        except:
            pass
    
    # Exibir estatísticas
    print("\n" + "="*60)
    print("📊 ESTATÍSTICAS DE NOTAS FISCAIS")
    print("="*60)
    print(f"🛒 Total de produtos: {total_items}")
    print(f"🏪 Estabelecimentos diferentes: {len(estabelecimentos)}")
    print(f"💰 Valor total gasto: R$ {total_valor:.2f}")
    print(f"🎁 Total de descontos: R$ {total_desconto:.2f}")
    print(f"💵 Valor líquido: R$ {total_valor - total_desconto:.2f}")
    print("="*60 + "\n")


def main():
    """Função principal do leitor de QR Code"""
    print("\n" + "="*60)
    print("🚀 NFCe Reader - Modo Webcam")
    print("="*60)
    print("📋 Configurações:")
    print(f"   - Câmera: índice {CAMERA_INDEX}")
    print(f"   - Delay entre leituras: {RESET_DELAY}s")
    print(f"   - Arquivo de saída: {CSV_FILE}")
    print("="*60 + "\n")
    
    # Inicializar CSV
    init_csv()
    
    # Tentar abrir a câmera
    cap = cv2.VideoCapture(CAMERA_INDEX)
    
    if not cap.isOpened():
        print(f"[✗] Erro: Não foi possível abrir a câmera no índice {CAMERA_INDEX}")
        print(f"[!] Tente usar índice 0 (webcam padrão)")
        return
    
    print("[✓] Câmera iniciada com sucesso!")
    print("[→] Aguardando QR codes...\n")
    
    last_read_time = 0
    total_scans = 0
    
    try:
        while True:
            ret, frame = cap.read()
            
            if not ret:
                print("[✗] Erro ao capturar frame")
                continue
            
            # Decodificar QR codes
            qrcodes = pyzbar.decode(frame)
            current_time = time.time()
            
            # Processar QR codes encontrados
            for qrcode in qrcodes:
                url = qrcode.data.decode('utf-8')
                
                # Desenhar retângulo ao redor do QR code
                (x, y, w, h) = qrcode.rect
                cv2.rectangle(frame, (x, y), (x + w, y + h), COLOR_GREEN, 4)
                
                # Verificar delay entre leituras
                if current_time - last_read_time > RESET_DELAY:
                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] QR Code detectado!")
                    
                    if process_nfce(url):
                        total_scans += 1
                        last_read_time = current_time
                        
                        # Feedback visual
                        cv2.putText(frame, "PROCESSADO!", (x, y - 10), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, COLOR_GREEN, 2)
                    else:
                        # Erro no processamento
                        cv2.putText(frame, "ERRO!", (x, y - 10), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, COLOR_RED, 2)
            
            # Desenhar painel de informações
            draw_info_panel(frame, last_read_time, total_scans)
            
            # Mostrar frame
            cv2.imshow("NFCe Reader", frame)
            
            # Verificar teclas pressionadas
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q') or key == ord('Q'):
                print("\n[→] Encerrando...")
                break
            elif key == ord('s') or key == ord('S'):
                show_stats()
                
    except KeyboardInterrupt:
        print("\n[→] Interrompido pelo usuário")
    
    finally:
        # Limpar recursos
        cap.release()
        cv2.destroyAllWindows()
        
        # Estatísticas finais
        print("\n" + "="*60)
        print("✅ Sessão encerrada!")
        print(f"📊 Total de NFCes processadas: {total_scans}")
        print(f"💾 Dados salvos em: {CSV_FILE}")
        print("="*60 + "\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[✗] Erro fatal: {str(e)}")
        sys.exit(1)
