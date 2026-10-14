import importlib.util,sys,copy,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'skill/scripts'))
import evidence_checks as check
class EvidenceAttack(unittest.TestCase):
    def margin(self):return dict(current=dict(start='2026-01-01',end='2026-06-30',scope='consolidated',unit='CNY',revenue=200,cost=100),prior=dict(start='2025-01-01',end='2025-06-30',scope='consolidated',unit='CNY',restatementStatus='not-required',revenue=100,cost=70))
    def freight(self):
        base=dict(start='2019-11-01',end='2019-11-30',route='TD3C',vesselBasis='standard',unit='USD/day',aggregation='settlement-period-mean',benchmark='Baltic')
        return dict(asOf='2019-12-01',forecast={**base,'quoteDate':'2019-10-20','value':80000},realized={**base,'value':75000})
    def test_matched_margin(self):self.assertAlmostEqual(check.margin_compare(self.margin())['changePctPoints'],20)
    def test_half_vs_full(self):
        p=self.margin();p['prior']['end']='2025-12-31';self.assertEqual(check.margin_compare(p)['status'],'blocked')
    def test_restatement_unknown(self):
        p=self.margin();p['prior'].pop('restatementStatus');self.assertEqual(check.margin_compare(p)['status'],'blocked')
    def test_scope_mismatch(self):
        p=self.margin();p['prior']['scope']='oil';self.assertEqual(check.margin_compare(p)['status'],'blocked')
    def test_currency_mismatch(self):
        p=self.margin();p['prior']['unit']='USD';self.assertEqual(check.margin_compare(p)['status'],'blocked')
    def test_matched_single_freight(self):self.assertEqual(check.freight_error(self.freight())['status'],'one-declared-observation')
    def test_ffa_november_vs_october(self):
        p=self.freight();p['realized'].update(start='2019-10-24',end='2019-10-24');self.assertEqual(check.freight_error(p)['status'],'blocked')
    def test_route_mismatch(self):
        p=self.freight();p['realized']['route']='TD22';self.assertEqual(check.freight_error(p)['status'],'blocked')
    def test_unfinished_settlement(self):
        p=self.freight();p['asOf']='2019-11-15';self.assertEqual(check.freight_error(p)['status'],'blocked')
    def test_late_forecast(self):
        p=self.freight();p['forecast']['quoteDate']='2019-11-10';self.assertEqual(check.freight_error(p)['status'],'blocked')
    def test_benchmark_missing(self):
        p=self.freight();p['forecast'].pop('benchmark');self.assertEqual(check.freight_error(p)['status'],'blocked')
    def test_point_not_mean(self):
        p=self.freight();p['realized']['aggregation']='daily-point';self.assertEqual(check.freight_error(p)['status'],'blocked')
    def test_reposts_one_root(self):
        r=check.source_roots([dict(id='a',originalPublisher='Baltic'),dict(id='b',parent='a'),dict(id='c',parent='b')]);self.assertEqual(r['knownRootCount'],1)
    def test_unknown_parent(self):self.assertEqual(check.source_roots([dict(id='a',parent='missing')])['knownRootCount'],0)
    def test_source_cycle(self):
        with self.assertRaises(ValueError):check.source_roots([dict(id='a',parent='b'),dict(id='b',parent='a')])
    def test_duplicate_source(self):
        with self.assertRaises(ValueError):check.source_roots([dict(id='a'),dict(id='a')])
    def test_profit_share_vs_vessel_share(self):
        p=dict(profitWeight=dict(population='all-foreign',period='H1',measure='gross-profit',value=.782),spotWeight=dict(population='VLCC',period='H1',measure='vessel-count',value=.83));self.assertEqual(check.exposure_bridge(p)['status'],'blocked')
    def test_same_population_different_period(self):
        p=dict(profitWeight=dict(population='x',period='Q2',measure='profit',value=.5),spotWeight=dict(population='x',period='H1',measure='profit',value=.5));self.assertEqual(check.exposure_bridge(p)['status'],'blocked')
    def test_false_source_authentication(self):self.assertFalse(check.review(dict(sources=[dict(id='a')]))['sourceVerified'])
if __name__=='__main__':unittest.main()
