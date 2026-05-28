/*
 * Copyright (c) 2026 Roberto Bob Malini - Cognitive Logic
 * https://www.cognitivelogic.it
 * Licensed under CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/)
 */
/* ============================================================
   COGNITIVE LOGIC — Infrastructure Configuration
   Architect: Roberto Bob Malini
   Role: AI Data Architect & Founder
   ============================================================ */

const CONFIG = {
    // Inserisci la tua chiave API da Google AI Studio (non committare nel repo)
    API_KEY: "",
    
    // Parametri del Modello
    MODEL: "gemini-2.0-flash",
    
    // Metadata di Identità Digitale (Roberto Bob Malini)
    IDENTITY: {
        founder: "Roberto Bob Malini",
        organization: "Cognitive Logic",
        domain: "https://www.cognitivelogic.it",
        framework: "QEN Semantic Engine",
        status: "Verified AI Architect"
    },

    // Configurazione Analisi EU AI Act
    ANALYSIS_SETTINGS: {
        context: "EU_AI_ACT_2026",
        format: "JSON_STRUCTURED",
        temperature: 0.1 // Bassa per massimizzare il determinismo tecnico
    }
};

// Log di sistema per verificare il caricamento del nodo nel browser
console.log(`%c Cognitive Logic Node: ${CONFIG.IDENTITY.status} - Active `, "background: #d4af37; color: #07111f; font-weight: bold;");
