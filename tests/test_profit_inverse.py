import unittest,sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'skill/scripts'))
from evidence_checks import profit_inverse,review
class ProfitInverse(unittest.TestCase):
    def example(self):
        common=dict(symbol='EXAMPLE',start='2026-01-01',end='2026-12-31',scope='single segment',profitDefinition='attributable net',profitUnit='CNY',taxBasis='after-tax',ownershipBasis='attributable')
        rate=dict(route='same-route',tceDefinition='realised-spot',tceUnit='USD/day')
        return dict(target=dict(**common,value=120),anchor=dict(**common,**rate),sensitivity=dict(**common,**rate,value=2),baselineTce=100,baselineProfit=100,validTceRange=[80,120],otherFactorsHeldConstant=True)
    def test_anchored_equation(self):
        r=profit_inverse(self.example());self.assertEqual(r['impliedTce'],110);self.assertFalse(r['sourceVerified'])
    def test_missing_anchor_is_not_zero(self):
        for key in ('baselineTce','baselineProfit','validTceRange'):
            with self.subTest(key=key):
                p=self.example();p.pop(key);self.assertEqual(profit_inverse(p)['status'],'blocked')
    def test_company_period_tax_and_attribution_mismatches(self):
        for key in ('symbol','end','scope','profitDefinition','profitUnit','taxBasis','ownershipBasis'):
            with self.subTest(key=key):
                p=self.example();p['sensitivity'][key]='different';self.assertEqual(profit_inverse(p)['status'],'blocked')
    def test_unknown_tax_not_assumed(self):
        p=self.example()
        for r in ('target','anchor','sensitivity'):p[r]['taxBasis']='unknown'
        self.assertEqual(profit_inverse(p)['status'],'blocked')
    def test_route_mismatch(self):
        p=self.example();p['sensitivity']['route']='another-route';self.assertEqual(profit_inverse(p)['status'],'blocked')
    def test_extreme_extrapolation(self):
        p=self.example();p['target']['value']=10000;self.assertEqual(profit_inverse(p)['status'],'blocked')
    def test_base_outside_range(self):
        p=self.example();p['baselineTce']=1000;self.assertEqual(profit_inverse(p)['status'],'blocked')
    def test_negative_or_zero_slope(self):
        for v in (0,-1,float('inf'),True):
            p=self.example();p['sensitivity']['value']=v
            with self.assertRaises(ValueError):profit_inverse(p)
    def test_other_factors_not_fixed(self):
        p=self.example();p['otherFactorsHeldConstant']=False;self.assertEqual(profit_inverse(p)['status'],'blocked')
    def test_zero_profit_is_explicit_valid_anchor(self):
        p=self.example();p['baselineProfit']=0;p['target']['value']=20;self.assertEqual(profit_inverse(p)['impliedTce'],110)
    def test_registered_offline_interface(self):
        self.assertEqual(review({'profitInverse':self.example()})['results']['profitInverse']['status'],'conditional-local-scenario')
    def test_report_conclusions_withdrawn_not_certified(self):
        root=Path(__file__).resolve().parents[1];rows={c['id']:c for c in json.loads((root/'evidence/claims-20261014.json').read_text(encoding='utf-8'))['claims']}
        for cid in ['d-0311','d-0405','d-0422','d-0424','d-0595']:
            self.assertEqual(rows[cid]['status'],'withdrawn-inference');self.assertFalse(rows[cid]['activeUse']);self.assertTrue(rows[cid]['missingEvidence'])
    def test_delivery_missing_original_remains_unverified(self):
        root=Path(__file__).resolve().parents[1];rows={c['id']:c for c in json.loads((root/'evidence/claims-20261014.json').read_text(encoding='utf-8'))['claims']}
        for n in range(69,74):
            row=rows[f'd-chart-{n:04}'];self.assertEqual(row['status'],'unverified');self.assertEqual(row['sourcePages'],{'cosco-presentation-h1-2026':[13]});self.assertFalse(row['activeUse'])
    def test_annual_margin_uses_operating_cost_not_total_cost(self):
        root=Path(__file__).resolve().parents[1];a=json.loads((root/'evidence/round4-20261014.json').read_text(encoding='utf-8'))['cmesAnnual']
        self.assertAlmostEqual(a['marginPct'],(a['revenueCny']-a['costCny'])/a['revenueCny']*100);self.assertEqual(round(a['marginPct'],2),26.47)
    def test_pb_chart_subject_and_rounding(self):
        root=Path(__file__).resolve().parents[1];rows={c['id']:c for c in json.loads((root/'evidence/claims-20261014.json').read_text(encoding='utf-8'))['claims']};series={s['sourceId']:s for s in json.loads((root/'evidence/pb-recompute-20261014.json').read_text(encoding='utf-8'))['series']}
        for n in range(108,120):
            c=rows[f's-chart-{n:04}'];s=series[c['sources'][0]];self.assertIn('近 '+str([1,3,5,10][(n-108)//3])+' 年',c['context']);self.assertIn({'600026':'中远海能','601872':'招商轮船','601975':'招商南油'}[s['symbol']],c['context']);self.assertEqual(float(c['original']),round(s['percentileStrictLess']*100,1));self.assertEqual(c['status'],'recomputed-vendor');self.assertFalse(c['activeUse'])
