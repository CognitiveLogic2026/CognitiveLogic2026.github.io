#!/usr/bin/env python3
"""Read-only deterministic cross-record validator for QEN International Watch."""
import argparse, json, re, sys
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker, RefResolver

ROOT=Path(__file__).resolve().parents[1]; SD=ROOT/'schemas/international-watch'
SCHEMAS={'event-registry':'event-registry','claim-registry':'claim-registry','source-registry':'international-watch-source-registry','evidence-ledger':'evidence-ledger','source-dependency':'source-dependency','narrative-comparison':'narrative-comparison','epistemic-assessment':'epistemic-assessment','contradictions':'contradiction','workflow':'workflow'}
FORBIDDEN={'truth_score','trust_score','truth_percentage','confidence_percentage','probability_of_truth'}
ID_RE=re.compile(r'^IW-\d{3}(?:-(?:E|S)\d{3}|-(?:CLM|SRC|EVD|ASM|DEP|CON|NAR|WF)-\d{3})?$')
ALLOWED_STATES={'ACCERTATO','FORTEMENTE_CORROBORATO','PLAUSIBILE','CONTESTATO','NON_VERIFICATO','CONTRADDETTO','INDETERMINABILE'}
SCHEMA_VERSION='1.0.0'
TRANS={None:{'draft'},'draft':{'in_review'},'in_review':{'draft','approved'},'approved':{'in_review','published'},'published':{'superseded','withdrawn'},'superseded':set(),'withdrawn':set()}
def load(p): return json.loads(p.read_text(encoding='utf-8'))
def walk(v):
 if isinstance(v,dict):
  for k,x in v.items(): yield k,x; yield from walk(x)
 elif isinstance(v,list):
  for x in v: yield from walk(x)
def main(argv=None):
 ap=argparse.ArgumentParser(); ap.add_argument('--case',default='IW-001'); ap.add_argument('--path',type=Path); a=ap.parse_args(argv)
 base=a.path or ROOT/'data/international-watch/cases'/a.case; errors=[]; warnings=[]; bundles={}
 def err(code,msg): errors.append(f'{code}: {msg}')
 def warn(code,msg): warnings.append(f'{code}: {msg}')
 common=load(SD/'common.schema.json'); store={common['$id']:common,'common.schema.json':common}
 for filename,schema_name in SCHEMAS.items():
  p=base/f'{filename}.json'
  if not p.exists(): err('FILE_MISSING',str(p)); continue
  try: b=load(p); bundles[filename]=b.get('records',[])
  except Exception as e: err('JSON_INVALID',f'{p}: {e}'); continue
  schema=load(SD/f'{schema_name}.schema.json'); Draft202012Validator.check_schema(schema)
  v=Draft202012Validator(schema,resolver=RefResolver.from_schema(schema,store=store),format_checker=FormatChecker())
  for i,r in enumerate(bundles[filename]):
   for e in sorted(v.iter_errors(r),key=lambda x:list(x.path)): err('SCHEMA',f'{filename}[{i}] {e.message}')
 manifest=base/'dossier-manifest.json'
 if not manifest.exists(): err('FILE_MISSING',str(manifest))
 else:
  m=load(manifest)
  for f in m.get('files',[]):
   if not (base/f).exists(): err('FILE_REF',f'{f} does not exist')
 all_records=[r for rs in bundles.values() for r in rs]; ids={}
 for r in all_records:
  i=r.get('id')
  if i in ids: err('DUPLICATE_ID',i)
  ids[i]=r
  if not i or not ID_RE.match(i): err('ID_FORMAT',str(i))
  if r.get('schema_version')!=SCHEMA_VERSION: err('VERSION',f'{i} schema_version')
  if r.get('status')=='published': err('PUBLICATION_GATE',f'{i} pilot cannot be published')
  for k,_ in walk(r):
   if k in FORBIDDEN: err('FORBIDDEN_FIELD',f'{i}.{k}')
 events={r['event_id']:r for r in bundles.get('event-registry',[])}; sources={r['source_id']:r for r in bundles.get('source-registry',[])}; evs={r['evidence_id']:r for r in bundles.get('evidence-ledger',[])}; asms={r['assessment_id']:r for r in bundles.get('epistemic-assessment',[])}; deps={r['edge_id']:r for r in bundles.get('source-dependency',[])}; claims={r['claim_id']:r for r in bundles.get('claim-registry',[])}
 for c in claims.values():
  for key,table in [('event_id',events),('origin_source_id',sources),('assessment_id',asms)]:
   if c.get(key) not in table: err('BROKEN_REF',f"{c['claim_id']}.{key}={c.get(key)}")
  if not c.get('origin_source_id'): err('CLAIM_ORIGIN',c['claim_id'])
  for x in c.get('evidence_refs',[]):
   if x not in evs: err('BROKEN_REF',f'{c["claim_id"]}.evidence={x}')
  for x in c.get('counter_evidence_refs',[]):
   if x not in evs: err('BROKEN_REF',f'{c["claim_id"]}.counter={x}')
  for x in c.get('dependency_refs',[]):
   if x not in deps: err('BROKEN_REF',f'{c["claim_id"]}.dependency={x}')
  if not c.get('temporal_scope') or not c.get('as_of') or not c.get('geographic_scope'): err('SCOPE',c['claim_id'])
  if c.get('translation_method')!='none' and not c.get('translation'): err('TRANSLATION',c['claim_id'])
  if not c.get('revision_triggers'): err('REVISION_TRIGGERS',c['claim_id'])
  if not c.get('counter_evidence_refs') and not c.get('counter_evidence_absence_reason'): err('COUNTER_EVIDENCE_REASON',c['claim_id'])
 for e in evs.values():
  if not e.get('does_not_establish'): err('DOES_NOT_ESTABLISH',e['evidence_id'])
  for x in e.get('supports',[])+e.get('contradicts',[]):
   if x not in claims: err('BROKEN_REF',f'{e["evidence_id"]}->{x}')
  if e.get('archived_uri') and not e.get('content_hash'): err('HASH_REQUIRED',e['evidence_id'])
  if not e.get('archived_uri') and not e.get('archived_unavailability_reason'): err('ARCHIVE_REASON',e['evidence_id'])
 for s in sources.values():
  if not s.get('archived_capture') and not s.get('archived_unavailability_reason'): err('ARCHIVE_REASON',s['source_id'])
  if not s.get('accessed_at'): err('SOURCE_ACCESS_TIME',s['source_id'])
 for x in deps.values():
  if x.get('from') not in ids or x.get('to') not in ids: err('BROKEN_REF',f'{x["edge_id"]} from/to')
  if (x.get('republication_or_translation') or x.get('unknown_dependency') or x.get('evidence_collection_independent')!='yes') and x.get('counts_as_independent_corroboration'): err('FALSE_INDEPENDENCE',x['edge_id'])
 graph={x['from']:x['to'] for x in deps.values() if x.get('edge_type') in {'derived_from','republication','translation','summary','repeats'}}
 for start in graph:
  seen=set(); cur=start
  while cur in graph:
   if cur in seen: err('DEPENDENCY_CYCLE',start); break
   seen.add(cur); cur=graph[cur]
 for x in asms.values():
  if x.get('claim_id') not in claims: err('BROKEN_REF',f'{x["assessment_id"]}.claim')
  if x.get('state') not in ALLOWED_STATES: err('EPISTEMIC_STATE',x['assessment_id'])
  if not x.get('unknowns') or not x.get('limits'): err('ASSESSMENT_LIMITS',x['assessment_id'])
  if x.get('state') in {'CONTESTATO','CONTRADDETTO','INDETERMINABILE'} and not x.get('reasoning_summary'): err('ASSESSMENT_REASON',x['assessment_id'])
  if not x.get('contrary_evidence') and not any('counter' in z.lower() or 'attribution' in z.lower() for z in x.get('unknowns',[])): warn('COUNTER_EVIDENCE',f'{x["assessment_id"]}: absence explained only by general unknowns')
  if x.get('status')=='approved' and (not x.get('reviewer') or 'pending' in x.get('reviewer','').lower()): err('HUMAN_REVIEWER',x['assessment_id'])
 for w in bundles.get('workflow',[]):
  if w.get('publication_automatic') is not False: err('AUTO_PUBLICATION',w['workflow_id'])
  prev=None
  for h in w.get('history',[]):
   if h.get('from')!=prev or h.get('to') not in TRANS.get(prev,set()): err('WORKFLOW_TRANSITION',f"{w['workflow_id']} {h.get('from')}->{h.get('to')}")
   prev=h.get('to')
  if prev!=w.get('current_state'): err('WORKFLOW_STATE',w['workflow_id'])
 print(f'International Watch validation: {base}')
 for x in errors: print('ERROR',x)
 for x in warnings: print('WARNING',x)
 print(f'SUMMARY records={len(all_records)} errors={len(errors)} warnings={len(warnings)}')
 return 1 if errors else 0
if __name__=='__main__': sys.exit(main())
