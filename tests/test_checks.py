import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
def load(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'skill/scripts'/ (name+'.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
calc=load('research_checks');html=load('check_report')
class Arithmetic(unittest.TestCase):
    def test_overlap_unknown(self):
        r=calc.capacity(dict(total=100,restricted=20,oldExcluded=30));self.assertIsNone(r['remaining']);self.assertEqual(r['remainingRange'],[50,70])
    def test_overlap_exact(self):self.assertEqual(calc.capacity(dict(total=100,restricted=20,oldExcluded=30,overlap=10))['remaining'],60)
    def test_impossible_overlap(self):
        with self.assertRaises(ValueError):calc.capacity(dict(total=100,restricted=80,oldExcluded=70,overlap=10))
    def test_storage_funding(self):
        r=calc.storage(dict(days=90,cargoBarrels=2000000,dailyHireUsd=50000,oilPriceUsdPerBarrel=70,annualFundingRate=.05,otherCostsUsd=200000,forwardSpreadUsdPerBarrel=5));self.assertAlmostEqual(r['requiredSpreadUsdPerBarrel'],3.21301369863);self.assertGreater(r['netCarryUsd'],0)
    def test_zero_capacity(self):
        with self.assertRaises(ValueError):calc.storage(dict(days=90,cargoBarrels=0))
    def test_earnings_units(self):
        r=calc.earnings(dict(operatingVessels=40,earningDays=350,deltaTceUsdPerDay=10000,cnyPerUsd=7,spotExposure=.8,taxRate=.25));self.assertEqual(r['preTaxIncrementCny'],784000000);self.assertEqual(r['afterTaxMechanicalIncrementCny'],588000000)
    def test_nonfinite_bool(self):
        for x in [float('nan'),float('inf'),True]:
            with self.subTest(x=x),self.assertRaises(ValueError):calc.number(x,'x')
    def test_ties(self):self.assertEqual(calc.percentile(dict(current=2,values=[1,2,2,3]))['strictLessPercentile'],.25)
    def test_empty_percentile(self):
        with self.assertRaises(ValueError):calc.percentile(dict(current=2,values=[]))
class Html(unittest.TestCase):
    def test_balanced_but_wrong_nesting(self):self.assertEqual(html.inspect('<div><p>x</div></p>')['status'],'failed')
    def test_duplicate_id(self):self.assertEqual(html.inspect('<div id="x"></div><div id="x"></div>')['status'],'failed')
    def test_comments_not_tags(self):self.assertEqual(html.inspect('<!-- <div> --><p>x</p>')['status'],'passed-static-checks')
    def test_quote_variants_missing_chart(self):
        r=html.inspect('<script>echarts.init(document.getElementById("chart_a"));</script>',skip_js=True);self.assertEqual(r['status'],'failed')
    def test_json_not_javascript(self):self.assertEqual(html.inspect('<script type="application/json">{}</script>')['javascript'],'not-applicable')
    def test_node_missing_is_incomplete(self):
        with patch.object(html.shutil,'which',return_value=None):self.assertEqual(html.inspect('<script>let x=1</script>')['status'],'incomplete')
    def test_explicit_skip_incomplete(self):self.assertEqual(html.inspect('<script>let x=1</script>',skip_js=True)['status'],'incomplete')
    def test_independent_script_syntax(self):
        if not html.shutil.which('node'):self.skipTest('node unavailable')
        self.assertEqual(html.inspect('<script>let x=1;</script><script>let x=2;</script>')['status'],'passed-static-checks')
    def test_bad_javascript(self):
        if not html.shutil.which('node'):self.skipTest('node unavailable')
        self.assertEqual(html.inspect('<script>const = ;</script>')['status'],'failed')


class Contract(unittest.TestCase):
    def test_empty_modules(self):
        with self.assertRaises(ValueError):calc.review(dict(asOf='2026-10-14',basis='test'))
    def test_missing_basis(self):
        with self.assertRaises(ValueError):calc.review(dict(asOf='2026-10-14',basis='',capacity={}))
    def test_invalid_date(self):
        with self.assertRaises(ValueError):calc.review(dict(asOf='2026-99-99',basis='test'))
    def test_exposure_out_of_bounds(self):
        for ratio in [-.1,1.01]:
            with self.subTest(ratio=ratio),self.assertRaises(ValueError):calc.earnings(dict(operatingVessels=10,earningDays=350,deltaTceUsdPerDay=10000,cnyPerUsd=7,spotExposure=ratio,taxRate=.25))
    def test_negative_rate_scenario(self):
        r=calc.earnings(dict(operatingVessels=10,earningDays=350,deltaTceUsdPerDay=-1000,cnyPerUsd=7,spotExposure=.5,taxRate=.25));self.assertEqual(r['preTaxIncrementCny'],-12250000)
    def test_no_source_certification(self):
        r=calc.review(dict(asOf='2026-10-14',basis='declared',capacity=dict(total=100,restricted=20,oldExcluded=30)));self.assertFalse(r['sourceVerified'])
    def test_cli_preserves_old_result(self):
        import tempfile,subprocess,sys
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'result.json';target.write_text('frozen',encoding='utf-8')
            r=subprocess.run([sys.executable,'-X','utf8',str(ROOT/'skill/scripts/research_checks.py'),'--input',str(ROOT/'examples/teaching.json'),'--output',str(target)],capture_output=True)
            self.assertEqual(r.returncode,1);self.assertEqual(target.read_text(),'frozen')
    def test_unclosed_tags(self):self.assertEqual(html.inspect('<div><p>x</p>')['status'],'failed')
    def test_script_attribute_quotes(self):self.assertEqual(html.inspect('<script type="application/ld+json">{"x":1}</script>')['status'],'passed-static-checks')
    def test_duplicate_chart_init(self):self.assertEqual(html.inspect('<div id="chart_a"></div><script>echarts.init(document.getElementById("chart_a"));echarts.init(document.getElementById("chart_a"));</script>',skip_js=True)['status'],'failed')
if __name__=='__main__':unittest.main()
