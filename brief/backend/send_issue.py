from __future__ import annotations

import argparse
import html
import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlencode

import requests

from .issue_deliveries import (
    create_issue_delivery,
    update_issue_delivery,
)
from .resend_sender import (
    DEFAULT_PUBLIC_BASE_URL,
    RESEND_API_URL,
    _required_env,
)
from .subscribers import update_delivery_status


@dataclass(frozen=True)
class IssueContent:
    slug: str
    subject: str
    preview: str
    canonical_url: str


NUMBER_ZERO = IssueContent(
    slug="numero-zero",
    subject=(
        "Cognitive Logic Brief #0 — "
        "Non tutto ciò che cambia merita una decisione"
    ),
    preview=(
        "Quattro segnali su evidenze, agenti AI, "
        "concessioni e filiere."
    ),
    canonical_url=(
        "https://cognitivelogic.it/brief/numero-zero/"
    ),
)


BRIEF_ONE = IssueContent(
    slug="dal-dato-alla-decisione",
    subject=(
        "Cognitive Logic Brief #1 — "
        "Dal dato alla decisione"
    ),
    preview=(
        "Quando un’informazione diventa evidenza: "
        "tre casi e una verifica operativa."
    ),
    canonical_url=(
        "https://cognitivelogic.it/brief/"
        "dal-dato-alla-decisione/"
    ),
)


def build_unsubscribe_url(token: str) -> str:
    base_url = os.getenv(
        "BRIEF_PUBLIC_BASE_URL",
        DEFAULT_PUBLIC_BASE_URL,
    ).rstrip("/")

    return (
        f"{base_url}/brief/unsubscribe?"
        + urlencode({"token": token})
    )


def render_number_zero(
    unsubscribe_url: str,
    *,
    test: bool = False,
) -> tuple[str, str, str]:
    subject = NUMBER_ZERO.subject
    if test:
        subject = f"[TEST] {subject}"

    preview = NUMBER_ZERO.preview
    canonical = NUMBER_ZERO.canonical_url
    safe_unsubscribe = html.escape(
        unsubscribe_url,
        quote=True,
    )

    text = f"""Cognitive Logic Brief — Numero Zero

Non tutto ciò che cambia merita una decisione

{preview}

LA LENTE
Avere il dato non significa poter decidere.

Quando i dati sostengono raccomandazioni o decisioni,
occorre sapere quali evidenze hanno sostenuto il risultato,
se possono essere contestate e se la decisione sarà
ricostruibile.

Approfondisci:
https://cognitivelogic.it/research/data-governance-evidence-governance/

IL CASO
Quando un agente agisce, chi può ancora dire no?

La presenza di una persona nel processo non dimostra che
conservi un'autorità effettiva. Occorre correlare evento,
evidenza, soglia di materialità, autorità e decision record.

Caso verificato:
https://cognitivelogic.it/international-watch/distributed-ai-agent-incidents-governance/

TERRITORI E DECISIONI PUBBLICHE
Una gara comincia prima del bando.

Investimenti, valore della concessione, indennizzo,
criteri e caratteristiche del territorio richiedono
evidenze organizzate prima della procedura.

Quadro verificato:
https://cognitivelogic.it/international-watch/concessioni-balneari-consiglio-stato-6539-2026/

DAL VERTICALE
Il caldo non finisce quando termina l'emergenza.

Per la ristorazione un'anomalia climatica diventa
disponibilità, qualità, provenienza, prezzo e menu.

Leggi su FuoriMenù:
https://fuorimenu.substack.com/p/il-caldo-non-finisce-nei-campi-cosa

UNA DOMANDA DA PORTARE CON SÉ
Se questa informazione fosse sbagliata, sapremmo
accorgercene prima che diventi una decisione?

Leggi il Numero Zero:
{canonical}

Disiscriviti:
{unsubscribe_url}

Cognitive Logic
Data must be intelligible.
"""

    html_body = f"""<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width">
<title>{html.escape(subject)}</title>
</head>
<body style="margin:0;background:#071015;color:#edf5f5;
font-family:Arial,Helvetica,sans-serif;">
<div style="display:none;max-height:0;overflow:hidden;
opacity:0;color:transparent;">
{html.escape(preview)}
</div>

<table role="presentation" width="100%" cellspacing="0"
cellpadding="0" border="0" style="background:#071015;">
<tr>
<td align="center" style="padding:32px 16px;">

<table role="presentation" width="100%" cellspacing="0"
cellpadding="0" border="0"
style="max-width:680px;background:#0b1720;
border:1px solid #233744;">

<tr>
<td style="padding:38px 34px 28px;">
<p style="margin:0 0 18px;color:#9fcbd4;
font-size:12px;letter-spacing:2px;text-transform:uppercase;">
Cognitive Logic Brief · Numero Zero
</p>

<h1 style="margin:0;color:#ffffff;font-family:Georgia,serif;
font-size:42px;line-height:1.08;font-weight:normal;">
Non tutto ciò che cambia merita una decisione
</h1>

<p style="margin:24px 0 0;color:#b8c5cb;
font-size:18px;line-height:1.65;">
Quattro segnali per capire quando un cambiamento modifica
davvero evidenze, responsabilità e decisioni.
</p>
</td>
</tr>

<tr>
<td style="padding:0 34px 30px;">
<img
src="https://cognitivelogic.it/img/og/cognitive-logic-brief-numero-zero.png"
width="612"
alt="Cognitive Logic Brief Numero Zero"
style="display:block;width:100%;height:auto;border:0;">
</td>
</tr>

<tr>
<td style="padding:8px 34px 38px;color:#d7e0e3;
font-size:16px;line-height:1.75;">

<p>
Ogni giorno arrivano nuovi dati, norme, incidenti,
strumenti e previsioni. Il problema non è trovarne altri:
è capire quali cambiano realmente una decisione.
</p>

<h2 style="margin:42px 0 8px;color:#9fcbd4;
font-size:12px;letter-spacing:2px;text-transform:uppercase;">
01 · La lente
</h2>
<h3 style="margin:0 0 14px;color:#ffffff;
font-family:Georgia,serif;font-size:27px;font-weight:normal;">
Avere il dato non significa poter decidere
</h3>
<p>
Quando i dati sostengono raccomandazioni o decisioni,
occorre sapere quali evidenze hanno sostenuto il risultato,
se possono essere contestate e se la decisione sarà
ricostruibile.
</p>
<p>
<a href="https://cognitivelogic.it/research/data-governance-evidence-governance/"
style="color:#a9dce5;">
Approfondisci l’Evidence Governance →
</a>
</p>

<h2 style="margin:42px 0 8px;color:#9fcbd4;
font-size:12px;letter-spacing:2px;text-transform:uppercase;">
02 · Il caso
</h2>
<h3 style="margin:0 0 14px;color:#ffffff;
font-family:Georgia,serif;font-size:27px;font-weight:normal;">
Quando un agente agisce, chi può ancora dire no?
</h3>
<p>
La presenza di una persona nel processo non dimostra che
conservi un’autorità effettiva. Occorre correlare evento,
evidenza, soglia di materialità, autorità e decision record.
</p>
<p>
<a href="https://cognitivelogic.it/international-watch/distributed-ai-agent-incidents-governance/"
style="color:#a9dce5;">
Consulta il caso verificato →
</a>
</p>

<h2 style="margin:42px 0 8px;color:#9fcbd4;
font-size:12px;letter-spacing:2px;text-transform:uppercase;">
03 · Territori
</h2>
<h3 style="margin:0 0 14px;color:#ffffff;
font-family:Georgia,serif;font-size:27px;font-weight:normal;">
Una gara comincia prima del bando
</h3>
<p>
Investimenti, valore della concessione, indennizzo,
criteri e caratteristiche del territorio richiedono
evidenze organizzate prima della procedura.
</p>
<p>
<a href="https://cognitivelogic.it/international-watch/concessioni-balneari-consiglio-stato-6539-2026/"
style="color:#a9dce5;">
Verifica il quadro sulla sentenza 6539/2026 →
</a>
</p>

<h2 style="margin:42px 0 8px;color:#9fcbd4;
font-size:12px;letter-spacing:2px;text-transform:uppercase;">
04 · Dal verticale
</h2>
<h3 style="margin:0 0 14px;color:#ffffff;
font-family:Georgia,serif;font-size:27px;font-weight:normal;">
Il caldo non finisce quando termina l’emergenza
</h3>
<p>
Per la ristorazione un’anomalia climatica diventa
disponibilità, qualità, provenienza, prezzo e menu.
</p>
<p>
<a href="https://fuorimenu.substack.com/p/il-caldo-non-finisce-nei-campi-cosa"
style="color:#a9dce5;">
Leggi il caso completo su FuoriMenù →
</a>
</p>

<table role="presentation" width="100%" cellspacing="0"
cellpadding="0" border="0"
style="margin-top:42px;border:1px solid #34505f;">
<tr>
<td style="padding:24px;">
<p style="margin:0 0 10px;color:#9fcbd4;
font-size:12px;letter-spacing:2px;text-transform:uppercase;">
Una domanda da portare con sé
</p>
<p style="margin:0;color:#ffffff;font-family:Georgia,serif;
font-size:24px;line-height:1.45;">
Se questa informazione fosse sbagliata, sapremmo
accorgercene prima che diventi una decisione?
</p>
</td>
</tr>
</table>

<p style="margin:38px 0 0;text-align:center;">
<a href="{canonical}"
style="display:inline-block;padding:14px 22px;
background:#dceef1;color:#071015;text-decoration:none;
font-weight:bold;">
Leggi il Numero Zero
</a>
</p>
</td>
</tr>

<tr>
<td style="padding:28px 34px;border-top:1px solid #233744;
color:#85969e;font-size:12px;line-height:1.7;">
Cognitive Logic · Data must be intelligible.<br>
Ricevi questa email perché hai confermato l’iscrizione
a Cognitive Logic Brief.<br>
<a href="{safe_unsubscribe}" style="color:#a9c5cc;">
Disiscriviti
</a>
</td>
</tr>

</table>
</td>
</tr>
</table>
</body>
</html>
"""

    return subject, text, html_body



def render_brief_one(
    unsubscribe_url: str,
    *,
    test: bool = False,
) -> tuple[str, str, str]:
    subject = BRIEF_ONE.subject
    if test:
        subject = f"[TEST] {subject}"

    preview = BRIEF_ONE.preview
    canonical = BRIEF_ONE.canonical_url
    safe_unsubscribe = html.escape(
        unsubscribe_url,
        quote=True,
    )

    text = f"""Cognitive Logic Brief — #1

Dal dato alla decisione: quando un’informazione diventa evidenza

{preview}

Un dato può essere corretto. Una fonte può essere autorevole.
Ma la decisione successiva è davvero ricostruibile?

01 · DAL DATO AL CLAIM

Il 53,7% rilevato da ISTAT può essere corretto nel perimetro
della rilevazione. Quando diventa un claim sulla "circolarità"
delle aziende agricole, però, occorre ricostruire:

fonte → metodo → dato → interpretazione → claim

02 · DALLA RACCOMANDAZIONE ALL'AZIONE

In fabbrica una raccomandazione AI può influenzare una decisione
operativa. Non basta valutarne la qualità predittiva: servono dati,
controlli, autorità umana e responsabilità ricostruibili.

03 · EVIDENZA E DECISIONE PUBBLICA

Nelle procedure sulle concessioni demaniali, una valutazione
economica può entrare direttamente nella costruzione della
decisione amministrativa. Provenienza, metodo e responsabilità
diventano quindi parte dell'evidenza.

LA DOMANDA

Su quali basi abbiamo deciso?

STRUMENTO OPERATIVO

12 domande per capire se un'organizzazione governa davvero l'AI:
https://cognitivelogic.it/resources/documents/12-domande-governance-ai/

Leggi Cognitive Logic Brief #1:
{canonical}

Disiscriviti:
{unsubscribe_url}

Cognitive Logic
Data must be intelligible.
"""

    html_body = f"""<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width">
<title>{html.escape(subject)}</title>
</head>

<body style="margin:0;background:#071015;color:#edf5f5;
font-family:Arial,Helvetica,sans-serif;">

<div style="display:none;max-height:0;overflow:hidden;
opacity:0;color:transparent;">
{html.escape(preview)}
</div>

<table role="presentation" width="100%" cellspacing="0"
cellpadding="0" border="0" style="background:#071015;">
<tr>
<td align="center" style="padding:32px 16px;">

<table role="presentation" width="100%" cellspacing="0"
cellpadding="0" border="0"
style="max-width:680px;background:#0b1720;
border:1px solid #233744;">

<tr>
<td style="padding:38px 34px 28px;">

<p style="margin:0 0 18px;color:#9fcbd4;
font-size:12px;letter-spacing:2px;text-transform:uppercase;">
Cognitive Logic Brief · #1
</p>

<h1 style="margin:0;color:#ffffff;font-family:Georgia,serif;
font-size:42px;line-height:1.08;font-weight:normal;">
Dal dato alla decisione
</h1>

<p style="margin:18px 0 0;color:#ffffff;
font-family:Georgia,serif;font-size:26px;line-height:1.35;">
Quando un’informazione diventa evidenza
</p>

<p style="margin:24px 0 0;color:#b8c5cb;
font-size:18px;line-height:1.65;">
Tre settori diversi mostrano lo stesso problema:
possiamo ricostruire la catena che porta
dall’informazione alla decisione?
</p>

</td>
</tr>

<tr>
<td style="padding:0 34px 30px;">

<img
src="https://cognitivelogic.it/img/og/cognitive-logic-brief-1-dal-dato-alla-decisione.png"
width="612"
alt="Cognitive Logic Brief #1 — Dal dato alla decisione"
style="display:block;width:100%;height:auto;border:0;">

</td>
</tr>

<tr>
<td style="padding:8px 34px 38px;color:#d7e0e3;
font-size:16px;line-height:1.75;">

<p>
Un dato può essere corretto. Una fonte può essere autorevole.
Una procedura può essere documentata. Ma nessuna di queste
condizioni garantisce, da sola, che la decisione successiva
sia verificabile.
</p>

<h2 style="margin:42px 0 8px;color:#9fcbd4;
font-size:12px;letter-spacing:2px;text-transform:uppercase;">
01 · Dal dato al claim
</h2>

<h3 style="margin:0 0 14px;color:#ffffff;
font-family:Georgia,serif;font-size:27px;font-weight:normal;">
Quando il dato non coincide con ciò che affermiamo
</h3>

<p>
Il 53,7% rilevato da ISTAT può essere corretto nel perimetro
della rilevazione. Quando diventa un claim sulla “circolarità”
delle aziende agricole, occorre ricostruire fonte, metodo,
dato, interpretazione e affermazione finale.
</p>

<h2 style="margin:42px 0 8px;color:#9fcbd4;
font-size:12px;letter-spacing:2px;text-transform:uppercase;">
02 · Dalla raccomandazione all’azione
</h2>

<h3 style="margin:0 0 14px;color:#ffffff;
font-family:Georgia,serif;font-size:27px;font-weight:normal;">
Quando l’AI entra nella decisione industriale
</h3>

<p>
Una raccomandazione AI può influenzare una decisione operativa.
Non basta valutarne la qualità predittiva: occorre sapere quali
dati siano stati usati, quali controlli siano intervenuti e chi
conservi l’autorità di confermare, modificare o interrompere
l’azione.
</p>

<h2 style="margin:42px 0 8px;color:#9fcbd4;
font-size:12px;letter-spacing:2px;text-transform:uppercase;">
03 · Evidenza e decisione pubblica
</h2>

<h3 style="margin:0 0 14px;color:#ffffff;
font-family:Georgia,serif;font-size:27px;font-weight:normal;">
Quando l’evidenza entra nella procedura amministrativa
</h3>

<p>
Nelle procedure relative alle concessioni demaniali una
valutazione economica può entrare direttamente nella costruzione
della decisione amministrativa. Provenienza, metodo e
responsabilità diventano quindi parte dell’evidenza.
</p>

<table role="presentation" width="100%" cellspacing="0"
cellpadding="0" border="0"
style="margin-top:42px;border:1px solid #34505f;">
<tr>
<td style="padding:24px;">

<p style="margin:0 0 10px;color:#9fcbd4;
font-size:12px;letter-spacing:2px;text-transform:uppercase;">
Una domanda da portare con sé
</p>

<p style="margin:0;color:#ffffff;font-family:Georgia,serif;
font-size:27px;line-height:1.4;">
Su quali basi abbiamo deciso?
</p>

</td>
</tr>
</table>

<h2 style="margin:42px 0 8px;color:#9fcbd4;
font-size:12px;letter-spacing:2px;text-transform:uppercase;">
Strumento operativo
</h2>

<h3 style="margin:0 0 14px;color:#ffffff;
font-family:Georgia,serif;font-size:27px;font-weight:normal;">
12 domande per capire se un’organizzazione governa davvero l’AI
</h3>

<p>
Una checklist per verificare responsabilità, dati, controlli,
evidenze, tracciabilità e autorità umana.
</p>

<p>
<a
href="https://cognitivelogic.it/resources/documents/12-domande-governance-ai/"
style="color:#a9dce5;">
Apri la checklist →
</a>
</p>

<p style="margin:42px 0 0;text-align:center;">

<a href="{canonical}"
style="display:inline-block;padding:14px 22px;
background:#dceef1;color:#071015;text-decoration:none;
font-weight:bold;">
Leggi Cognitive Logic Brief #1
</a>

</p>

</td>
</tr>

<tr>
<td style="padding:28px 34px;border-top:1px solid #233744;
color:#85969e;font-size:12px;line-height:1.7;">

Cognitive Logic · Data must be intelligible.<br>
Ricevi questa email perché hai confermato l’iscrizione
a Cognitive Logic Brief.<br>

<a href="{safe_unsubscribe}" style="color:#a9c5cc;">
Disiscriviti
</a>

</td>
</tr>

</table>
</td>
</tr>
</table>

</body>
</html>
"""

    return subject, text, html_body


def send_issue(
    email: str,
    issue: IssueContent,
    renderer,
    *,
    test: bool,
    db_path: Path | None = None,
) -> str:
    issue_slug = (
        f"{issue.slug}-test"
        if test
        else issue.slug
    )

    delivery = create_issue_delivery(
        email,
        issue_slug,
        db_path=db_path,
    )

    unsubscribe_url = build_unsubscribe_url(
        delivery.unsubscribe_token
    )

    subject, text, html_body = renderer(
        unsubscribe_url,
        test=test,
    )

    payload = {
        "from": _required_env("BRIEF_FROM_EMAIL"),
        "to": [delivery.email],
        "subject": subject,
        "text": text,
        "html": html_body,
        "headers": {
            "List-Unsubscribe": f"<{unsubscribe_url}>",
            "List-Unsubscribe-Post": (
                "List-Unsubscribe=One-Click"
            ),
        },
        "tags": [
            {"name": "publication", "value": "brief"},
            {"name": "issue", "value": issue_slug},
        ],
    }

    try:
        response = requests.post(
            RESEND_API_URL,
            headers={
                "Authorization": (
                    f"Bearer {_required_env('RESEND_API_KEY')}"
                ),
                "Content-Type": "application/json",
                "Idempotency-Key": (
                    f"brief-{issue_slug}-{delivery.id}"
                ),
            },
            json=payload,
            timeout=15,
        )

        if not 200 <= response.status_code < 300:
            raise RuntimeError(
                "Resend delivery failed with HTTP "
                f"{response.status_code}"
            )

        response_data = response.json()
        resend_email_id = str(
            response_data.get("id") or ""
        ).strip()

        if not resend_email_id:
            raise RuntimeError(
                "Resend response has no email id"
            )

        update_issue_delivery(
            delivery.id,
            "sent",
            resend_email_id=resend_email_id,
            db_path=db_path,
        )

        update_delivery_status(
            delivery.email,
            "sent",
            db_path=db_path,
        )

        return resend_email_id

    except Exception as exc:
        try:
            update_issue_delivery(
                delivery.id,
                "failed",
                error=str(exc),
                db_path=db_path,
            )
        except Exception:
            pass
        raise


def send_number_zero(
    email: str,
    *,
    test: bool,
    db_path: Path | None = None,
) -> str:
    return send_issue(
        email,
        NUMBER_ZERO,
        render_number_zero,
        test=test,
        db_path=db_path,
    )


def send_brief_one(
    email: str,
    *,
    test: bool,
    db_path: Path | None = None,
) -> str:
    return send_issue(
        email,
        BRIEF_ONE,
        render_brief_one,
        test=test,
        db_path=db_path,
    )



def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Preview or send one Cognitive Logic Brief issue "
            "to one explicit active subscriber."
        )
    )

    parser.add_argument("--email", required=True)
    parser.add_argument(
        "--issue",
        choices=("numero-zero", "brief-1"),
        default="numero-zero",
        help=(
            "Issue to preview or send. "
            "Default: numero-zero."
        ),
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Use a test issue identifier and [TEST] subject.",
    )
    parser.add_argument(
        "--confirm-send",
        action="store_true",
        help="Actually send. Without this flag only preview.",
    )

    args = parser.parse_args()

    if args.issue == "brief-1":
        renderer = render_brief_one
        sender = send_brief_one
    else:
        renderer = render_number_zero
        sender = send_number_zero

    if not args.confirm_send:
        subject, text, html_body = renderer(
            "https://cognitivelogic.it/brief/unsubscribe"
            "?token=PREVIEW_ONLY",
            test=args.test,
        )

        print("MODE: PREVIEW")
        print("ISSUE:", args.issue)
        print("RECIPIENT:", args.email)
        print("SUBJECT:", subject)
        print("TEXT LENGTH:", len(text))
        print("HTML LENGTH:", len(html_body))
        print("NO EMAIL SENT")
        return 0

    resend_email_id = sender(
        args.email,
        test=args.test,
    )

    print("MODE: SENT")
    print("ISSUE:", args.issue)
    print("RECIPIENT:", args.email)
    print("RESEND EMAIL ID:", resend_email_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
