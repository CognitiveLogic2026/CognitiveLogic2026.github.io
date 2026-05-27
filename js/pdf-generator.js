/*
 * Copyright (c) 2026 Roberto Bob Malini - Cognitive Logic
 * https://www.cognitivelogic.it
 * Licensed under CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/)
 */
function initPdfGenerator() {
    console.log('[PDF] Inizializzazione...');
    const resultBox = document.getElementById('resultBox');
    if (!resultBox) return;
    
    const observer = new MutationObserver(() => {
        if (resultBox.classList.contains('show') && !document.getElementById('downloadPdfBtn')) {
            addPdfDownloadButton();
        }
    });
    observer.observe(resultBox, { attributes: true });
}

function addPdfDownloadButton() {
    const resultBox = document.getElementById('resultBox');
    const downloadBtn = document.createElement('button');
    downloadBtn.id = 'downloadPdfBtn';
    downloadBtn.className = 'btn btn-primary';
    downloadBtn.style.marginTop = '16px';
    downloadBtn.style.width = '100%';
    downloadBtn.innerHTML = '📥 Scarica PDF';
    downloadBtn.onclick = generateAndDownloadPdf;
    
    const upsellBox = resultBox.querySelector('.upsell-box');
    if (upsellBox) {
        upsellBox.parentNode.insertBefore(downloadBtn, upsellBox);
    } else {
        resultBox.appendChild(downloadBtn);
    }
    console.log('[PDF] Bottone aggiunto');
}

async function generateAndDownloadPdf(e) {
    if (e) e.preventDefault();
    const btn = document.getElementById('downloadPdfBtn');
    const originalText = btn.innerHTML;
    
    try {
        btn.disabled = true;
        btn.innerHTML = '⏳ Generazione...';
        
        const pdfData = collectPdfData();
        console.log('[PDF] Dati raccolti:', pdfData);
        
        const response = await fetch('https://api.cognitivelogic.it/api/pdf-export', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(pdfData)
        });
        
        if (!response.ok) {
            throw new Error(`Errore server: ${response.status}`);
        }
        
        const blob = await response.blob();
        downloadBlob(blob, pdfData.filename);
        
        btn.innerHTML = '✓ Scaricato';
        setTimeout(() => {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }, 2000);
        
    } catch (error) {
        console.error('[PDF] Errore:', error);
        alert('Errore: ' + error.message);
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

function collectPdfData() {
    const stabilimento = document.getElementById('stabilimento')?.value || '';
    const comune = document.getElementById('comune')?.value || '';
    const modulo = document.getElementById('modulo')?.value || '';
    
    const scoreNumber = document.getElementById('scoreNumber')?.textContent?.trim() || '0';
    const scoreTier = document.getElementById('scoreTier')?.textContent?.replace('◆ ', '') || '';
    const vectorVs = document.getElementById('vectorVs')?.textContent || '0';
    const vectorVa = document.getElementById('vectorVa')?.textContent || '0';
    const vectorVt = document.getElementById('vectorVt')?.textContent || '0';
    const resultText = document.getElementById('resultText')?.innerHTML || '';
    
    const now = new Date();
    const timestamp = now.toISOString();
    const dateStr = now.toLocaleDateString('it-IT').replace(/\//g, '-');
    const filename = `QEN_Balneare_${stabilimento.replace(/\s+/g, '_')}_${dateStr}.pdf`;
    
    return {
        timestamp: timestamp,
        filename: filename,
        stabilimento: stabilimento,
        comune: comune,
        modulo: modulo,
        qen_score: parseInt(scoreNumber),
        tier: scoreTier,
        vectors: {
            vs: parseInt(vectorVs),
            va: parseInt(vectorVa),
            vt: parseInt(vectorVt)
        },
        analysis: resultText
    };
}

function downloadBlob(blob, filename) {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
    console.log('[PDF] Scaricato:', filename);
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPdfGenerator);
} else {
    initPdfGenerator();
}
