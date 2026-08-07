import React, { useState } from 'react';
import questionsData from './questions.json';

const DEFAULT_OPTIONS = ['Assente', 'Parziale', 'Adeguato', 'Completo'];
const AREA_WEIGHTS = { A: 0.40, B: 0.35, C: 0.25 };
const AREA_LABELS = { A: 'Semantica', B: 'Processo', C: 'Human Oversight' };

function computeLiveScore(answers, questions) {
  const areaValues = { A: [], B: [], C: [] };
  questions.forEach((q) => {
    const v = answers[q.id];
    if (typeof v === 'number') areaValues[q.area].push(v);
  });
  const areaScore = (vals) => {
    if (!vals.length) return null;
    const avg = vals.reduce((s, v) => s + v, 0) / vals.length;
    return (avg / 3) * 100;
  };
  const a = areaScore(areaValues.A);
  const b = areaScore(areaValues.B);
  const c = areaScore(areaValues.C);
  if (a === null || b === null || c === null) return null;
  const total = a * AREA_WEIGHTS.A + b * AREA_WEIGHTS.B + c * AREA_WEIGHTS.C;
  return { total: Math.round(total * 100) / 100, a, b, c };
}

const QENAssessment = () => {
  const [step, setStep] = useState(0);
  const [sessionId] = useState(() => crypto.randomUUID());
  const [answers, setAnswers] = useState({});
  const [consented, setConsented] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  const questions = questionsData.questions;
  const liveScore = computeLiveScore(answers, questions);
  const allAnswered = questions.every((q) => typeof answers[q.id] === 'number');

  const acceptDisclaimer = async () => {
    setError(null);
    try {
      const res = await fetch('/compliance-audit/wizard/disclaimer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sessionId, consented: true }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(body.error || 'Errore disclaimer');
      setStep(1);
    } catch (e) {
      setError(e.message);
    }
  };

  const setAnswer = (questionId, value) => {
    setAnswers((prev) => ({ ...prev, [questionId]: value }));
  };

  const submitAssessment = async () => {
    setSubmitting(true);
    setError(null);
    try {
      const payload = {
        sessionId,
        answers: questions.map((q) => ({ id: q.id, area: q.area, value: answers[q.id] })),
      };
      const res = await fetch('/compliance-audit/wizard/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || 'Errore invio');
      setResult(body);
      setStep(2);
    } catch (e) {
      setError(e.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="qen-container">
      {error && <div className="qen-error" role="alert">{error}</div>}

      {step === 0 && (
        <div className="qen-step qen-step-disclaimer">
          <h2>Disclaimer QEN</h2>
          <p>
            La logica di questo sistema e ispezionabile: pesi, soglie e formula di calcolo sono
            pubblici. Questo strumento fornisce un pre-assessment orientativo e non sostituisce
            la valutazione legale o una consulenza professionale.
          </p>
          <label className="qen-consent-label">
            <input
              type="checkbox"
              checked={consented}
              onChange={(e) => setConsented(e.target.checked)}
            />
            {' '}Ho letto e acconsento al trattamento dei dati per questa sessione di valutazione.
          </label>
          <button disabled={!consented} onClick={acceptDisclaimer}>
            Inizia
          </button>
        </div>
      )}

      {step === 1 && (
        <div className="qen-step qen-step-questions">
          <h2>Self-Assessment QEN</h2>
          {questions.map((q) => (
            <fieldset key={q.id} className="qen-question">
              <legend>{q.text}</legend>
              {(q.options || DEFAULT_OPTIONS).map((label, idx) => (
                <label key={idx} className="qen-option">
                  <input
                    type="radio"
                    name={`q-${q.id}`}
                    checked={answers[q.id] === idx}
                    onChange={() => setAnswer(q.id, idx)}
                  />
                  {' '}{label}
                </label>
              ))}
            </fieldset>
          ))}

          {liveScore && (
            <div className="qen-live-score">
              <strong>Punteggio provvisorio: {liveScore.total}/100</strong>
              <div className="qen-live-breakdown">
                Area A ({AREA_LABELS.A}): {Math.round(liveScore.a)} &middot;{' '}
                Area B ({AREA_LABELS.B}): {Math.round(liveScore.b)} &middot;{' '}
                Area C ({AREA_LABELS.C}): {Math.round(liveScore.c)}
              </div>
            </div>
          )}

          <button disabled={!allAnswered || submitting} onClick={submitAssessment}>
            {submitting ? 'Invio...' : 'Invia'}
          </button>
        </div>
      )}

      {step === 2 && result && (
        <div className="qen-step qen-step-result">
          <h2>Risultato</h2>
          <p className="qen-final-score">
            QEN Score: <strong>{result.qen_score}/100</strong> &mdash; {result.verdict}
          </p>
          <ul className="qen-area-breakdown">
            <li>Area A ({AREA_LABELS.A}): {result.area_scores.A}</li>
            <li>Area B ({AREA_LABELS.B}): {result.area_scores.B}</li>
            <li>Area C ({AREA_LABELS.C}): {result.area_scores.C}</li>
          </ul>
        </div>
      )}
    </div>
  );
};

export default QENAssessment;
