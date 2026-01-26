/**
 * NFCe Web Reader - Frontend JavaScript (Otimizado)
 * Gerencia a interação do usuário e comunicação com a API
 */

// Estado da aplicação
const state = {
    isProcessing: false,
    currentData: [],
    qrScanner: null,
    isScannerActive: false
};

// Elementos do DOM
const elements = {
    alertContainer: document.getElementById('alertContainer'),
    
    // Scanner
    qrReader: document.getElementById('qr-reader'),
    startScanBtn: document.getElementById('startScanBtn'),
    stopScanBtn: document.getElementById('stopScanBtn'),
    scanResult: document.getElementById('scanResult'),
    scannedUrl: document.getElementById('scannedUrl'),
    
    // Stats
    statItems: document.getElementById('statItems'),
    statValue: document.getElementById('statValue'),
    statStores: document.getElementById('statStores'),
    statDiscount: document.getElementById('statDiscount'),
    
    // Modal
    dataModal: document.getElementById('dataModal'),
    modalOverlay: document.getElementById('modalOverlay'),
    closeModal: document.getElementById('closeModal'),
    viewDataBtn: document.getElementById('viewDataBtn'),
    downloadBtn: document.getElementById('downloadBtn'),
    clearDataBtn: document.getElementById('clearDataBtn'),
    
    // Table
    loadingTable: document.getElementById('loadingTable'),
    emptyState: document.getElementById('emptyState'),
    tableWrapper: document.getElementById('tableWrapper'),
    dataTableBody: document.getElementById('dataTableBody')
};

/**
 * Inicialização
 */
console.log('🔧 Script carregado!');

document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 DOM carregado - Inicializando aplicação...');
    
    if (!elements.startScanBtn) {
        console.error('❌ Botão startScanBtn não encontrado!');
    }
    
    initEventListeners();
    loadStats();
    
    console.log('✅ Aplicação inicializada');
});

/**
 * Configurar event listeners
 */
function initEventListeners() {
    console.log('🎯 Configurando event listeners...');
    
    // Scanner controls
    if (elements.startScanBtn) {
        elements.startScanBtn.addEventListener('click', () => {
            console.log('🖱️ Botão Iniciar Scanner clicado!');
            startQRScanner();
        });
    }
    
    if (elements.stopScanBtn) {
        elements.stopScanBtn.addEventListener('click', () => {
            console.log('🖱️ Botão Parar Scanner clicado!');
            stopQRScanner();
        });
    }
    
    // Modal controls
    if (elements.viewDataBtn) elements.viewDataBtn.addEventListener('click', openModal);
    if (elements.closeModal) elements.closeModal.addEventListener('click', closeModal);
    if (elements.modalOverlay) elements.modalOverlay.addEventListener('click', closeModal);
    
    // Actions
    if (elements.downloadBtn) elements.downloadBtn.addEventListener('click', handleDownload);
    if (elements.clearDataBtn) elements.clearDataBtn.addEventListener('click', handleClearData);
    
    // Keyboard accessibility
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && elements.dataModal && elements.dataModal.style.display !== 'none') {
            closeModal();
        }
    });
}

/**
 * Iniciar scanner de QR code (OTIMIZADO PARA NFCE)
 */
async function startQRScanner() {
    console.log('🎬 Iniciando scanner QR Otimizado...');
    
    try {
        clearAlerts();
        
        // Verificar se Html5Qrcode está disponível
        if (typeof Html5Qrcode === 'undefined') {
            console.error('❌ Biblioteca Html5Qrcode não carregada!');
            showAlert('❌ Erro: Biblioteca de scanner não carregada. Recarregue a página.', 'error');
            return;
        }
        
        // Limpar placeholder
        elements.qrReader.innerHTML = '';
        
        // --- CONFIGURAÇÃO OTIMIZADA ---
        const config = {
            // FPS baixo (10-15) permite melhor exposição de luz por frame e 
            // mais tempo de CPU para processar imagens de alta resolução
            fps: 10, 
            
            qrbox: function(viewfinderWidth, viewfinderHeight) {
                // Aumentado para 75% da tela (melhor usabilidade)
                const minEdge = Math.min(viewfinderWidth, viewfinderHeight);
                const size = Math.floor(minEdge * 0.75);
                return {
                    width: size,
                    height: size
                };
            },
            // aspectRatio removido para usar o nativo do sensor
            videoConstraints: {
                facingMode: "environment",
                focusMode: "continuous",
                // Forçar alta resolução (CRÍTICO para QR codes densos de notas)
                width: { min: 1024, ideal: 1920, max: 3840 },
                height: { min: 720, ideal: 1080, max: 2160 }
            },
            experimentalFeatures: {
                useBarCodeDetectorIfSupported: true
            }
        };
        
        console.log('📋 Configuração do scanner:', config);
        
        state.qrScanner = new Html5Qrcode("qr-reader");
        
        showAlert('📷 Iniciando câmera em Alta Resolução...', 'info');
        
        await state.qrScanner.start(
            { facingMode: "environment" },
            config,
            onScanSuccess,
            onScanError
        );
        
        console.log('✅ Scanner iniciado com sucesso!');
        
        state.isScannerActive = true;
        state.isProcessing = false;
        
        // UI Updates
        elements.startScanBtn.style.display = 'none';
        elements.stopScanBtn.style.display = 'inline-flex';
        elements.scanResult.style.display = 'none';
        
        // Tentar ativar configurações avançadas (Flash/Zoom) após início
        setTimeout(async () => {
            try {
                // Tenta aplicar foco contínuo novamente via constraints avançadas
                const capabilities = state.qrScanner.getRunningTrackCameraCapabilities();
                
                if (state.qrScanner.applyVideoConstraints) {
                     await state.qrScanner.applyVideoConstraints({
                        focusMode: "continuous",
                        advanced: [{ focusMode: "continuous" }]
                     });
                }

                // Auto-activar flash se estiver muito escuro (opcional/hardware dependente)
                // Se preferir botão manual, remova este bloco
                if (capabilities && capabilities.torch) {
                   // Apenas loga disponibilidade, não força ativação para não cegar o usuário
                   console.log('💡 Flash disponível'); 
                   showAlert('💡 Dica: Toque na tela para focar (se disponível)', 'info');
                }
            } catch (e) {
                console.log('⚠️ Ajustes finos de câmera não suportados:', e);
            }
        }, 800);
        
    } catch (err) {
        console.error('❌ Erro ao iniciar scanner:', err);
        
        let errorMsg = 'Erro ao acessar câmera: ';
        if (err.name === 'NotAllowedError') errorMsg = 'Permissão negada. Verifique as configurações.';
        else if (err.name === 'NotFoundError') errorMsg = 'Nenhuma câmera encontrada.';
        else if (err.name === 'NotReadableError') errorMsg = 'Câmera em uso por outro app.';
        else errorMsg += err.message;
        
        showAlert(errorMsg, 'error');
        
        // Restaurar placeholder
        elements.qrReader.innerHTML = '<div class="qr-reader-placeholder"><div class="camera-icon">📷</div><p>Erro na câmera</p></div>';
    }
}

/**
 * Parar scanner de QR code
 */
async function stopQRScanner() {
    try {
        if (state.qrScanner && state.isScannerActive) {
            await state.qrScanner.stop();
            state.qrScanner.clear();
            state.isScannerActive = false;
            elements.startScanBtn.style.display = 'inline-flex';
            elements.stopScanBtn.style.display = 'none';
            
            elements.qrReader.innerHTML = '<div class="qr-reader-placeholder"><div class="camera-icon">📷</div><p>Clique em "Iniciar Scanner" para começar</p></div>';
            
            showAlert('⏹️ Scanner parado', 'success');
        }
    } catch (err) {
        console.error('Erro ao parar scanner:', err);
    }
}

/**
 * Callback de sucesso do scanner
 */
function onScanSuccess(decodedText, decodedResult) {
    if (state.isProcessing) return;
    
    console.log('✅ QR Code detectado:', decodedText);
    state.isProcessing = true;
    
    // Feedback visual
    elements.scanResult.style.display = 'block';
    elements.scanResult.style.animation = 'pulse 0.5s ease';
    elements.scannedUrl.textContent = decodedText.substring(0, 50) + '...';
    
    // Feedback tátil
    if ('vibrate' in navigator) navigator.vibrate([200]);
    
    // Feedback sonoro
    playBeep();
    
    processNFCe(decodedText);
}

/**
 * Callback de erro do scanner
 */
function onScanError(error) {
    // Ignora erros de frame vazio
}

/**
 * Helper para som
 */
function playBeep() {
    try {
        const beep = new AudioContext();
        const oscillator = beep.createOscillator();
        const gainNode = beep.createGain();
        oscillator.connect(gainNode);
        gainNode.connect(beep.destination);
        oscillator.frequency.value = 800;
        oscillator.type = 'sine';
        gainNode.gain.setValueAtTime(0.1, beep.currentTime);
        oscillator.start(beep.currentTime);
        oscillator.stop(beep.currentTime + 0.1);
    } catch (e) { /* Ignorar se falhar */ }
}

/**
 * Processar NFCe usando Scrapy Spider
 */
async function processNFCe(url) {
    clearAlerts();
    showAlert('⏳ Processando NFCe... Aguarde.', 'info');
    
    try {
        const response = await fetch('/api/process', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });
        
        const data = await response.json();
        
        if (!response.ok) throw new Error(data.error || 'Erro ao processar NFCe');
        
        showAlert('✅ Sucesso! Aguarde 3s para próxima...', 'success');
        await loadStats();
        
        setTimeout(() => {
            elements.scanResult.style.display = 'none';
            state.isProcessing = false;
            if (state.isScannerActive) {
                showAlert('📷 Pronto para próximo QR Code', 'success');
            }
        }, 3000);
        
    } catch (error) {
        console.error('❌ Erro:', error);
        showAlert(`❌ ${error.message}`, 'error');
        setTimeout(() => {
            state.isProcessing = false;
            elements.scanResult.style.display = 'none';
        }, 2000);
    }
}

/**
 * Carregar estatísticas
 */
async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        
        if (data.success && data.stats) {
            animateNumber(elements.statItems, data.stats.total_items);
            animateNumber(elements.statValue, data.stats.total_value, true);
            animateNumber(elements.statStores, data.stats.stores.length);
            animateNumber(elements.statDiscount, data.stats.total_discount, true);
        }
    } catch (error) {
        console.error('Erro stats:', error);
    }
}

/**
 * Animar números
 */
function animateNumber(element, targetValue, isCurrency = false) {
    if(!element) return;
    const duration = 1000;
    const start = parseFloat(element.textContent.replace(/[^\d,.-]/g, '').replace(',', '.')) || 0;
    const end = targetValue;
    const startTime = performance.now();
    
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const easeProgress = 1 - Math.pow(1 - progress, 3);
        const current = start + (end - start) * easeProgress;
        
        element.textContent = isCurrency ? formatCurrency(current) : Math.round(current).toString();
        
        if (progress < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
}

function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
}

/**
 * Modal e Tabela
 */
async function openModal() {
    elements.dataModal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    elements.loadingTable.style.display = 'flex';
    elements.emptyState.style.display = 'none';
    elements.tableWrapper.style.display = 'none';
    
    try {
        const response = await fetch('/api/data');
        const result = await response.json();
        
        if (result.success) {
            state.currentData = result.data;
            if (result.data.length === 0) {
                elements.loadingTable.style.display = 'none';
                elements.emptyState.style.display = 'flex';
            } else {
                renderTable(result.data);
                elements.loadingTable.style.display = 'none';
                elements.tableWrapper.style.display = 'block';
            }
        } else {
            showAlert(`Erro: ${result.message}`, 'error');
            closeModal();
        }
    } catch (error) {
        showAlert('Erro de conexão.', 'error');
        closeModal();
    }
}

function renderTable(data) {
    elements.dataTableBody.innerHTML = '';
    data.forEach((row, index) => {
        const tr = document.createElement('tr');
        tr.style.animationDelay = `${index * 0.02}s`;
        tr.innerHTML = `
            <td><strong>${escapeHtml(row.Estabelecimento || 'N/A')}</strong></td>
            <td>${escapeHtml(row.Produto || 'N/A')}</td>
            <td>${escapeHtml(row.Quantidade || 'N/A')}</td>
            <td>${escapeHtml(row.Unidade || 'N/A')}</td>
            <td><strong>${escapeHtml(row.Valor_Total || 'N/A')}</strong></td>
            <td style="color: ${row.Desconto ? 'var(--success)' : 'var(--gray-400)'}">${escapeHtml(row.Desconto || '-')}</td>
        `;
        elements.dataTableBody.appendChild(tr);
    });
}

function closeModal() {
    elements.dataModal.style.display = 'none';
    document.body.style.overflow = '';
}

/**
 * Utils: Download, Clear, Alerts
 */
async function handleDownload() {
    try {
        const response = await fetch('/api/download');
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `nfce_data_${new Date().toISOString().slice(0, 10)}.csv`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();
            showAlert('✅ Download iniciado!', 'success');
        } else {
            const data = await response.json();
            showAlert(`❌ ${data.message}`, 'error');
        }
    } catch (error) { showAlert('❌ Erro no download.', 'error'); }
}

async function handleClearData() {
    if (!confirm('⚠️ Limpar TODOS os dados?')) return;
    try {
        const response = await fetch('/api/clear', { method: 'POST' });
        const data = await response.json();
        if (data.success) {
            showAlert('✅ Dados limpos!', 'success');
            closeModal();
            loadStats();
        } else {
            showAlert(`❌ ${data.message}`, 'error');
        }
    } catch (error) { showAlert('❌ Erro ao limpar.', 'error'); }
}

function showAlert(message, type = 'success') {
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `<span class="alert-icon">${type === 'success' ? '✅' : '❌'}</span><span>${message}</span><button class="alert-close">×</button>`;
    
    alert.querySelector('.alert-close').addEventListener('click', () => alert.remove());
    elements.alertContainer.appendChild(alert);
    setTimeout(() => { if (alert.parentElement) alert.remove(); }, 5000);
}

function clearAlerts() { elements.alertContainer.innerHTML = ''; }

function escapeHtml(text) {
    const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
    return text.toString().replace(/[&<>"']/g, m => map[m]);
}

if ('serviceWorker' in navigator) console.log('✅ PWA Support Ready');