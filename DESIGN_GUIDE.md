# 🎨 NFCe Web Reader - Guia Visual

## 📸 Screenshots e Descrição Visual

### 🎯 Interface Principal

```
┌─────────────────────────────────────────────────────────────────┐
│  📋 NFCe Reader                        📊 Ver Dados  ⬇️ Download │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│         Controle Financeiro Simplificado                         │
│    Cole a URL da sua nota fiscal NFCe e deixe a tecnologia      │
│              organizar seus dados automaticamente                │
│                                                                   │
│  ┌─────────┬─────────┬─────────┬─────────┐                     │
│  │ 🛒      │ 💰      │ 🏪      │ 🎁      │                     │
│  │ 0       │ R$ 0,00 │ 0       │ R$ 0,00 │                     │
│  │Produtos │  Total  │ Lojas   │Descontos│                     │
│  └─────────┴─────────┴─────────┴─────────┘                     │
│                                                                   │
│  Cole a URL da NFCe aqui:                                       │
│  ┌────────────────────────────────────┬──────────────────┐     │
│  │ https://www.fazenda.pr.gov.br/...  │ Processar NFCe   │     │
│  └────────────────────────────────────┴──────────────────┘     │
│                                                                   │
│  💡 Dica: Encontre o QR Code na sua nota e copie a URL          │
│                                                                   │
│  📱 Como usar:                                                   │
│  1. Acesse o site da sua nota fiscal através do QR Code         │
│  2. Copie a URL completa da página                              │
│  3. Cole a URL no campo acima e clique em "Processar"           │
│  4. Seus dados serão automaticamente salvos                     │
│  5. Use "Ver Dados" para visualizar ou "Download" para exportar │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 📊 Modal de Visualização de Dados

```
┌─────────────────────────────────────────────────────────────────┐
│  📊 Dados Salvos                      🗑️ Limpar Tudo      ✕    │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │Estabelecimento│Produto     │Qtd│UN │Valor Total│Desconto│  │
│  ├───────────────────────────────────────────────────────────┤ │
│  │Supermercado X │Arroz 5kg   │ 1 │UN │  R$ 25,90 │   -    │  │
│  │Supermercado X │Feijão 1kg  │ 2 │UN │  R$ 16,00 │ -R$ 2  │  │
│  │Padaria Y      │Pão Frances │ 1 │KG │  R$ 8,50  │   -    │  │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## 🎨 Paleta de Cores

### Cores Principais
- **Primary**: `#6366f1` - Azul/roxo vibrante
- **Success**: `#10b981` - Verde para ações positivas
- **Danger**: `#ef4444` - Vermelho para ações destrutivas
- **Background**: Gradiente roxo/azul

### Neutrals
- **Texto principal**: `#111827` (Cinza 900)
- **Texto secundário**: `#6b7280` (Cinza 500)
- **Bordas**: `#e5e7eb` (Cinza 200)
- **Background cards**: `#ffffff` (Branco)

## 📱 Design Responsivo

### Desktop (> 768px)
```
┌─────────────────────────────────────────────┐
│  Header com logo e botões lado a lado       │
├─────────────────────────────────────────────┤
│                                               │
│  [Card 1] [Card 2] [Card 3] [Card 4]        │
│                                               │
│  ┌────────────────────────────────┐         │
│  │  Formulário centralizado        │         │
│  │  Max-width: 800px              │         │
│  └────────────────────────────────┘         │
│                                               │
└─────────────────────────────────────────────┘
```

### Mobile (< 768px)
```
┌─────────────────┐
│  Logo           │
│  📊 Ver Dados   │
│  ⬇️ Download    │
├─────────────────┤
│  [Card 1]       │
│  [Card 2]       │
│  [Card 3]       │
│  [Card 4]       │
│                 │
│  ┌───────────┐ │
│  │Formulário │ │
│  │Full-width │ │
│  └───────────┘ │
└─────────────────┘
```

## ✨ Animações e Interações

### Efeitos Visuais
1. **Hover nos Cards**: Elevação com `translateY(-4px)`
2. **Loading Spinner**: Rotação suave de 360°
3. **Fade In**: Alertas aparecem com `opacity` transition
4. **Scale In**: Modal com efeito de escala
5. **Number Animation**: Contadores animados com easing

### Transições
- **Padrão**: `300ms cubic-bezier(0.4, 0, 0.2, 1)`
- **Suave e natural**: Usa easing para sensação premium

## 🎯 Acessibilidade (WCAG 2.1)

### ✅ Implementado
- ✅ Contraste adequado (AAA)
- ✅ Navegação por teclado completa
- ✅ Atributos ARIA (role, aria-label, aria-live)
- ✅ Focus visível em todos os elementos interativos
- ✅ Textos alternativos e semântica HTML5
- ✅ Suporte a leitores de tela
- ✅ Redução de animações (prefers-reduced-motion)
- ✅ Alto contraste (prefers-contrast: high)

### Teclas de Atalho
- **ESC**: Fechar modal
- **TAB**: Navegar entre elementos
- **ENTER**: Enviar formulário/confirmar ação
- **SPACE**: Ativar botões

## 🎭 Estados Visuais

### Botão Estados
```
Normal:    [Processar NFCe]
Hover:     [Processar NFCe] ↑ (elevado)
Loading:   [⟳ Processando...]
Disabled:  [Processar NFCe] (opaco)
Focus:     [Processar NFCe] (outline azul)
```

### Alertas
```
Sucesso:  ✅ NFCe processada com sucesso!
Erro:     ❌ Erro: URL inválida
Loading:  ⟳ Processando...
```

## 📐 Layout Grid

### Cards de Estatísticas
```css
display: grid;
grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
gap: 1.5rem;
```

### Formulário
```css
display: flex;
gap: 1rem;
flex-wrap: wrap; /* Responsivo */
```

### Tabela
```css
width: 100%;
border-collapse: collapse;
sticky header (position: sticky; top: 0)
```

## 🖼️ Ícones Utilizados

### Emoji Icons
- 📋 NFCe Reader (Logo)
- 🛒 Produtos
- 💰 Valor Total
- 🏪 Estabelecimentos
- 🎁 Descontos
- 📊 Visualização
- ⬇️ Download
- 🗑️ Limpar
- ✅ Sucesso
- ❌ Erro
- 💡 Dica
- 📱 Mobile

## 🎬 Fluxo de Uso

```
1. Usuário acessa → [Interface Principal]
           ↓
2. Cola URL NFCe → [Validação]
           ↓
3. Clica Processar → [Loading State]
           ↓
4. Scrapy processa → [Backend]
           ↓
5. Dados salvos → [CSV]
           ↓
6. Stats atualizados → [Dashboard]
           ↓
7. Alerta de sucesso → [✅ Processado!]
           ↓
8. Usuário pode:
   - Ver Dados (Modal)
   - Download CSV
   - Processar mais notas
```

## 🚀 Performance

### Otimizações
- ✅ CSS minificado mentalmente
- ✅ JavaScript vanilla (sem frameworks pesados)
- ✅ Lazy loading de dados
- ✅ Debounce em eventos
- ✅ RequestAnimationFrame para animações
- ✅ Processamento assíncrono

### Métricas Alvo
- **First Contentful Paint**: < 1s
- **Time to Interactive**: < 2s
- **Lighthouse Score**: > 90

## 🎨 Customização

Para personalizar cores, edite as CSS variables em `style.css`:

```css
:root {
    --primary: #6366f1;        /* Cor principal */
    --success: #10b981;        /* Sucesso */
    --danger: #ef4444;         /* Perigo */
    --spacing-md: 1rem;        /* Espaçamento */
    --radius-md: 0.5rem;       /* Border radius */
}
```

---

**Design System**: Material Design + Custom
**Tipografia**: Inter (Google Fonts)
**Inspiração**: Modern SaaS interfaces
