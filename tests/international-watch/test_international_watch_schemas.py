import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker, RefResolver


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT / "schemas" / "international-watch"
EXAMPLE_DIR = ROOT / "data" / "international-watch" / "examples"
PAIRS = {
    "event-registry": "event-registry.min.json",
    "claim-registry": "claim-registry.min.json",
    "international-watch-source-registry": "international-watch-source-registry.min.json",
    "evidence-ledger": "evidence-ledger.min.json",
    "source-dependency": "source-dependency.min.json",
    "narrative-comparison": "narrative-comparison.min.json",
    "epistemic-assessment": "epistemic-assessment.min.json",
}
FORBIDDEN_KEYS = {"truth_score", "trust_score", "truth_percentage", "probability_true"}


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def validator(name):
    schema = load(SCHEMA_DIR / f"{name}.schema.json")
    common = load(SCHEMA_DIR / "common.schema.json")
    Draft202012Validator.check_schema(schema)
    resolver = RefResolver.from_schema(
        schema,
        store={common["$id"]: common, "common.schema.json": common},
    )
    return Draft202012Validator(schema, resolver=resolver, format_checker=FormatChecker())


def walk_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_keys(child)


class InternationalWatchSchemaTests(unittest.TestCase):
    def test_minimal_examples_validate(self):
        for schema_name, example_name in PAIRS.items():
            with self.subTest(schema=schema_name):
                validator(schema_name).validate(load(EXAMPLE_DIR / example_name))

    def test_fixture_references_and_claim_invariants(self):
        event = load(EXAMPLE_DIR / PAIRS["event-registry"])
        claim = load(EXAMPLE_DIR / PAIRS["claim-registry"])
        source = load(EXAMPLE_DIR / PAIRS["international-watch-source-registry"])
        evidence = load(EXAMPLE_DIR / PAIRS["evidence-ledger"])
        dependency = load(EXAMPLE_DIR / PAIRS["source-dependency"])
        assessment = load(EXAMPLE_DIR / PAIRS["epistemic-assessment"])
        self.assertEqual(claim["event_id"], event["event_id"])
        self.assertEqual(claim["origin_source_id"], source["source_id"])
        self.assertEqual(set(claim["evidence_refs"]), {evidence["evidence_id"]})
        self.assertEqual(set(claim["dependency_refs"]), {dependency["edge_id"]})
        self.assertEqual(claim["assessment_id"], assessment["assessment_id"])
        self.assertTrue(claim["origin_source_id"] and claim["temporal_scope"] and claim["claim_type"])
        required_claim_fields = {
            "claim_id", "event_id", "claim_text_original", "language", "translation",
            "translation_method", "claim_type", "speaker_actor_id", "origin_source_id",
            "origin_timestamp", "publication_timestamp", "original_context", "subject",
            "predicate", "object", "qualifiers", "geographic_scope", "temporal_scope",
            "definition_refs", "testability", "evidence_refs", "counter_evidence_refs",
            "dependency_refs", "assessment_id",
        }
        self.assertTrue(required_claim_fields.issubset(claim))

    def test_assessment_has_reasoning_rules_and_limits(self):
        assessment = load(EXAMPLE_DIR / PAIRS["epistemic-assessment"])
        self.assertTrue(assessment["state"] and assessment["reasoning_summary"])
        self.assertTrue(assessment["decision_rules_applied"] and assessment["limits"])

    def test_every_evidence_states_what_it_does_not_establish(self):
        self.assertTrue(load(EXAMPLE_DIR / PAIRS["evidence-ledger"])["does_not_establish"])

    def test_republication_is_not_independent_corroboration(self):
        dependency = load(EXAMPLE_DIR / PAIRS["source-dependency"])
        self.assertTrue(dependency["republication_or_translation"])
        self.assertFalse(dependency["counts_as_independent_corroboration"])
        invalid = dict(dependency, counts_as_independent_corroboration=True)
        self.assertTrue(list(validator("source-dependency").iter_errors(invalid)))

    def test_no_truth_or_generic_trust_scores_or_truth_percentages(self):
        files = list(SCHEMA_DIR.glob("*.json")) + list(EXAMPLE_DIR.glob("*.json"))
        for path in files:
            self.assertTrue(FORBIDDEN_KEYS.isdisjoint(set(walk_keys(load(path)))), path)

    def test_iw_001_is_explicitly_non_conclusive_and_non_publishable(self):
        manifest = load(ROOT / "data" / "international-watch" / "manifest.json")
        assessment = load(EXAMPLE_DIR / PAIRS["epistemic-assessment"])
        self.assertEqual(manifest["case_seed"], "IW-001")
        self.assertFalse(manifest["publication_allowed"])
        self.assertEqual(assessment["state"], "INDETERMINABILE")

    def test_iw_003_records_human_publication_authorization(self):
        case = ROOT / "data" / "international-watch" / "cases" / "IW-003"
        manifest = load(case / "dossier-manifest.json")
        workflow = load(case / "workflow.json")["records"][0]
        claims = load(case / "claim-registry.json")["records"]
        assessments = load(case / "epistemic-assessment.json")["records"]
        self.assertEqual(manifest["status"], "published")
        self.assertTrue(manifest["publication_allowed"])
        self.assertIsNotNone(manifest["approved_at"])
        self.assertIsNotNone(manifest["published_at"])
        self.assertEqual(workflow["current_state"], "published")
        self.assertTrue(all(record["status"] == "approved" for record in claims + assessments))
        main = next(record for record in assessments if record["claim_id"] == "IW-003-CLM-001")
        self.assertEqual(main["state"], "CONTRADDETTO")


if __name__ == "__main__":
    unittest.main()
