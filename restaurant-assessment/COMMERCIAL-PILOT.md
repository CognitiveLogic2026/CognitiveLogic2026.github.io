# Restaurant Assessment — commercial pilot

Date: 2026-10-09. Status: proposal for review, not deployed.

## Observations and intervention

The supplied Pienissimo screenshots show a concrete opening question about AI visibility, a repeated free-test CTA, a promised immediate result with four scores and a PDF, and a lead form collecting contact details before the result. This is evidence about the presentation only. No test was submitted, PDF inspected or scoring methodology verified. Commercial effectiveness is not established by screenshots.

The Cognitive Logic source already contains 15 questions, five dimension scores, three preliminary priorities, D/O/D/V status and a mailto qualification flow. This change makes the free self-assessment and practical benefits explicit, adds an entry CTA and progress feedback, and retains the existing scoring calculation, questions and internal area names. Area headings use Italian explanations. High scores indicate a more structured declared base; they do not indicate measured economic opportunity. No financial gain, AI visibility or conformity is promised.

A stale-results bug is fixed: operational priority cards are cleared when a repeat submission contains only unknown answers. The result-brand style previously placed after the closing HTML tag is moved to the head.

## Measurement integration: pending

The page dispatches `cognitive-logic:funnel` on `document`. Payload contains only `page`, `version` and `event`, with no form values, scores, URL parameters or identifiers. Event names:

| Event | Trigger | Interpretation |
| --- | --- | --- |
| page_view | Page script loaded | One page load |
| assessment_start | First radio answer changed | Questionnaire started; entry CTA click is not a start |
| assessment_complete | Valid questionnaire submission | Result generated |
| request_prepared | Valid qualification submission, before mailto | Email draft prepared, not sent |

Each event is emitted at most once per page load. There is no cookie, storage, network collector or analytics provider. This is an integration hook, not an operational analytics dashboard. A collector must be configured and verified separately before relying on aggregate conversion counts. Until then, do not report funnel rates. Views may be available from existing server logs, with bots/reloads making these approximate; logs do not capture questionnaire completion.

Received requests and qualified prospects must be counted from actual incoming emails. A prepared email is not a received request. The existing statement that the site does not transmit or store form data remains true. Any future collector must preserve this or update the notice to match actual behavior.

## Pilot: 30 days from deployment

1. Before starting: connect the event listener to the chosen existing analytics system, or document that aggregate funnel measurement remains unavailable. Verify all four events arrive without form content. Record the deployment date as day 1.
2. Use the existing Bologna restaurant outreach queue. Lead with the operational problem: outdated information, difficult reservations or data that do not inform decisions. Link to `/restaurant-assessment/`. No additional product is needed.
3. Log outreach sent, actual replies and actual assessment requests received in the existing prospect register. Mark a prospect qualified only when restaurant identity, a concrete problem and willingness to provide relevant evidence have been confirmed.
4. Review weekly where interest drops. After 30 days, calculate starts/views, completions/starts and prepared requests/completions only if a verified collector exists. Keep received requests and qualified contacts distinct. State denominator and sample size; no invented conversion targets.
5. Change one message at a time. Choose the next intervention based on the weakest observed stage. No guarantee of more customers or revenue.

## Review and deployment

Validation completed in jsdom: original and proposed score, coverage, dimension values and ordered priorities match for all-yes, all-no, all-partial, all-unknown and mixed answers. Required field validation, repeat submissions, current email context and four deduplicated funnel events passed; event payloads contain no personal data. Browser layout validation was not completed because Chromium was unavailable and its download failed. Responsive rules were added, but desktop/mobile visual QA and repository CI remain required before merge.

Target file is already included in `ops/public-static-manifest.txt`; canonical remains `/restaurant-assessment/`. Merge and production deployment are separate from this proposal. After deployment verify the public headline, CTA, all questionnaire answers, results, D/O/D/V and mailto on desktop and mobile. Confirm request emails carry the latest score and priorities. Run the repository's required checks in the full checkout before merge.
