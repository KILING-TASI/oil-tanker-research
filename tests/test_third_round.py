import json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class ThirdRound(unittest.TestCase):
    def setUp(self):
        self.rows={c['id']:c for c in json.loads((ROOT/'evidence/claims-20261014.json').read_text(encoding='utf-8'))['claims']}
    def test_segment_chart_matches_period_correction(self):
        for n in range(94,98):
            c=self.rows[f'd-chart-{n:04}'];self.assertEqual(c['status'],'contradicted');self.assertEqual(c['sourcePages'],{'cmes-h1-2026':[16]});self.assertFalse(c['activeUse'])
    def test_annual_chart_cannot_enter_current_comparison(self):
        for n in range(98,101):
            c=self.rows[f'd-chart-{n:04}'];self.assertEqual(c['status'],'period-conflict');self.assertIn('2025全年',c['ruling']);self.assertFalse(c['activeUse'])
    def test_locked_is_not_realised(self):
        c=self.rows['d-chart-0078'];self.assertEqual(c['status'],'partial-disclosure');self.assertIn('86%',c['ruling']);self.assertFalse(c['activeUse'])
    def test_cash_guide_not_chinese_accounting_floor(self):
        for cid in ['d-0327','d-chart-0074','d-chart-0080']:
            c=self.rows[cid];self.assertIn('未来12个月',c['ruling']);self.assertIn('不是会计利润保本',c['ruling']);self.assertEqual(c['sources'],['frontline-q2-2026'])
    def test_margins_do_not_certify_cross_period_growth(self):
        for n in range(55,58):
            c=self.rows[f'd-chart-{n:04}'];self.assertEqual(c['status'],'recomputed');self.assertIn('不能',c['ruling'])
