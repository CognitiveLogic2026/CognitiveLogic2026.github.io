const API_URL = "https://api.cognitivelogic.it/analyze";
const PDF_URL = "https://api.cognitivelogic.it/export-pdf";

const inputEl = document.getElementById("chat-input");
const analyzeBtn = document.getElementById("analyze-btn");
const clearBtn = document.getElementById("clear-btn");
const pdfBtn = document.getElementById("pdf-btn");
const statusLine = document.getElementById("status-line");

const decisionBox = document.getElementById("decision-box");
const riskLevelBox = document.getElementById("risk-level");
const riskScoreBox = document.getElementById("risk-score");
const whyBox = document.getElementById("why");
const impactBox = document.getElementById("impact");
const summaryBox = document.getElementById("summary");
const gapsList = document.getElementById("gaps-list");
const recommendationsList = document.getElementById("recommendations-list");
const rawOutput = document.getElementById("raw-output");

function setLoadingState(isLoading) {
  if (analyzeBtn) analyzeBtn.disabled = isLoading;
  if (clearBtn) clearBtn.disabled = isLoading;
  if (pdfBtn) pdfBtn.disabled = isLoading;
}

function clearLists() {
  if (gapsList) gapsList.innerHTML = "";
  if (recommendationsList) recommendationsList.innerHTML = "";
}

function renderList(listEl, items) {
  if (!listEl) return;

  listEl.innerHTML = "";

  if (!items || !Array.isArray(items) || items.length === 0) {
    const li = document.createElement("li");
    li.textContent = "—";
    listEl.appendChild(li);
    return;
  }

  items.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    listEl.appendChild(li);
  });
}

function getDecisionFromRisk(riskLevel) {
  if (riskLevel === "HIGH") {
    return "🔴 CRITICAL — intervento immediato richiesto";
  }
  if (riskLevel === "MEDIUM") {
    return "🟠 ACTION REQUIRED — implementare controlli mancanti";
  }
  if (riskLevel === "LOW") {
    return "🟢 MONITOR — sistema gestibile con controlli base";
  }
  return "—";
}

function getWhyFromData(data) {
  if (data.why) return data.why;

  if (Array.isArray(data.gaps) && data.gaps.length > 0) {
    return `Segnali rilevati: ${data.gaps.join(", ")}.`;
  }

  return "Nessuna motivazione dettagliata restituita dal backend.";
}

function getImpactFromRisk(riskLevel) {
  if (riskLevel === "HIGH") {
    return "Impatto elevato: servono controlli formali, verifica normativa e supervisione immediata.";
  }
  if (riskLevel === "MEDIUM") {
    return "Impatto medio: servono misure di trasparenza, tracciabilità e controllo operativo.";
  }
  if (riskLevel === "LOW") {
    return "Impatto contenuto: sistema monitorabile con controlli base.";
  }
  return "Impatto non disponibile.";
}

function resetOutput() {
  if (decisionBox) decisionBox.textContent = "—";
  if (riskLevelBox) riskLevelBox.textContent = "—";
  if (riskScoreBox) riskScoreBox.textContent = "—";
  if (whyBox) whyBox.textContent = "—";
  if (impactBox) impactBox.textContent = "—";
  if (summaryBox) summaryBox.textContent = "—";
  clearLists();
  if (rawOutput) rawOutput.textContent = "In attesa di risposta backend.";
}

function showLoadingOutput() {
  if (decisionBox) decisionBox.textContent = "Elaborazione...";
  if (riskLevelBox) riskLevelBox.textContent = "...";
  if (riskScoreBox) riskScoreBox.textContent = "...";
  if (whyBox) whyBox.textContent = "Il backend sta elaborando i segnali rilevati.";
  if (impactBox) impactBox.textContent = "Valutazione impatto in corso.";
  if (summaryBox) summaryBox.textContent = "Il backend sta elaborando la richiesta.";
  clearLists();
  if (rawOutput) rawOutput.textContent = "Richiesta inviata al backend...";
}

async function sendMessage() {
  if (!inputEl) {
    console.error("Elemento #chat-input non trovato");
    return;
  }

  const text = inputEl.value.trim();

  if (!text) {
    if (statusLine) statusLine.textContent = "Inserisci una descrizione del sistema AI.";
    inputEl.focus();
    return;
  }

  setLoadingState(true);
  if (statusLine) statusLine.textContent = "Analisi in corso...";
  showLoadingOutput();

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        system: text,
        context: "EU"
      })
    });

    const contentType = response.headers.get("content-type") || "";
    let data;

    if (contentType.includes("application/json")) {
      data = await response.json();
    } else {
      const textResponse = await response.text();
      throw new Error(`Risposta non JSON: ${textResponse}`);
    }

    if (!response.ok) {
      throw new Error(data?.detail || `HTTP ${response.status}`);
    }

    const decision = data.decision || getDecisionFromRisk(data.risk_level);
    const why = getWhyFromData(data);
    const impact = data.impact || getImpactFromRisk(data.risk_level);

    if (decisionBox) decisionBox.textContent = decision;
    if (riskLevelBox) riskLevelBox.textContent = data.risk_level || "—";
    if (riskScoreBox) riskScoreBox.textContent = data.risk_score ?? "—";
    if (whyBox) whyBox.textContent = why;
    if (impactBox) impactBox.textContent = impact;
    if (summaryBox) summaryBox.textContent = data.summary || "—";

    renderList(gapsList, data.gaps);
    renderList(recommendationsList, data.recommendations);

    if (rawOutput) rawOutput.textContent = JSON.stringify(data, null, 2);
    if (statusLine) statusLine.textContent = "Analisi completata.";
  } catch (error) {
    if (decisionBox) decisionBox.textContent = "Errore";
    if (riskLevelBox) riskLevelBox.textContent = "—";
    if (riskScoreBox) riskScoreBox.textContent = "—";
    if (whyBox) whyBox.textContent = "La richiesta non ha ricevuto una risposta valida.";
    if (impactBox) impactBox.textContent = "Verificare endpoint, backend e console.";
    if (summaryBox) summaryBox.textContent = error.message || "Errore sconosciuto.";
    clearLists();
    if (rawOutput) rawOutput.textContent = String(error);
    if (statusLine) statusLine.textContent = `Errore: ${error.message}`;
    console.error("sendMessage error:", error);
  } finally {
    setLoadingState(false);
  }
}

function clearForm() {
  if (!inputEl) return;
  inputEl.value = "";
  resetOutput();
  if (statusLine) statusLine.textContent = "Campi puliti.";
  inputEl.focus();
}

async function exportPdf() {
  if (!inputEl) return;

  const text = inputEl.value.trim();

  if (!text) {
    if (statusLine) statusLine.textContent = "Inserisci una descrizione prima di esportare il PDF.";
    inputEl.focus();
    return;
  }

  setLoadingState(true);
  if (statusLine) statusLine.textContent = "Generazione PDF executive in corso...";

  try {
    const response = await fetch(PDF_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        system: text,
        context: "EU"
      })
    });

    if (!response.ok) {
      const errText = await response.text();
      throw new Error(`Export PDF fallito: ${response.status} ${errText}`);
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "cognitive-logic-executive-report.pdf";
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);

    if (statusLine) statusLine.textContent = "PDF esportato correttamente.";
  } catch (error) {
    if (statusLine) statusLine.textContent = `Errore PDF: ${error.message}`;
    console.error("exportPdf error:", error);
  } finally {
    setLoadingState(false);
  }
}

if (analyzeBtn) analyzeBtn.addEventListener("click", sendMessage);
if (clearBtn) clearBtn.addEventListener("click", clearForm);
if (pdfBtn) pdfBtn.addEventListener("click", exportPdf);

window.sendMessage = sendMessage;

resetOutput();
