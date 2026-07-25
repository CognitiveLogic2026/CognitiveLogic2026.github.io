"""QEN Bolkestein intelligible scoring contexts — ADR-CLE-004."""


def context_ristorazione(business):
    return (
        "Verticale ristorazione. Dimensioni QEN: inclusione e lavoro, "
        "energia e rifiuti, filiera locale e identità territoriale. "
        "Pesi verticali: VS 0.35, VA 0.35, VT 0.30."
    )


def context_alberghiero(business):
    return (
        "Verticale alberghiero. Dimensioni QEN: accessibilità e lavoro, "
        "efficienza energetica e gestione rifiuti, approvvigionamento locale. "
        "Pesi verticali: VS 0.35, VA 0.35, VT 0.30."
    )


def context_balneare(business):
    return (
        "Verticale balneare. Dimensioni QEN: accessibilità, sicurezza, "
        "gestione ambientale, territorio e filiera locale. "
        "Pesi verticali: VS 0.35, VA 0.35, VT 0.30."
    )


def get_prompt_fn(vertical):
    contexts = {
        "ristorazione": context_ristorazione,
        "alberghiero": context_alberghiero,
        "balneare": context_balneare,
    }
    return contexts.get(str(vertical).lower(), context_ristorazione)
