# 🚀 NFCe Web Reader - Guia de Uso

## 📋 Sobre o Projeto

Sistema web moderno e acessível para ler e processar notas fiscais NFCe. Desenvolvido com Flask (backend) e interface HTML/CSS/JavaScript responsiva.

## ✨ Funcionalidades

- 📱 **Interface Web Moderna**: Design responsivo e acessível
- 🔄 **Processamento Automático**: Cole a URL da NFCe e deixe o sistema fazer o resto
- 📊 **Dashboard com Estatísticas**: Visualize total de produtos, valores gastos e descontos
- 💾 **Exportação de Dados**: Download dos dados em formato CSV
- 🎨 **Design Acessível**: Segue boas práticas de acessibilidade (WCAG)
- ⚡ **Performance Otimizada**: Carregamento rápido e interações fluidas

## 🛠️ Tecnologias Utilizadas

### Backend
- **Flask 3.0** - Framework web Python
- **Scrapy 2.11** - Web scraping
- **Python 3.11+** - Linguagem base

### Frontend
- **HTML5** - Estrutura semântica
- **CSS3** - Design moderno com gradientes e animações
- **JavaScript Vanilla** - Sem dependências externas
- **Responsive Design** - Mobile-first approach

## 📦 Instalação

### Pré-requisitos

- [Python 3.11+](https://www.python.org/downloads/)
- pip (gerenciador de pacotes Python)

### Passo a Passo

1. **Clone o repositório** (se aplicável):
   ```bash
   git clone [seu-repositorio]
   cd NFCe
   ```

2. **Crie e ative o ambiente virtual**:
   
   Windows:
   ```bash
   python -m venv .nfce
   .\.nfce\Scripts\activate
   ```
   
   Linux/Mac:
   ```bash
   python3 -m venv .nfce
   source .nfce/bin/activate
   ```

3. **Instale as dependências**:
   ```bash
   pip install -r requirements.txt
   ```

## 🚀 Como Executar

1. **Inicie o servidor Flask**:
   ```bash
   python app.py
   ```

2. **Acesse a aplicação**:
   - Abra seu navegador em: [http://localhost:5000](http://localhost:5000)

3. **Como usar**:
   - Acesse a página da NFCe através do QR Code da sua nota fiscal
   - Copie a URL completa da página
   - Cole no campo de entrada da aplicação web
   - Clique em "Processar NFCe"
   - Aguarde o processamento (alguns segundos)
   - Visualize os dados salvos clicando em "Ver Dados"

## 📊 Funcionalidades da Interface

### Dashboard Principal
- **Produtos**: Contador total de produtos processados
- **Total Gasto**: Soma de todos os valores das notas
- **Estabelecimentos**: Quantidade de lojas diferentes
- **Descontos**: Total de descontos obtidos

### Visualização de Dados
- Tabela organizada com todos os produtos
- Filtros por estabelecimento
- Valores formatados em Real (R$)
- Responsiva para dispositivos móveis

### Ações Disponíveis
- **Ver Dados**: Visualizar todos os dados processados
- **Download CSV**: Exportar dados para planilha
- **Limpar Tudo**: Remover todos os dados salvos

## 🎨 Melhorias Implementadas

### Comparado ao Script Original

1. **Interface Gráfica**:
   - ✅ Não é mais necessário usar webcam
   - ✅ Cole diretamente a URL da NFCe
   - ✅ Design moderno e intuitivo
   - ✅ Funciona em qualquer dispositivo (mobile/desktop)

2. **Usabilidade**:
   - ✅ Feedback visual em tempo real
   - ✅ Animações suaves e agradáveis
   - ✅ Mensagens de erro claras
   - ✅ Confirmação antes de ações destrutivas

3. **Recursos Adicionais**:
   - ✅ Estatísticas em tempo real
   - ✅ Visualização dos dados antes de exportar
   - ✅ Download com nome de arquivo personalizado
   - ✅ Sistema de alertas informativo

4. **Acessibilidade**:
   - ✅ Suporte a leitores de tela
   - ✅ Navegação por teclado
   - ✅ Alto contraste
   - ✅ Textos alternativos

5. **Performance**:
   - ✅ Processamento assíncrono
   - ✅ Carregamento otimizado
   - ✅ Cache de dados
   - ✅ Compressão de resposta

## 📁 Estrutura de Arquivos

```
NFCe/
├── app.py                  # Backend Flask com API REST
├── main.py                 # Script original (mantido para referência)
├── requirements.txt        # Dependências Python
├── nfc_data.csv           # Arquivo de dados (gerado automaticamente)
│
├── templates/
│   └── index.html         # Interface principal
│
├── static/
│   ├── style.css          # Estilos CSS
│   └── script.js          # JavaScript da aplicação
│
└── nfceReader/            # Scrapy spider
    ├── scrapy.cfg
    └── nfceReader/
        ├── spiders/
        │   └── nfcedata.py
        └── ...
```

## 🔧 API Endpoints

### `POST /api/process`
Processa uma URL de NFCe
```json
{
  "url": "https://www.fazenda.pr.gov.br/nfce/..."
}
```

### `GET /api/data`
Retorna todos os dados salvos

### `GET /api/stats`
Retorna estatísticas dos dados

### `GET /api/download`
Download do arquivo CSV

### `POST /api/clear`
Limpa todos os dados

## 🐛 Troubleshooting

### Erro: "ModuleNotFoundError: No module named 'flask'"
**Solução**: Certifique-se de que o ambiente virtual está ativado e instale as dependências:
```bash
pip install -r requirements.txt
```

### Erro: "Port 5000 already in use"
**Solução**: Mude a porta no arquivo `app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # Mudou de 5000 para 5001
```

### Erro ao processar NFCe
**Solução**: 
- Verifique se a URL está correta
- Certifique-se de que é uma URL de NFCe válida
- Verifique sua conexão com a internet

## 🔐 Segurança

- ✅ Validação de entrada de dados
- ✅ Proteção contra XSS
- ✅ CSRF token (em produção)
- ✅ Sanitização de HTML

## 🚀 Próximas Melhorias (Sugestões)

- [ ] Adicionar autenticação de usuários
- [ ] Implementar PWA (Progressive Web App)
- [ ] Adicionar gráficos e relatórios
- [ ] Filtros avançados na visualização
- [ ] Exportação em múltiplos formatos (Excel, PDF)
- [ ] API para integração com outros sistemas
- [ ] Modo escuro
- [ ] Histórico de processamento

## 📝 Licença

Este projeto é de código aberto e está disponível para uso pessoal e educacional.

## 🤝 Contribuindo

Sugestões e melhorias são bem-vindas! Sinta-se à vontade para:
- Reportar bugs
- Sugerir novas funcionalidades
- Melhorar a documentação
- Contribuir com código

## 📧 Suporte

Se encontrar algum problema ou tiver dúvidas, abra uma issue no repositório.

---

**Desenvolvido com ❤️ para facilitar seu controle financeiro**
