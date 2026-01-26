"""
NFCe Web Reader - Backend Flask
Aplicação web para ler e processar notas fiscais NFCe
"""

from flask import Flask, render_template, request, jsonify, send_file
import os
import sys
import csv
import json
from datetime import datetime
import subprocess
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'nfce-reader-secret-key-2024'

# Caminho do arquivo CSV
CSV_FILE = "nfc_data.csv"

def init_csv():
    """Inicializa o arquivo CSV se não existir"""
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(["Estabelecimento", "Produto", "Quantidade", "Unidade", "Valor_Total", "Desconto"])
        logger.info("CSV inicializado com sucesso")

def run_spider(url):
    """Executa o spider Scrapy via subprocess"""
    try:
        # Comando Scrapy com proteção para Windows
        comando = f'scrapy crawl nfcedata -a url="{url}"'
        
        # Executar Scrapy como subprocess
        result = subprocess.run(
            comando,
            cwd="nfceReader/",
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return {"success": True, "message": "NFCe processada com sucesso"}
        else:
            return {"success": False, "message": f"Erro ao processar: {result.stderr}"}
            
    except subprocess.TimeoutExpired:
        return {"success": False, "message": "Timeout ao processar NFCe"}
    except Exception as e:
        logger.error(f"Erro ao processar NFCe: {str(e)}")
        return {"success": False, "message": str(e)}

@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

@app.route('/api/process', methods=['POST'])
def process_nfce():
    """Processa uma URL de NFCe"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({"success": False, "message": "URL não fornecida"}), 400
        
        # Validar URL
        if 'fazenda' not in url.lower() or 'nfce' not in url.lower():
            return jsonify({
                "success": False, 
                "message": "URL inválida. Certifique-se de que é uma URL de NFCe"
            }), 400
        
        # Inicializar CSV se necessário
        init_csv()
        
        # Executar o spider
        result = run_spider(url)
        
        if result["success"]:
            return jsonify({
                "success": True,
                "message": "NFCe processada com sucesso!"
            })
        else:
            return jsonify({
                "success": False,
                "message": result["message"]
            }), 500
            
    except Exception as e:
        logger.error(f"Erro no endpoint /api/process: {str(e)}")
        return jsonify({
            "success": False, 
            "message": f"Erro interno: {str(e)}"
        }), 500

@app.route('/api/data', methods=['GET'])
def get_data():
    """Retorna os dados do CSV"""
    try:
        if not os.path.exists(CSV_FILE):
            return jsonify({"success": True, "data": []})
        
        data = []
        with open(CSV_FILE, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                data.append(row)
        
        return jsonify({"success": True, "data": data})
    except Exception as e:
        logger.error(f"Erro ao ler dados: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/download', methods=['GET'])
def download_csv():
    """Download do arquivo CSV"""
    try:
        if not os.path.exists(CSV_FILE):
            return jsonify({"success": False, "message": "Nenhum dado disponível"}), 404
        
        return send_file(
            CSV_FILE,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'nfce_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
    except Exception as e:
        logger.error(f"Erro ao fazer download: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/clear', methods=['POST'])
def clear_data():
    """Limpa todos os dados do CSV"""
    try:
        if os.path.exists(CSV_FILE):
            os.remove(CSV_FILE)
        init_csv()
        return jsonify({"success": True, "message": "Dados limpos com sucesso"})
    except Exception as e:
        logger.error(f"Erro ao limpar dados: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Retorna estatísticas dos dados"""
    try:
        if not os.path.exists(CSV_FILE):
            return jsonify({
                "success": True,
                "stats": {
                    "total_items": 0,
                    "total_value": 0,
                    "total_discount": 0,
                    "stores": []
                }
            })
        
        data = []
        with open(CSV_FILE, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                data.append(row)
        
        # Calcular estatísticas
        total_items = len(data)
        total_value = 0
        total_discount = 0
        stores = {}
        
        for row in data:
            # Processar valor
            valor_str = row.get('Valor_Total', '0').replace('.', '').replace(',', '.')
            try:
                valor = float(valor_str) if valor_str else 0
                total_value += valor
            except:
                pass
            
            # Processar desconto
            desconto_str = row.get('Desconto', '0').replace('-', '').replace('.', '').replace(',', '.')
            try:
                desconto = float(desconto_str) if desconto_str else 0
                total_discount += desconto
            except:
                pass
            
            # Contar por estabelecimento
            store = row.get('Estabelecimento', 'Não identificado')
            stores[store] = stores.get(store, 0) + 1
        
        store_list = [{"name": k, "count": v} for k, v in stores.items()]
        store_list.sort(key=lambda x: x['count'], reverse=True)
        
        return jsonify({
            "success": True,
            "stats": {
                "total_items": total_items,
                "total_value": round(total_value, 2),
                "total_discount": round(total_discount, 2),
                "stores": store_list[:5]  # Top 5 estabelecimentos
            }
        })
    except Exception as e:
        logger.error(f"Erro ao calcular estatísticas: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == '__main__':
    init_csv()
    port = int(os.environ.get('PORT', 5000))
    print("\n" + "="*60)
    print("🚀 NFCe Web Reader - Servidor iniciado!")
    print("="*60)
    print(f"📱 Acesse: http://localhost:{port}")
    print("💡 Pressione Ctrl+C para parar o servidor")
    print("="*60 + "\n")
    app.run(debug=os.environ.get('FLASK_ENV') != 'production', host='0.0.0.0', port=port)
