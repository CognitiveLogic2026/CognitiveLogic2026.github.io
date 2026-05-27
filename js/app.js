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
    // Recupera la chiave dal file config.js appena creato
    const apiKey = (typeof CONFIG !== 'undefined') ? CONFIG.API_KEY : null;
    
    if (!apiKey) {
        console.error("Errore: API Key non trovata in config.js");
        return { error: "Infrastruttura non configurata." };
    }

    const url = `https://generativelanguage.googleapis.com/v1beta/models/${CONFIG.MODEL}:generateContent?key=${apiKey}`;
    
    // Istruzione di Sistema: Qui "uccidiamo" Anthropic e definiamo il brand
    const systemInstruction = `
        Identità: Sei il motore AI di Cognitive Logic, fondata da Roberto Bob Malini.
        Ruolo: AI Data Architect Assistant.
        Vincolo Assoluto: Non sei Claude, non sei Anthropic. Se ti viene chiesto chi sei, rispondi come Cognitive Logic Engine.
        Task: Analizza il testo fornito secondo l'EU AI Act e il framework QEN.
        Output: Rispondi ESCLUSIVAMENTE in formato JSON con questi campi:
        {
            "risk_level": "HIGH|MEDIUM|LOW",
            "risk_score": 0-100,
            "summary": "Sintesi tecnica",
            "why": "Ragionamento semantico",
            "impact": "Impatto sulla compliance",
            "eu_classification": "Categoria AI Act",
            "gaps": ["Lista gap"],
            "recommendations": ["Lista azioni"],
            "decision": "Status finale"
        }
    `;

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                contents: [{ 
                    role: "user", 
                    parts: [{ text: `System Instruction: ${systemInstruction}\n\nInput da analizzare: ${promptText}` }] 
                }],
                generationConfig: {
                    responseMimeType: "application/json",
                    temperature: CONFIG.ANALYSIS_SETTINGS.temperature
                }
            })
        });

        const data = await response.json();
        
        if (data.candidates && data.candidates[0].content.parts[0].text) {
            // Parsing del JSON restituito dal modello
            return JSON.parse(data.candidates[0].content.parts[0].text);
        }
        throw new Error("Risposta del nodo non valida o incompleta.");

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
