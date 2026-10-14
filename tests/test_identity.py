import unittest,json,sys,copy,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'skill/scripts'))
import evidence_checks as check
class IdentityChecks(unittest.TestCase):
    def example(self):
        b=dict(symbol='601975',start='2025-01-01',end='2025-12-31',metric='product-revenue',unit='CNY',definition='disclosed',value=3049698478.29)
        return dict(asOf='2026-10-14',claim=b.copy(),evidence=dict(**b,publishedAt='2026-03-31'))
    def test_period_mislabel(self):
        p=self.example();p['claim'].update(start='2026-01-01',end='2026-06-30')
        self.assertEqual(check.identity_compare(p)['status'],'blocked')
    def test_company_swap(self):
        p=self.example();p['claim']['symbol']='601872';self.assertIn('symbol',check.identity_compare(p)['mismatchFields'])
    def test_dividend_per_ten_vs_share(self):
        p=self.example();p['claim']['unit']='CNY/10shares';self.assertEqual(check.identity_compare(p)['status'],'blocked')
    def test_unknown_definition(self):
        p=self.example();p['evidence']['definition']=''
        with self.assertRaises(ValueError):check.identity_compare(p)
    def test_future_publication(self):
        p=self.example();p['evidence']['publishedAt']='2026-10-15';self.assertEqual(check.identity_compare(p)['status'],'blocked')
    def test_exact_match_not_authentication(self):
        self.assertFalse(check.identity_compare(self.example())['sourceVerified'])
    def test_value_conflict(self):
        p=self.example();p['claim']['value']+=100;self.assertEqual(check.identity_compare(p)['status'],'declared-value-conflict')
if __name__=='__main__':unittest.main()
