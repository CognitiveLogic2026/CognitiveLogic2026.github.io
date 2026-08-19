import copy, importlib.util, json, tempfile, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('iwv',ROOT/'scripts/international_watch_validator.py'); iwv=importlib.util.module_from_spec(spec); spec.loader.exec_module(iwv)
BASE=ROOT/'data/international-watch/cases/IW-001'

class CrossRecordValidatorTests(unittest.TestCase):
 def run_case(self,mutator=None):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)
   for src in BASE.glob('*.json'): (p/src.name).write_bytes(src.read_bytes())
   if mutator: mutator(p)
   return iwv.main(['--path',str(p)])
 def mutate(self,file,fn):
  def apply(p):
   q=p/file; x=json.loads(q.read_text()); fn(x); q.write_text(json.dumps(x))
  return apply
 def test_valid_iw001(self): self.assertEqual(self.run_case(),0)
 def test_duplicate_id(self): self.assertNotEqual(self.run_case(self.mutate('claim-registry.json',lambda x:x['records'][1].update(id=x['records'][0]['id']))),0)
 def test_missing_reference(self): self.assertNotEqual(self.run_case(self.mutate('claim-registry.json',lambda x:x['records'][0].update(event_id='IW-001-E999'))),0)
 def test_claim_without_origin(self): self.assertNotEqual(self.run_case(self.mutate('claim-registry.json',lambda x:x['records'][0].update(origin_source_id=''))),0)
 def test_evidence_without_does_not_establish(self): self.assertNotEqual(self.run_case(self.mutate('evidence-ledger.json',lambda x:x['records'][0].update(does_not_establish=[]))),0)
 def test_assessment_without_unknowns(self): self.assertNotEqual(self.run_case(self.mutate('epistemic-assessment.json',lambda x:x['records'][0].update(unknowns=[]))),0)
 def test_republication_as_independent(self): self.assertNotEqual(self.run_case(self.mutate('source-dependency.json',lambda x:x['records'][0].update(counts_as_independent_corroboration=True))),0)
 def test_invalid_epistemic_state(self): self.assertNotEqual(self.run_case(self.mutate('epistemic-assessment.json',lambda x:x['records'][0].update(state='TRUE'))),0)
 def test_published_without_approval(self): self.assertNotEqual(self.run_case(self.mutate('claim-registry.json',lambda x:x['records'][0].update(status='published'))),0)
 def test_approved_assessment_without_human_reviewer(self): self.assertNotEqual(self.run_case(self.mutate('epistemic-assessment.json',lambda x:x['records'][0].update(status='approved',reviewer='Pending'))),0)
 def test_impossible_dependency_cycle(self):
  def f(x):
   x['records'][0].update(edge_type='derived_from',**{'from':'IW-001-SRC-005','to':'IW-001-SRC-010'}); y=copy.deepcopy(x['records'][0]); y.update(id='IW-001-DEP-099',edge_id='IW-001-DEP-099',node_id='IW-001-SRC-010',**{'from':'IW-001-SRC-010','to':'IW-001-SRC-005'}); x['records'].append(y)
  self.assertNotEqual(self.run_case(self.mutate('source-dependency.json',f)),0)
 def test_local_archive_hash_missing(self): self.assertNotEqual(self.run_case(self.mutate('evidence-ledger.json',lambda x:x['records'][0].update(archived_uri='https://archive.example/item',content_hash=None))),0)
 def test_forbidden_workflow_transition(self):
  def f(x): x['records'][0]['history'][1].update(to='published')
  self.assertNotEqual(self.run_case(self.mutate('workflow.json',f)),0)
 def test_forbidden_score_field(self): self.assertNotEqual(self.run_case(self.mutate('claim-registry.json',lambda x:x['records'][0].update(truth_score=1))),0)
 def test_missing_file_reference(self): self.assertNotEqual(self.run_case(self.mutate('dossier-manifest.json',lambda x:x['files'].append('absent.json'))),0)

if __name__=='__main__': unittest.main()
