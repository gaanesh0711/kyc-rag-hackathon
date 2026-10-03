import unittest
from types import SimpleNamespace
from unittest.mock import patch
from test_api import api
from fastapi.testclient import TestClient
from simulator import Assessment, CompanyAssessment, dataset_records, simulate

class SimulatorTests(unittest.TestCase):
    def setUp(self):
        api.request_counts.clear()
        data={'ids':['a','b'], 'documents':['Wallet evidence','Investment evidence'], 'metadatas':[
            {'company_name':'Wallet Co','regulator':'RBI','vertical':'PPI & Wallets','source_doc':'wallet.pdf'},
            {'company_name':'Invest Co','regulator':'SEBI','vertical':'Wealthtech','source_doc':'invest.pdf'}]}
        self.model=SimpleNamespace(invoke=lambda messages:Assessment(companies=[CompanyAssessment(record_id='a',status='potential_impact',reasoning='Documented wallet activity.',review_action='Review wallet limits.')]))
        self.chain=SimpleNamespace(retriever=SimpleNamespace(vectorstore=SimpleNamespace(get=lambda **kwargs:data)),llm=SimpleNamespace(with_structured_output=lambda schema:self.model))
        api.chain=self.chain
        self.client=TestClient(api.app)

    def test_dataset_scope_counts_and_options(self):
        data=self.client.get('/simulation/options').json()
        self.assertEqual(data['total_records'],2)
        self.assertEqual(data['total_companies'],2)
        self.assertEqual(data['regulators'],['RBI','SEBI'])

    def test_filters_and_source_linkage(self):
        response=self.client.post('/simulate',json={'rule':'Lower wallet limits','regulator':'RBI','vertical':'PPI & Wallets'})
        self.assertEqual(response.status_code,200)
        data=response.json()
        self.assertEqual(data['reviewed_records'],1)
        self.assertEqual(data['total_records'],2)
        self.assertTrue(data['hypothetical'])
        self.assertEqual(data['companies'][0]['excerpt'],'Wallet evidence')
        self.assertEqual(data['companies'][0]['company'],'Wallet Co')

    def test_invalid_filter_and_empty_scope(self):
        self.assertEqual(self.client.post('/simulate',json={'rule':'Rule','regulator':'Unknown'}).status_code,400)
        self.assertEqual(self.client.post('/simulate',json={'rule':'Rule','regulator':'SEBI','vertical':'PPI & Wallets'}).status_code,400)

    def test_input_bounds(self):
        self.assertEqual(self.client.post('/simulate',json={'rule':'   '}).status_code,400)
        self.assertEqual(self.client.post('/simulate',json={'rule':'a'*2001}).status_code,422)

    def test_incomplete_or_invented_records_rejected(self):
        records=dataset_records(self.chain)
        with self.assertRaises(ValueError):simulate(self.chain,records,'Rule')
        self.model.invoke=lambda messages:Assessment(companies=[CompanyAssessment(record_id='invented',status='no_clear_link',reasoning='Unknown',review_action='Review')])
        with self.assertRaises(ValueError):simulate(self.chain,records[:1],'Rule')

    def test_duplicate_records_rejected(self):
        item=CompanyAssessment(record_id='a',status='potential_impact',reasoning='Wallet',review_action='Review')
        self.model.invoke=lambda messages:Assessment(companies=[item,item])
        with self.assertRaises(ValueError):simulate(self.chain,dataset_records(self.chain),'Rule')

    def test_provider_error_sanitized_and_slot_released(self):
        def fail(messages):raise RuntimeError('private-secret')
        self.model.invoke=fail
        with self.assertLogs(api.logger,level='ERROR'):
            response=self.client.post('/simulate',json={'rule':'Rule','regulator':'RBI'})
        self.assertEqual(response.status_code,502)
        self.assertNotIn('private-secret',response.text)
        self.assertTrue(api.request_slots.acquire(blocking=False))
        api.request_slots.release()

    def test_complete_whole_dataset_review(self):
        self.model.invoke=lambda messages:Assessment(companies=[CompanyAssessment(record_id=record_id,status='insufficient_evidence',reasoning='Cannot establish applicability.',review_action='Check documentation.') for record_id in ['a','b']])
        response=self.client.post('/simulate',json={'rule':'Rule'})
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()['reviewed_records'],2)

if __name__=='__main__':unittest.main()
