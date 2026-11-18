import unittest
from types import SimpleNamespace
from app.assessment_cache import AssessmentCache

class TestAssessmentCache(unittest.TestCase):
 def test_context_key_and_eviction(self):
  c=AssessmentCache(1);a=SimpleNamespace(assessment_context='SIMULATED_AS_OF',as_of='2026-01-02',required_price_session='2025-12-31',evidence_cutoff_at=None,policy_revision='D',release_revision='r1');b=SimpleNamespace(**{**a.__dict__,'assessment_context':'CURRENT_AS_OF'})
  ka=c.key(a,'A32',10);kb=c.key(b,'A32',10);self.assertNotEqual(ka,kb);c.put(ka,{'payload':1});c.put(kb,{'payload':2});self.assertIsNone(c.get(ka));self.assertEqual(c.get(kb)['payload'],2)

 def test_lookback_is_part_of_the_key(self):
  c=AssessmentCache();r=SimpleNamespace(assessment_context='SIMULATED_AS_OF',as_of='2026-01-02',required_price_session='2025-12-31',evidence_cutoff_at=None,policy_revision='D',release_revision='r1')
  self.assertNotEqual(c.key(r,'A32',5),c.key(r,'A32',10))
