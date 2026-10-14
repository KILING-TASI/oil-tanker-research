# SPDX-License-Identifier: MIT
"""Original conditional arithmetic; inputs are declarations, not authenticated facts."""
import argparse
from datetime import date
import json
import math
from pathlib import Path

def number(value,name,low=None,high=None):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value): raise ValueError(name+'必须是有限数字')
    if low is not None and value<low or high is not None and value>high: raise ValueError(name+'超出范围')
    return float(value)
def storage(p):
    days=number(p['days'],'days',1);cargo=number(p['cargoBarrels'],'cargoBarrels',1)
    hire=number(p['dailyHireUsd'],'dailyHireUsd',0);price=number(p['oilPriceUsdPerBarrel'],'oilPriceUsdPerBarrel',0)
    rate=number(p['annualFundingRate'],'annualFundingRate',0,1);other=number(p['otherCostsUsd'],'otherCostsUsd',0)
    spread=number(p['forwardSpreadUsdPerBarrel'],'forwardSpreadUsdPerBarrel')
    funding=price*cargo*rate*days/365;threshold=(hire*days+funding+other)/cargo
    return {'requiredSpreadUsdPerBarrel':threshold,'declaredSpreadUsdPerBarrel':spread,'netCarryUsd':(spread-threshold)*cargo,'fundingCostUsd':funding,'scope':'同油种、同地点、同交割期限下的声明成本情景；不认证货源、信用、可租船或成交'}
def capacity(p):
    total=number(p['total'],'total',1);a=number(p['restricted'],'restricted',0,total);b=number(p['oldExcluded'],'oldExcluded',0,total)
    overlap=p.get('overlap')
    if overlap is None:
        return {'status':'unknown-overlap','remainingRange':[max(0,total-a-b),total-max(a,b)],'remaining':None}
    overlap=number(overlap,'overlap',max(0,a+b-total),min(a,b))
    return {'status':'conditional','remaining':total-a-b+overlap,'excludedUnion':a+b-overlap,'scope':'两类集合去重；艘数不是可直接执行的有效运力，另需DWT、船型、效率和船货适配'}
def earnings(p):
    n=number(p['operatingVessels'],'operatingVessels',0);days=number(p['earningDays'],'earningDays',0,366);delta=number(p['deltaTceUsdPerDay'],'deltaTceUsdPerDay');fx=number(p['cnyPerUsd'],'cnyPerUsd',0.000001);spot=number(p['spotExposure'],'spotExposure',0,1);tax=number(p['taxRate'],'taxRate',0,1)
    pre=n*days*delta*fx*spot
    return {'preTaxIncrementCny':pre,'afterTaxMechanicalIncrementCny':pre*(1-tax),'scope':'声明期间、同船型的静态边际收入桥接；税率线性对称，负情景不保证可抵税；未模拟租约分成、经营成本变化、汇率套保及公司净利润'}
def percentile(p):
    current=number(p['current'],'current');values=p['values']
    if not isinstance(values,list) or not values or len(values)>100000: raise ValueError('values需1至100000条')
    values=[number(x,'values') for x in values];ties=sum(x==current for x in values)
    return {'strictLessPercentile':sum(x<current for x in values)/len(values),'tieCount':ties,'sampleCount':len(values),'scope':'严格小于的经验分位；输入窗口、日期、频率和净资产口径由调用者声明；不是风险概率'}
FUNCTIONS={'storage':storage,'capacity':capacity,'earnings':earnings,'percentile':percentile}
def review(data):
    if not isinstance(data,dict): raise ValueError('输入必须为对象')
    asof=date.fromisoformat(data['asOf']); results={}
    if not isinstance(data.get('basis'),str) or not data['basis'].strip(): raise ValueError('需填写basis，说明时点、单位和来源/教学假设')
    for name,fn in FUNCTIONS.items():
        if name in data:
            results[name]=fn(data[name])
            for value in results[name].values():
                if isinstance(value,float) and not math.isfinite(value): raise ValueError('计算溢出')
    if not results: raise ValueError('至少提供一个计算模块')
    return {'status':'conditional-arithmetic','asOf':asof.isoformat(),'basis':data['basis'],'sourceVerified':False,'results':results,'limits':['不联网取数，不认证输入来源','不同期限contango不可直接对比','FFA是远期合约报价，不能保证运价或股价预测准确']}
def main():
    ap=argparse.ArgumentParser(description='油运声明假设算术核对');ap.add_argument('--input',required=True);ap.add_argument('--output');args=ap.parse_args()
    try:
        def reject(v): raise ValueError('禁止JSON非有限常量: '+v)
        r=review(json.loads(Path(args.input).read_text(encoding='utf-8-sig'),parse_constant=reject));text=json.dumps(r,ensure_ascii=False,indent=2,allow_nan=False)
        if args.output:
            with Path(args.output).open('x',encoding='utf-8') as f:f.write(text)
        print(text);return 0
    except (OSError,ValueError,KeyError,TypeError,OverflowError) as e:print('核对失败：'+str(e));return 1
if __name__=='__main__':raise SystemExit(main())
