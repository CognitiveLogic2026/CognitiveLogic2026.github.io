/*
 * Copyright (c) 2026 Roberto Bob Malini - Cognitive Logic
 * https://www.cognitivelogic.it
 * Licensed under CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/)
 */
/**
 * COGNITIVE LOGIC — AI Node Connector (Engine)
 * Gestisce la comunicazione con il Pure Data Node.
 */
async function askGemini(promptText) {
    const API_BASE = "https://api.cognitivelogic.it";

    try {
        const response = await fetch(`${API_BASE}/qen-score`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ description: promptText })
        });

        const data = await response.json();

        if (data.status === "success" && data.qen) {
            const q = data.qen;
            const score = q.qen_score ?? 50;
            const risk_level = score >= 70 ? "LOW" : score >= 40 ? "MEDIUM" : "HIGH";
            return {
                risk_level,
                risk_score: score,
                summary: q.sintesi ?? "",
                decision: q.badge ?? "QEN UNVERIFIED",
                vs: q.vs,
                va: q.va,
                vt: q.vt,
                provider: q.provider
            };
        }
        throw new Error(data.error ?? "Risposta del nodo non valida o incompleta.");

    } catch (e) {
        console.error("Node Failure:", e);
        return {
            risk_level: "HIGH",
            decision: "ERRORE SISTEMA",
            summary: "Il Pure Data Node non ha risposto correttamente.",
            why: e.message
        };
    }
}
