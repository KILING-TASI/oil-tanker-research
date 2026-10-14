import unittest,json,sys,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'skill/scripts'))
import evidence_checks as check
class SecondRound(unittest.TestCase):
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
    def test_original_and_mirror_one_root(self):
        rows=json.loads((ROOT/'evidence/sources-20261014.json').read_text(encoding='utf-8'))['sources'];rows={x['id']:x for x in rows};a=rows['nanjing-h1-2026-primary'];b=rows['nanjing-h1-2026-mirror'];self.assertEqual(a['sha256'],b['sha256']);self.assertEqual(a['publisherRoot'],b['publisherRoot'])
    def test_fleet_and_sensitivity_boundaries(self):
        p=json.loads((ROOT/'evidence/second-round-inputs.json').read_text(encoding='utf-8'));f=p['fleet'];self.assertEqual(f['vlccOwned']+f['vlccCharteredIn'],f['vlccOperating']);self.assertEqual(f['allTankersOwned']+f['allTankersCharteredIn'],153);s=p['sensitivity'];self.assertEqual(sum(x['value'] for x in s['components']),s['sum']);self.assertEqual(s['sum']*10000,s['sumCny']);self.assertIsNone(s['days']);self.assertIsNone(s['taxBasis']);self.assertIsNone(s['attributableProfitBridge'])
    def test_exact_period_conflict_mapping(self):
        x=json.loads((ROOT/'evidence/claims-20261014.json').read_text(encoding='utf-8'));c={r['id']:r for r in x['claims']}
        for i in range(385,396):self.assertEqual(c['d-'+str(i).zfill(4)]['status'],'period-conflict');self.assertIn('njtc-fy2025',c['d-'+str(i).zfill(4)]['sources'])
        for id in ['d-0228','d-0229','d-0232','d-0233']:self.assertEqual(c[id]['status'],'contradicted')
if __name__=='__main__':unittest.main()
