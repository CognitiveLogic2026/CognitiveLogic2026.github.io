/**
 * COGNITIVE LOGIC — UI Controller
 * Gestisce l'interazione tra l'utente e la dashboard QEN.
 */
document.addEventListener('DOMContentLoaded', () => {
    // Selettori (Assicurati che gli ID nel tuo HTML siano questi)
    const inputEl = document.getElementById("chat-input");
    const analyzeBtn = document.getElementById("analyze-btn");
    const statusLine = document.getElementById("status-line");

    // Elementi Dashboard da popolare
    const ui = {
        risk: document.getElementById("risk-level"),
        score: document.getElementById("risk-score"),
        summary: document.getElementById("summary"),
        decision: document.getElementById("decision-box"),
        fill: document.getElementById("risk-fill") // La barra di progresso gialla
    };

    if (!analyzeBtn) {
        console.warn("Bottone 'analyze-btn' non trovato nell'HTML.");
        return;
    }

    analyzeBtn.addEventListener("click", async () => {
        const text = inputEl.value.trim();
        if (!text) {
            if (statusLine) statusLine.textContent = "Inserire una descrizione per l'analisi.";
            return;
        }

        // Stato di caricamento
        analyzeBtn.disabled = true;
        if (statusLine) statusLine.textContent = "Interrogazione nodi semantici in corso...";
        if (ui.decision) ui.decision.textContent = "ELABORAZIONE...";

        // Chiamata alla funzione in app.js
        const result = await askGemini(text);

        // Popolamento dinamico della UI
        if (ui.risk) ui.risk.textContent = result.risk_level;
        if (ui.score) ui.score.textContent = `${result.risk_score}/100`;
        if (ui.summary) ui.summary.textContent = result.summary;
        
        if (ui.decision) {
            ui.decision.textContent = result.decision;
            // Applica la classe colore (es. decision-high nel tuo CSS)
            ui.decision.className = `decision-box decision-${result.risk_level.toLowerCase()}`;
        }

        // Animazione della barra di progresso (CSS transition)
        if (ui.fill) {
            ui.fill.style.width = `${result.risk_score}%`;
        }

        // Reset UI
        analyzeBtn.disabled = false;
        if (statusLine) statusLine.textContent = "Analisi completata. Nodo attivo.";
    });
});
