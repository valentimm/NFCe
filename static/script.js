/**
 * NFCe Web Reader - Frontend JavaScript
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
    console.log('📱 Botão startScanBtn:', elements.startScanBtn);
    console.log('📱 Botão stopScanBtn:', elements.stopScanBtn);
    console.log('📱 Div qr-reader:', elements.qrReader);
    
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
        console.log('✅ Listener do startScanBtn registrado');
    } else {
        console.error('❌ startScanBtn não encontrado!');
    }
    
    if (elements.stopScanBtn) {
        elements.stopScanBtn.addEventListener('click', () => {
            console.log('🖱️ Botão Parar Scanner clicado!');
            stopQRScanner();
        });
        console.log('✅ Listener do stopScanBtn registrado');
    } else {
        console.error('❌ stopScanBtn não encontrado!');
    }
    
    // Modal controls
    elements.viewDataBtn.addEventListener('click', openModal);
    elements.closeModal.addEventListener('click', closeModal);
    elements.modalOverlay.addEventListener('click', closeModal);
    
    // Actions
    elements.downloadBtn.addEventListener('click', handleDownload);
    elements.clearDataBtn.addEventListener('click', handleClearData);
    
    // Keyboard accessibility
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && elements.dataModal.style.display !== 'none') {
            closeModal();
        }
    });
}

/**
 * Iniciar scanner de QR code
 */
async function startQRScanner() {
    console.log('🎬 Iniciando scanner QR...');
    
    try {
        clearAlerts();
        
        // Verificar se Html5Qrcode está disponível
        if (typeof Html5Qrcode === 'undefined') {
            console.error('❌ Biblioteca Html5Qrcode não carregada!');
            showAlert('❌ Erro: Biblioteca de scanner não carregada. Recarregue a página.', 'error');
            return;
        }
        
        // Verificar suporte a câmera
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            console.error('❌ Navigator.mediaDevices não disponível');
            showAlert('❌ Seu navegador não suporta acesso à câmera.', 'error');
            return;
        }
        
        console.log('✅ Suporte à câmera verificado');
        
        // Limpar placeholder
        elements.qrReader.innerHTML = '';
        
        // Configurar scanner com melhor desempenho
        const config = {
            fps: 30, // Aumentado para detecção mais rápida
            qrbox: function(viewfinderWidth, viewfinderHeight) {
                // Área de scan maior e responsiva
                let minEdge = Math.min(viewfinderWidth, viewfinderHeight);
                let qrboxSize = Math.floor(minEdge * 0.7);
                return {
                    width: qrboxSize,
                    height: qrboxSize
                };
            },
            aspectRatio: 1.777778, // 16:9 para melhor qualidade
            disableFlip: false, // Permite espelhamento
            experimentalFeatures: {
                useBarCodeDetectorIfSupported: true // API nativa mais rápida
            },
            // Formatos suportados
            formatsToSupport: [
                Html5QrcodeSupportedFormats.QR_CODE
            ]
        };
        
        console.log('📋 Configuração do scanner:', config);
        
        state.qrScanner = new Html5Qrcode("qr-reader");
        console.log('✅ Objeto Html5Qrcode criado');
        
        showAlert('📷 Solicitando acesso à câmera...', 'success');
        
        console.log('📸 Chamando scanner.start()...');
        
        // Usar apenas facingMode (biblioteca aceita apenas 1 propriedade)
        await state.qrScanner.start(
            { facingMode: "environment" }, // Câmera traseira
            config,
            onScanSuccess,
            onScanError
        );
        
        console.log('✅ Scanner iniciado com sucesso!');
        
        state.isScannerActive = true;
        elements.startScanBtn.style.display = 'none';
        elements.stopScanBtn.style.display = 'inline-flex';
        elements.scanResult.style.display = 'none';
        
        // Tentar ativar lanterna se disponível (Android)
        try {
            const stream = state.qrScanner.getRunningTrackCameraCapabilities();
            if (stream && stream.torch) {
                console.log('💡 Lanterna disponível');
            }
        } catch (e) {
            console.log('💡 Lanterna não disponível');
        }
        
        clearAlerts();
        showAlert('✅ Scanner ativo! Mantenha o QR Code dentro do quadrado', 'success');
        
        // Adicionar dica após 3 segundos
        setTimeout(() => {
            if (state.isScannerActive) {
                showAlert('💡 Dica: Aproxime ou afaste o celular até o QR ficar nítido', 'info');
            }
        }, 3000);
        
    } catch (err) {
        console.error('❌ Erro ao iniciar scanner:', err);
        console.error('Tipo do erro:', err.name);
        console.error('Mensagem:', err.message);
        
        let errorMsg = '❌ Erro ao acessar câmera: ';
        
        if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
            errorMsg += 'Permissão negada. Clique no ícone da câmera na barra de endereço e permita o acesso.';
        } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
            errorMsg += 'Nenhuma câmera encontrada no dispositivo.';
        } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
            errorMsg += 'Câmera já está em uso por outro aplicativo. Feche outros aplicativos de câmera.';
        } else if (err.name === 'NotSupportedError') {
            errorMsg += 'Acesso à câmera requer HTTPS. Use https://localhost ou faça deploy.';
        } else {
            errorMsg += err.message || 'Erro desconhecido. Verifique as permissões e tente novamente.';
        }
        
        showAlert(errorMsg, 'error');
        
        // Restaurar placeholder
        elements.qrReader.innerHTML = '<div class="qr-reader-placeholder"><div class="camera-icon">📷</div><p>Erro ao iniciar câmera</p><small style="color: #666; margin-top: 8px;">' + err.message + '</small></div>';
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
            
            // Restaurar placeholder
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
    console.log('✅ QR Code detectado:', decodedText);
    
    // Parar scanner imediatamente
    stopQRScanner();
    
    // Feedback visual
    elements.scanResult.style.display = 'block';
    elements.scanResult.style.animation = 'pulse 0.5s ease';
    elements.scannedUrl.textContent = decodedText;
    
    // Feedback tátil (vibração)
    if ('vibrate' in navigator) {
        navigator.vibrate([200, 100, 200]); // Vibração mais forte
    }
    
    // Feedback sonoro
    try {
        const beep = new AudioContext();
        const oscillator = beep.createOscillator();
        const gainNode = beep.createGain();
        oscillator.connect(gainNode);
        gainNode.connect(beep.destination);
        oscillator.frequency.value = 800;
        oscillator.type = 'sine';
        gainNode.gain.setValueAtTime(0.3, beep.currentTime);
        oscillator.start(beep.currentTime);
        oscillator.stop(beep.currentTime + 0.1);
    } catch (e) {
        console.log('🔇 Som não disponível');
    }
    
    // Processar automaticamente
    processNFCe(decodedText);
}

/**
 * Callback de erro do scanner
 */
function onScanError(error) {
    // Ignorar erros de "não encontrado" (são normais durante o scan)
    // console.warn('Scanner error:', error);
}
    
    // Modal controls
    elements.viewDataBtn.addEventListener('click', openModal);
    elements.closeModal.addEventListener('click', closeModal);
    elements.modalOverlay.addEventListener('click', closeModal);
    
    // Actions
    elements.downloadBtn.addEventListener('click', handleDownload);
    elements.clearDataBtn.addEventListener('click', handleClearData);
    
    // Keyboard accessibility
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && elements.dataModal.style.display !== 'none') {
            closeModal();
        }
    });

/**
 * Carregar estatísticas
 */
async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        
        if (data.success) {
            const stats = data.stats;
            
            // Animar números
            animateNumber(elements.statItems, stats.total_items);
            animateNumber(elements.statValue, stats.total_value, true);
            animateNumber(elements.statStores, stats.stores.length);
            animateNumber(elements.statDiscount, stats.total_discount, true);
        }
    } catch (error) {
        console.error('Erro ao carregar estatísticas:', error);
    }
}

/**
 * Animar números
 */
function animateNumber(element, targetValue, isCurrency = false) {
    const duration = 1000;
    const start = parseFloat(element.textContent.replace(/[^\d,.-]/g, '').replace(',', '.')) || 0;
    const end = targetValue;
    const startTime = performance.now();
    
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Easing function (easeOutCubic)
        const easeProgress = 1 - Math.pow(1 - progress, 3);
        const current = start + (end - start) * easeProgress;
        
        if (isCurrency) {
            element.textContent = formatCurrency(current);
        } else {
            element.textContent = Math.round(current).toString();
        }
        
        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }
    
    requestAnimationFrame(update);
}

/**
 * Formatar valor monetário
 */
function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(value);
}

/**
 * Abrir modal com dados
 */
async function openModal() {
    elements.dataModal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    
    // Mostrar loading
    elements.loadingTable.style.display = 'flex';
    elements.emptyState.style.display = 'none';
    elements.tableWrapper.style.display = 'none';
    
    try {
        const response = await fetch('/api/data');
        const result = await response.json();
        
        if (result.success) {
            state.currentData = result.data;
            
            if (result.data.length === 0) {
                // Mostrar estado vazio
                elements.loadingTable.style.display = 'none';
                elements.emptyState.style.display = 'flex';
            } else {
                // Mostrar tabela
                renderTable(result.data);
                elements.loadingTable.style.display = 'none';
                elements.tableWrapper.style.display = 'block';
            }
        } else {
            showAlert(`Erro ao carregar dados: ${result.message}`, 'error');
            closeModal();
        }
    } catch (error) {
        console.error('Erro ao carregar dados:', error);
        showAlert('Erro ao carregar dados do servidor.', 'error');
        closeModal();
    }
}

/**
 * Renderizar tabela de dados
 */
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
            <td style="color: ${row.Desconto ? 'var(--success)' : 'var(--gray-400)'}">
                ${escapeHtml(row.Desconto || '-')}
            </td>
        `;
        
        elements.dataTableBody.appendChild(tr);
    });
}

/**
 * Fechar modal
 */
function closeModal() {
    elements.dataModal.style.display = 'none';
    document.body.style.overflow = '';
}

/**
 * Download CSV
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
            document.body.removeChild(a);
            
            showAlert('✅ Download iniciado com sucesso!', 'success');
        } else {
            const data = await response.json();
            showAlert(`❌ Erro: ${data.message}`, 'error');
        }
    } catch (error) {
        console.error('Erro ao fazer download:', error);
        showAlert('❌ Erro ao fazer download do arquivo.', 'error');
    }
}

/**
 * Limpar dados
 */
async function handleClearData() {
    if (!confirm('⚠️ Tem certeza que deseja limpar TODOS os dados? Esta ação não pode ser desfeita!')) {
        return;
    }
    
    try {
        const response = await fetch('/api/clear', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert('✅ Dados limpos com sucesso!', 'success');
            closeModal();
            await loadStats();
        } else {
            showAlert(`❌ Erro: ${data.message}`, 'error');
        }
    } catch (error) {
        console.error('Erro ao limpar dados:', error);
        showAlert('❌ Erro ao limpar dados.', 'error');
    }
}

/**
 * Mostrar alerta
 */
function showAlert(message, type = 'success') {
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.setAttribute('role', 'alert');
    
    const icon = type === 'success' ? '✅' : '❌';
    
    alert.innerHTML = `
        <span class="alert-icon">${icon}</span>
        <span>${message}</span>
        <button class="alert-close" aria-label="Fechar alerta">×</button>
    `;
    
    const closeBtn = alert.querySelector('.alert-close');
    closeBtn.addEventListener('click', () => {
        alert.remove();
    });
    
    elements.alertContainer.appendChild(alert);
    
    // Auto-remover após 5 segundos
    setTimeout(() => {
        if (alert.parentElement) {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }
    }, 5000);
}

/**
 * Limpar todos os alertas
 */
function clearAlerts() {
    elements.alertContainer.innerHTML = '';
}

/**
 * Definir estado de loading do botão
 */
function setButtonLoading(isLoading) {
    elements.processBtn.disabled = isLoading;
    
    if (isLoading) {
        elements.btnText.style.display = 'none';
        elements.btnLoading.style.display = 'flex';
    } else {
        elements.btnText.style.display = 'block';
        elements.btnLoading.style.display = 'none';
    }
}

/**
 * Escape HTML para prevenir XSS
 */
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.toString().replace(/[&<>"']/g, m => map[m]);
}

/**
 * Detectar suporte a Service Worker (para PWA futuro)
 */
if ('serviceWorker' in navigator) {
    console.log('✅ Service Worker suportado - PWA disponível');
}
