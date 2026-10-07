import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from regulatory.store import Store
from regulatory.engine import evaluate, temporal, version_conflicts
from regulatory.models import Scenario, VersionReview
from regulatory.retrieval import search
from regulatory.sources.base import validate_url, normalize
from regulatory.sources.rbi import discover as rbi_discover
from regulatory.sources.sebi import discover as sebi_discover
from regulatory.api import router

TEXT='1. PPI issuers shall retain customer identification records and assess wallet verification requirements before enabling additional services.\n\n2. This illustrative text is used only for automated software verification and is not a real regulatory requirement.'

class RegulatoryTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory()
  self.store=Store(Path(self.temp.name)/'db.sqlite3')
  self.event=self.ingest(TEXT)
  self.profile={'id':'wallet','name':'Synthetic Wallet Co','review':{'entity_types':['ppi_issuer'],'jurisdiction':'IN','activities':['onboarding'],'effective_from':'2025-01-01','effective_to':None,'complete_entity_types':True}}
  with self.store.connect() as db:
   for id,name in [('wallet','Synthetic Wallet Co'),('broker','Synthetic Broker Co')]:
    db.execute('INSERT INTO entities VALUES(?,?,?)',(id,name,json.dumps({'records':[],'profile_status':'unreviewed'})))
  app=FastAPI()
  app.include_router(router(self.store,lambda request:None))
  self.client=TestClient(app)
 def tearDown(self):self.temp.cleanup()
 def ingest(self,text):
  return self.store.ingest(source_id='test',url='https://www.sebi.gov.in/legal/test.html',title='SYNTHETIC TEST ONLY',regulator='SEBI',raw=text.encode(),text=text)
 def approve_version(self,version_id=None,start='2025-01-01',end=None,status='final'):
  self.store.review('version',version_id or self.event['version_id'],{'reviewer':'TEST REVIEWER','rationale':'Synthetic test only','status':status,'effective_from':start,'effective_to':end,'publication_date':'2024-12-01'})
 def approve_obligation(self):
  o=self.store.obligations()[0]
  self.store.review('obligation',o['id'],{'reviewer':'TEST REVIEWER','rationale':'Synthetic test only','status':'approved','conditions':{'entity_types':['ppi_issuer'],'jurisdiction':'IN','activity':None},'quote':o['quote'],'action':'Retain records'})
  return self.store.obligations()[0]
 def test_duplicate_ingestion_and_reversion(self):
  self.assertFalse(self.ingest(TEXT)['created'])
  self.ingest(TEXT.replace('retain','securely retain'))
  self.assertTrue(self.ingest(TEXT)['created'])
  self.assertEqual(len(self.store.versions()),3)
  self.assertEqual(len(self.store.changes()),2)
 def test_append_only_snapshots(self):
  with self.assertRaises(sqlite3.IntegrityError):
   with self.store.connect() as db:db.execute('DELETE FROM versions')
 def test_diff_preserves_before_after(self):
  self.ingest(TEXT.replace('retain','securely retain'))
  change=self.store.changes()[0]
  self.assertEqual(change['previous_id'],self.event['version_id'])
  self.assertIn('securely retain',change['data']['changes'][0]['after'][0]['text'])
 def test_no_fake_change_on_first_import(self):self.assertEqual(self.store.changes(),[])
 def test_unreviewed_regulations_excluded(self):
  result=search(self.store,'wallet',as_of='2026-01-01')
  self.assertEqual(result['evidence'],[])
  self.assertEqual(result['excluded_versions'],1)
 def test_research_search_returns_official_quote(self):
  result=search(self.store,'wallet',effective_only=False)
  self.assertEqual(len(result['evidence']),1)
  self.assertIn('wallet',result['evidence'][0]['text'])
  self.assertEqual(result['evidence_status'],'unreviewed_source_passages')
 def test_effective_as_of_and_expiry(self):
  self.approve_version(start='2025-01-01',end='2026-01-01')
  self.assertTrue(search(self.store,'wallet',as_of='2025-05-01')['evidence'])
  self.assertFalse(search(self.store,'wallet',as_of='2026-05-01')['evidence'])
 def test_draft_is_never_effective(self):
  self.approve_version(status='draft')
  self.assertFalse(search(self.store,'wallet')['evidence'])
 def test_overlapping_versions_are_excluded(self):
  self.approve_version()
  second=self.ingest(TEXT.replace('retain','securely retain'))
  self.approve_version(second['version_id'])
  result=search(self.store,'wallet',as_of='2026-01-01')
  self.assertEqual(result['conflicting_documents'],1)
  self.assertFalse(result['evidence'])
 def test_review_quote_must_exist(self):
  with self.assertRaises(ValueError):
   self.store.review('obligation',self.store.obligations()[0]['id'],{'quote':'invented quote'})
 def test_unknown_profile_not_excluded(self):
  result=evaluate({'id':'x','name':'X','review':None},{'entity_types':['ppi_issuer'],'jurisdiction':'IN'},hypothetical=True)
  self.assertEqual(result['outcome'],'unknown')
  self.assertTrue(result['missing_information'])
 def test_reviewed_match(self):
  result=evaluate(self.profile,{'entity_types':['ppi_issuer'],'jurisdiction':'IN'},hypothetical=True,as_of='2026-01-01')
  self.assertEqual(result['outcome'],'matches_conditions')
 def test_complete_mismatch_vs_incomplete_profile(self):
  conditions={'entity_types':['stock_broker'],'jurisdiction':'IN'}
  self.assertEqual(evaluate(self.profile,conditions,hypothetical=True)['outcome'],'does_not_match')
  self.profile['review']['complete_entity_types']=False
  self.assertEqual(evaluate(self.profile,conditions,hypothetical=True)['outcome'],'unknown')
 def test_activity_gap_is_unknown(self):
  result=evaluate(self.profile,{'entity_types':['ppi_issuer'],'jurisdiction':'IN','activity':'undocumented'},hypothetical=True)
  self.assertEqual(result['outcome'],'unknown')
 def test_actual_and_scenario_share_matching(self):
  self.approve_version()
  o=self.approve_obligation()
  result=evaluate(self.profile,o['review']['conditions'],obligation=o,as_of='2026-01-01')
  self.assertEqual(result['outcome'],'matches_conditions')
 def test_unapproved_obligation_never_active(self):
  o=self.store.obligations()[0]
  self.assertEqual(evaluate(self.profile,o['conditions'],obligation=o)['outcome'],'unknown')
 def test_expired_profile_unknown(self):
  self.profile['review']['effective_to']='2025-02-01'
  self.assertEqual(evaluate(self.profile,{'entity_types':['ppi_issuer'],'jurisdiction':'IN'},hypothetical=True,as_of='2026-01-01')['outcome'],'unknown')
 def test_unsafe_urls_rejected(self):
  for url in ['http://www.sebi.gov.in/a','https://127.0.0.1/a','https://www.sebi.gov.in.evil.test/a','https://user:password@www.sebi.gov.in/a','https://www.sebi.gov.in:444/a']:
   with self.subTest(url=url),self.assertRaises(ValueError):validate_url(url,'SEBI',resolve=False)
 def test_private_dns_rejected(self):
  with patch('socket.getaddrinfo',return_value=[(2,1,6,'',('127.0.0.1',443))]),self.assertRaises(ValueError):validate_url('https://www.sebi.gov.in/a','SEBI')
 def test_rss_and_sebi_discovery(self):
  rss=b'<rss><channel><item><title>Rule</title><link>https://www.rbi.org.in/a</link></item></channel></rss>'
  self.assertEqual(len(rbi_discover(rss,'')),1)
  html=b'<a href="/legal/circulars/oct-2026/example.html">Example</a><a href="https://evil.test/legal/circulars/a.html">Bad</a>'
  self.assertEqual(len(sebi_discover(html,'https://www.sebi.gov.in')),1)
 def test_challenge_not_ingested(self):
  with self.assertRaises(ValueError):normalize(b'<html>Access denied. Please complete captcha</html>','text/html')
 def test_xml_entities_rejected(self):
  with self.assertRaises(ValueError):rbi_discover(b'<!DOCTYPE rss><rss/>','')
 def test_simulation_audit_and_conditions(self):
  response=self.client.post('/v2/simulate',json={'rule':'Hypothetical rule','conditions':{'entity_types':['ppi_issuer']}})
  self.assertEqual(response.status_code,200)
  data=response.json()
  self.assertEqual(data['counts'],{'unknown':2})
  audit=self.client.get('/v2/audit/'+data['audit_id']).json()
  self.assertEqual(audit['data']['input']['rule'],'Hypothetical rule')
  self.assertEqual(audit['data']['output']['results'],data['results'])
 def test_scenario_validation(self):
  self.assertEqual(self.client.post('/v2/simulate',json={'rule':'rule','conditions':{'entity_types':[]}}).status_code,422)
  self.assertEqual(self.client.post('/v2/simulate',json={'rule':'rule','conditions':{'entity_types':['ppi_issuer']},'entity_ids':['fake']}).status_code,400)
 def test_comparison_uses_one_obligation_set(self):
  response=self.client.post('/v2/compare',json={'entity_ids':['wallet','broker']})
  self.assertEqual(response.status_code,200)
  data=response.json()
  self.assertEqual(len(data['rows'][0]['results']),2)
  self.assertEqual({x['outcome'] for x in data['rows'][0]['results']},{'unknown'})
 def test_duplicate_comparison_rejected(self):
  self.assertEqual(self.client.post('/v2/compare',json={'entity_ids':['wallet','wallet']}).status_code,400)
 def test_no_public_review_or_sync_endpoint(self):
  self.assertEqual(self.client.post('/v2/review',json={}).status_code,404)
  self.assertEqual(self.client.post('/v2/sync',json={}).status_code,404)
 def test_hypothetical_does_not_mutate_official_corpus(self):
  before=len(self.store.versions())
  self.client.post('/v2/simulate',json={'rule':'new hypothetical rule','conditions':{'entity_types':['ppi_issuer']}})
  self.assertEqual(len(self.store.versions()),before)
 def test_invalid_effective_period(self):
  with self.assertRaises(ValueError):VersionReview(reviewer='test',rationale='Test review rationale',status='final',effective_from='2026-01-02',effective_to='2026-01-01')
 def test_superseded_version_remains_historically_searchable(self):
  self.approve_version(start='2025-01-01',end='2026-01-01',status='superseded')
  self.assertTrue(search(self.store,'wallet',as_of='2025-06-01')['evidence'])
  self.assertFalse(search(self.store,'wallet',as_of='2026-06-01')['evidence'])
 def test_profile_history_matches_requested_date(self):
  old={**self.profile['review'],'effective_to':'2026-01-01'}
  new={**self.profile['review'],'entity_types':['stock_broker'],'effective_from':'2026-01-01'}
  self.profile['review_history']=[old,new]
  self.profile['review']=new
  result=evaluate(self.profile,{'entity_types':['ppi_issuer'],'jurisdiction':'IN'},hypothetical=True,as_of='2025-06-01')
  self.assertEqual(result['outcome'],'matches_conditions')
  self.assertEqual(result['profile_review']['entity_types'],['ppi_issuer'])
 def test_actual_impact_audited(self):
  o=self.store.obligations()[0]
  response=self.client.post('/v2/impact/'+o['id'])
  self.assertEqual(response.status_code,200)
  self.assertEqual(self.client.get('/v2/audit/'+response.json()['audit_id']).json()['kind'],'actual_impact')
 def test_semantic_failure_disclosed(self):
  with patch('regulatory.retrieval.vectors',side_effect=RuntimeError('not available')):
   result=search(self.store,'wallet',effective_only=False,semantic=True)
  self.assertEqual(result['retrieval_mode'],'lexical_bm25')
  self.assertIn('unavailable',result['retrieval_notice'])

if __name__=='__main__':unittest.main()
