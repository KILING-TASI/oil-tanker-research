import json,sys,unittest,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'skill/scripts'))
import evidence_checks as check
class ValuationContracts(unittest.TestCase):
    def test_margin_derived_overflow(self):
        p=dict(current=dict(start='2026-01-01',end='2026-06-30',scope='all',unit='CNY',revenue=.000001,cost=1e308),prior=dict(start='2025-01-01',end='2025-06-30',scope='all',unit='CNY',revenue=1,cost=0,restatementStatus='not-required'))
        with self.assertRaises(ValueError):check.margin_compare(p)
    def test_freight_derived_overflow(self):
        b=dict(start='2026-09-01',end='2026-09-30',route='TD3C',vesselBasis='standard',unit='USD/day',aggregation='settlement-period-mean',benchmark='Baltic')
        p=dict(asOf='2026-10-13',forecast=dict(**b,quoteDate='2026-08-01',value=1e308),realized=dict(**b,value=.000001))
        with self.assertRaises(ValueError):check.freight_error(p)
    def test_retrieved_before_observed(self):
        p=self.valuation();p['retrievedAt']='2026-10-12'
        with self.assertRaises(ValueError):check.valuation_series(p)
    def test_nonobject_root(self):
        with self.assertRaises(ValueError):check.review([])
    def test_empty_margin_basis(self):
        p=dict(current=dict(start='2026-01-01',end='2026-06-30',scope='',unit='CNY',revenue=1,cost=0),prior=dict(start='2025-01-01',end='2025-06-30',scope='',unit='CNY',revenue=1,cost=0,restatementStatus='not-required'))
        with self.assertRaises(ValueError):check.margin_compare(p)
    def valuation(self):return dict(source='synthetic',netAssetBasis='declared',samplingBasis='vendor-sampled',asOf='2026-10-13',retrievedAt='2026-10-14',start='2026-10-11',end='2026-10-13',currentDate='2026-10-13',current=2,observations=[dict(date='2026-10-11',value=1),dict(date='2026-10-13',value=2)])
    def test_retrieval_not_time_machine(self):
        r=check.valuation_series(self.valuation());self.assertFalse(r['pointInTimeCertified']);self.assertTrue(r['retrievedAfterAsOf']);self.assertEqual(r['strictLessPercentile'],.5)
    def test_sparse_not_daily(self):
        p=self.valuation();p['samplingBasis']='calendar-daily'
        with self.assertRaises(ValueError):check.valuation_series(p)
    def test_duplicate_date(self):
        p=self.valuation();p['observations'].append(p['observations'][0])
        with self.assertRaises(ValueError):check.valuation_series(p)
    def test_future_window(self):
        p=self.valuation();p['end']='2026-10-14'
        with self.assertRaises(ValueError):check.valuation_series(p)
    def test_unknown_basis(self):
        p=self.valuation();p['netAssetBasis']=''
        with self.assertRaises(ValueError):check.valuation_series(p)
    def test_current_mismatch(self):
        p=self.valuation();p['current']=3
        with self.assertRaises(ValueError):check.valuation_series(p)
    def test_missing_target(self):
        p=self.valuation();p['observations'].pop()
        with self.assertRaises(ValueError):check.valuation_series(p)
    def test_nonfinite_pb(self):
        p=self.valuation();p['observations'][0]['value']=float('inf')
        with self.assertRaises(ValueError):check.valuation_series(p)
if __name__=='__main__':unittest.main()
