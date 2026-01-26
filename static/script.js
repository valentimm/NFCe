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
/**
 * Iniciar scanner de QR code (MODO COMPATIBILIDADE)
 */
async function startQRScanner() {
    console.log('🎬 Iniciando scanner QR (Modo Seguro)...');
    
    try {
        clearAlerts();
        
        if (typeof Html5Qrcode === 'undefined') {
            showAlert('❌ Erro: Biblioteca não carregada.', 'error');
            return;
        }
        
        elements.qrReader.innerHTML = '';
        
        // --- MUDANÇA PRINCIPAL AQUI ---
        // Usamos uma configuração mais leve para garantir que funciona em todos os celulares
        const config = {
            fps: 10, // Mantemos FPS baixo para dar tempo de processar
            qrbox: function(viewfinderWidth, viewfinderHeight) {
                // Caixa de leitura de 70% da tela
                const minEdge = Math.min(viewfinderWidth, viewfinderHeight);
                const size = Math.floor(minEdge * 0.7);
                return {
                    width: size,
                    height: size
                };
            },
            videoConstraints: {
                facingMode: "environment",
                // MUDANÇA: Usamos apenas 'ideal', removemos 'min/max'
                // Isso diz: "Tente 1080p, mas se não der, abra o que tiver"
                width: { ideal: 1280 }, 
                height: { ideal: 720 },
                // Tenta focar, mas não quebra se não suportar
                focusMode: "continuous"
            },
            // Desativamos recursos experimentais que podem travar iPhones
            experimentalFeatures: {
                useBarCodeDetectorIfSupported: false
            }
        };
        
        state.qrScanner = new Html5Qrcode("qr-reader");
        
        showAlert('📷 Iniciando câmera...', 'info');
        
        // Iniciamos o scanner
        await state.qrScanner.start(
            { facingMode: "environment" },
            config,
            onScanSuccess,
            onScanError
        );
        
        console.log('✅ Scanner iniciado!');
        
        state.isScannerActive = true;
        state.isProcessing = false;
        
        elements.startScanBtn.style.display = 'none';
        elements.stopScanBtn.style.display = 'inline-flex';
        elements.scanResult.style.display = 'none';
        
        showAlert('✅ Câmera ativa! Aproxime o QR Code.', 'success');
        
        // Tenta aplicar foco forçado após 1 segundo (hack para Androids)
        setTimeout(() => {
            try {
                const capabilities = state.qrScanner.getRunningTrackCameraCapabilities();
                // Se suportar torch (flash), avisa o usuário ou ativa botão
                if (capabilities && capabilities.torch) {
                    console.log('Flash disponível');
                }
                // Tenta focar novamente
                state.qrScanner.applyVideoConstraints({ focusMode: "continuous" })
                    .catch(err => console.log('Foco contínuo não suportado nativamente'));
            } catch (e) {
                // Ignora erros de ajuste fino
            }
        }, 1000);
        
    } catch (err) {
        console.error('❌ Erro crítico:', err);
        
        // Se falhar, tentamos o modo MAIS BÁSICO possível (último recurso)
        if (state.qrScanner && !state.isScannerActive) {
            console.log('⚠️ Tentando reiniciar em modo VGA básico...');
            try {
                await state.qrScanner.start(
                    { facingMode: "environment" },
                    { fps: 10, qrbox: 250 }, // Configuração padrão da lib
                    onScanSuccess,
                    onScanError
                );
                state.isScannerActive = true;
                showAlert('⚠️ Modo básico ativado (baixa resolução). Aproxime bem o celular.', 'warning');
                return; // Salvou!
            } catch (err2) {
                console.error('Falha total', err2);
            }
        }

        let errorMsg = 'Erro na câmera. ';
        if (err.name === 'NotAllowedError') errorMsg += 'Verifique permissões.';
        else if (err.name === 'NotFoundError') errorMsg += 'Câmera não encontrada.';
        else errorMsg += err.message;
        
        showAlert(errorMsg, 'error');
        elements.qrReader.innerHTML = '<div class="qr-reader-placeholder"><p>❌ Erro de câmera</p></div>';
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