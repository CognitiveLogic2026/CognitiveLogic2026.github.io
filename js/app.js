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
  analyzeBtn.disabled = isLoading;
  clearBtn.disabled = isLoading;
  pdfBtn.disabled = isLoading;
}

function clearLists() {
  gapsList.innerHTML = "";
  recommendationsList.innerHTML = "";
}

function renderList(listEl, items) {
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

function resetOutput() {
  decisionBox.textContent = "—";
  riskLevelBox.textContent = "—";
  riskScoreBox.textContent = "—";
  whyBox.textContent = "—";
  impactBox.textContent = "—";
  summaryBox.textContent = "—";
  clearLists();
  rawOutput.textContent = "In attesa di risposta backend.";
}

function showLoadingOutput() {
  decisionBox.textContent = "Elaborazione...";
  riskLevelBox.textContent = "...";
  riskScoreBox.textContent = "...";
  whyBox.textContent = "Il backend sta elaborando i segnali rilevati.";
  impactBox.textContent = "Valutazione impatto in corso.";
  summaryBox.textContent = "Il backend sta elaborando la richiesta.";
  clearLists();
  rawOutput.textContent = "Richiesta inviata al backend...";
}

async function sendMessage() {
  const text = inputEl.value.trim();

  if (!text) {
    statusLine.textContent = "Inserisci una descrizione del sistema AI.";
    inputEl.focus();
    return;
  }

  setLoadingState(true);
  statusLine.textContent = "Analisi in corso...";
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

    decisionBox.textContent = data.decision || "—";
    riskLevelBox.textContent = data.risk_level || "—";
    riskScoreBox.textContent = data.risk_score ?? "—";
    whyBox.textContent = data.why || "—";
    impactBox.textContent = data.impact || "—";
    summaryBox.textContent = data.summary || "—";

    renderList(gapsList, data.gaps);
    renderList(recommendationsList, data.recommendations);

    rawOutput.textContent = JSON.stringify(data, null, 2);
    statusLine.textContent = "Analisi completata.";
  } catch (error) {
    decisionBox.textContent = "Errore";
    riskLevelBox.textContent = "—";
    riskScoreBox.textContent = "—";
    whyBox.textContent = "La richiesta non ha ricevuto una risposta valida.";
    impactBox.textContent = "Verificare endpoint, backend e console.";
    summaryBox.textContent = error.message || "Errore sconosciuto.";
    clearLists();
    rawOutput.textContent = String(error);
    statusLine.textContent = `Errore: ${error.message}`;
  } finally {
    setLoadingState(false);
  }
}

function clearForm() {
  inputEl.value = "";
  resetOutput();
  statusLine.textContent = "Campi puliti.";
  inputEl.focus();
}

async function exportPdf() {
  const text = inputEl.value.trim();

  if (!text) {
    statusLine.textContent = "Inserisci una descrizione prima di esportare il PDF.";
    inputEl.focus();
    return;
  }

  setLoadingState(true);
  statusLine.textContent = "Generazione PDF executive in corso...";

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

    statusLine.textContent = "PDF esportato correttamente.";
  } catch (error) {
    statusLine.textContent = `Errore PDF: ${error.message}`;
  } finally {
    setLoadingState(false);
  }
}

analyzeBtn.addEventListener("click", sendMessage);
clearBtn.addEventListener("click", clearForm);
pdfBtn.addEventListener("click", exportPdf);

window.sendMessage = sendMessage;

resetOutput();
