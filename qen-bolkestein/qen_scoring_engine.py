# Copyright (c) 2026 Roberto Bob Malini - Cognitive Logic
# https://www.cognitivelogic.it
# Licensed under CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/)
def prompt_ristorazione(b):
    return f"""Analizza: {b['name']}, {b['city']}. Restituisci JSON: {{"vs_score": 0-100, "va_score": 0-100, "vt_score": 0-100, "qen_score": media_pesata, "confidence": 0.0-1.0}}. Criteri VS: ISO, CCNL, HR. VA: energia, rifiuti, cert. VT: filiera locale. Pesi: 0.35, 0.35, 0.30"""

def prompt_alberghiero(b):
    return f"""QEN Hotel: {b['name']}, {b['city']}. JSON: {{"vs_score": 0-100, "va_score": 0-100, "vt_score": 0-100, "qen_score": media, "confidence": 0.0-1.0}}. VS: cert, CCNL. VA: energia, rifiuti. VT: supply chain locale. Pesi: 0.35, 0.35, 0.30"""

def prompt_balneare(b):
    return f"""QEN Stabilimento: {b['name']}, {b['city']}. JSON: {{"vs_score": 0-100, "va_score": 0-100, "vt_score": 0-100, "qen_score": media, "confidence": 0.0-1.0}}. VS: cert. VA: energia. VT: filiera. Pesi: 0.35, 0.35, 0.30"""

def get_prompt_fn(vertical):
    m = {"ristorazione": prompt_ristorazione, "alberghiero": prompt_alberghiero, "balneare": prompt_balneare}
    return m.get(vertical.lower(), prompt_ristorazione)
