# SPDX-License-Identifier: MIT
"""Schema and comparison guards. Declared metadata is not source authentication."""
from datetime import date
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from research_checks import number

def period(p):
    start=date.fromisoformat(p['start']);end=date.fromisoformat(p['end'])
    if start>end:raise ValueError('期间起止颠倒')
    return start,end

def margin_compare(p):
    current=p['current'];prior=p['prior'];cs,ce=period(current);ps,pe=period(prior)
    if any(not isinstance(row.get(k),str) or not row[k].strip() for row in (current,prior) for k in ('scope','unit')):raise ValueError('毛利率范围与单位不能为空')
    if current['scope']!=prior['scope'] or current['unit']!=prior['unit']:return {'status':'blocked','reason':'范围/单位不一致'}
    if (cs.month,cs.day,ce.month,ce.day)!=(ps.month,ps.day,pe.month,pe.day) or cs.year!=ps.year+1 or ce.year!=pe.year+1:return {'status':'blocked','reason':'不是同一年度窗口的同比；半年不能对全年'}
    if prior.get('restatementStatus') not in ('restated','not-required'):return {'status':'blocked','reason':'上期重述状态未知'}
    rev=number(current['revenue'],'revenue',.000001);cost=number(current['cost'],'cost',0);prev=number(prior['revenue'],'prior revenue',.000001);pcost=number(prior['cost'],'prior cost',0)
    cur=number((rev-cost)/rev,'computed current margin');old=number((prev-pcost)/prev,'computed prior margin');delta=number((cur-old)*100,'computed margin change')
    return {'status':'conditional-comparison','currentMargin':cur,'priorMargin':old,'changePctPoints':delta,'limits':'简单毛利率，不含其他税费；不识别收益因果或公司净利润'}

def freight_error(p):
    forecast=p['forecast'];realized=p['realized'];fs,fe=period(forecast);rs,re=period(realized);asof=date.fromisoformat(p['asOf']);quote=date.fromisoformat(forecast['quoteDate'])
    if quote>=fs or quote>asof or re>asof:return {'status':'blocked','reason':'报价非提前冻结或结算期尚未结束'}
    keys=['route','vesselBasis','unit','aggregation','benchmark']
    if (fs,fe)!=(rs,re) or any(not forecast.get(k) or forecast.get(k)!=realized.get(k) for k in keys):return {'status':'blocked','reason':'航线/标准船/单位/指数/结算窗口/聚合方式不匹配'}
    if forecast['aggregation']!='settlement-period-mean':return {'status':'blocked','reason':'需匹配结算期均值，不能用单日价验证月合约'}
    actual=number(realized['value'],'realized',.000001);pred=number(forecast['value'],'forecast',0)
    error=number((pred-actual)/actual,'computed freight error')
    return {'status':'one-declared-observation','signedRelativeError':error,'absoluteRelativeError':abs(error),'limits':'一个声明样本不证明稳定预测能力，不认证输入，不映射股价'}

def source_roots(records):
    if not isinstance(records,list) or len(records)>10000:raise ValueError('sources必须为不超过10000项列表')
    lookup={}
    for row in records:
        id=row['id']
        if not isinstance(id,str) or not id or id in lookup:raise ValueError('来源id重复/空值')
        lookup[id]=row
    roots=set();unknown=[]
    for id in lookup:
        current=id;seen=set();root=None
        while current in lookup:
            if current in seen:raise ValueError('来源链存在循环')
            seen.add(current);row=lookup[current]
            if row.get('parent'):current=row['parent'];continue
            root=row.get('originalPublisher');break
        if root:roots.add(root)
        else:unknown.append(id)
    return {'declaredPublisherRoots':sorted(roots),'knownRootCount':len(roots),'unknownOriginIds':unknown,'limits':'声明源头去重，不认证原始数据独立性或发布者真实性'}

def exposure_bridge(p):
    a=p['profitWeight'];b=p['spotWeight']
    required=['population','period','measure']
    if any(not a.get(k) or a.get(k)!=b.get(k) for k in required):return {'status':'blocked','reason':'利润、船数或船日权重的总体/期间/度量不同，不可相乘认证敞口'}
    return {'status':'declared-aligned-product','value':number(a['value'],'profitWeight',0,1)*number(b['value'],'spotWeight',0,1),'limits':'声明总体匹配的机械乘积，不认证公司利润现货敞口'}

def review(p):
    if not isinstance(p,dict):raise ValueError('输入必须为对象')
    results={}
    for key,fn in [('margin',margin_compare),('freight',freight_error),('sources',source_roots),('exposure',exposure_bridge),('valuation',valuation_series),('identity',identity_compare),('profitInverse',profit_inverse)]:
        if key in p:results[key]=fn(p[key])
    if not results:raise ValueError('至少提供一项核对')
    return {'status':'comparison-guards','sourceVerified':False,'results':results}

def valuation_series(p):
    """Dated vendor observations; never label a sampled window daily or point-in-time."""
    for key in ('source','netAssetBasis','samplingBasis'):
        if not isinstance(p.get(key),str) or not p[key].strip():raise ValueError('估值序列缺少'+key)
    asof=date.fromisoformat(p['asOf']);retrieved=date.fromisoformat(p['retrievedAt']);start,end=period(p)
    if retrieved<asof:raise ValueError('取数日早于当前PB观察日，不能当已知事实')
    if end>asof or start>asof:raise ValueError('估值窗口晚于研究时点')
    rows=p['observations']
    if not isinstance(rows,list) or not rows or len(rows)>100000:raise ValueError('估值观察值数量无效')
    seen=set();values=[];dates=[]
    for row in rows:
        day=date.fromisoformat(row['date'])
        if day in seen:raise ValueError('估值日期重复')
        seen.add(day)
        if day>end or day<start:raise ValueError('估值观察值不在声明窗口')
        dates.append(day);values.append(number(row['value'],'PB',0))
    current=number(p['current'],'current PB',0);target=date.fromisoformat(p['currentDate'])
    if target!=asof or target!=end or target not in dates:raise ValueError('估值当前值日期缺失或与研究时点不一致')
    if values[dates.index(target)]!=current:raise ValueError('当前PB与序列末日不一致')
    dates.sort();gaps=[(b-a).days for a,b in zip(dates,dates[1:])]
    if p['samplingBasis']=='calendar-daily' and (any(g!=1 for g in gaps) or dates[0]!=start):raise ValueError('不能将稀疏或缺段序列声明为自然日日频')
    return {'status':'declared-vendor-recomputation','count':len(values),'firstDate':dates[0].isoformat(),'lastDate':dates[-1].isoformat(),'gapDays':sorted(set(gaps)),'strictLessPercentile':sum(v<current for v in values)/len(values),'ties':sum(v==current for v in values),'pointInTimeCertified':False,'retrievedAfterAsOf':retrieved>asof,'limits':'只复算声明样本；不认证历史可得性、净资产口径或估值风险。窗口名称不能替代实际日期和采样。'}

def identity_compare(p):
    """Match declared security, period and units; not a source certificate."""
    a=p['claim'];b=p['evidence'];asof=date.fromisoformat(p['asOf'])
    for row in (a,b):
        period(row)
        for key in ('symbol','metric','unit','definition'):
            if not isinstance(row.get(key),str) or not row[key].strip():raise ValueError('身份口径缺少'+key)
    if date.fromisoformat(b['publishedAt'])>asof or date.fromisoformat(b['end'])>asof:
        return {'status':'blocked','reason':'证据在研究时点尚未发布或观察期未结束'}
    keys=('symbol','start','end','metric','unit','definition')
    mismatch=[key for key in keys if a[key]!=b[key]]
    if mismatch:return {'status':'blocked','mismatchFields':mismatch,'reason':'公司/期间/指标/单位/定义不匹配，不能替换或认证'}
    delta=number(number(a['value'],'claim value')-number(b['value'],'evidence value'),'computed difference')
    tolerance=number(p.get('absoluteTolerance',0),'absoluteTolerance',0)
    return {'status':'declared-match' if abs(delta)<=tolerance else 'declared-value-conflict','difference':delta,'tolerance':tolerance,'sourceVerified':False,'limits':'声明字段匹配，不认证原文真伪、权益实施到账或因果；不要擅自填写未知期间/税费'}

def profit_inverse(p):
    """Invert an explicitly anchored local scenario, never profit divided by slope."""
    target=p['target'];anchor=p['anchor'];slope=p['sensitivity']
    keys=('symbol','start','end','scope','profitDefinition','profitUnit','taxBasis','ownershipBasis')
    mismatch=[]
    for key in keys:
        values=[row.get(key) for row in (target,anchor,slope)]
        if any(not isinstance(v,str) or not v.strip() or v in ('unknown','未知') for v in values) or len(set(values))!=1:mismatch.append(key)
    if mismatch:return {'status':'blocked','mismatchFields':mismatch,'reason':'目标利润、基准利润和敏感性的公司/业务/期间/税费/归属口径缺失或不一致'}
    for row in (target,anchor,slope):period(row)
    rate_keys=('route','tceDefinition','tceUnit')
    if any(not isinstance(anchor.get(k),str) or not anchor[k].strip() or anchor[k]!=slope.get(k) for k in rate_keys):
        return {'status':'blocked','reason':'敏感性和基准TCE航线/定义/单位不一致'}
    if any(p.get(k) is None for k in ('baselineTce','baselineProfit','validTceRange')):
        return {'status':'blocked','reason':'缺基准TCE、基准利润或局部适用区间；净利润不能直接除以敏感性'}
    if p.get('otherFactorsHeldConstant') is not True:return {'status':'blocked','reason':'未声明其他因素保持不变'}
    bounds=p['validTceRange']
    if not isinstance(bounds,list) or len(bounds)!=2:raise ValueError('validTceRange需两个边界')
    lo=number(bounds[0],'range low',0);hi=number(bounds[1],'range high',lo)
    base=number(p['baselineTce'],'baselineTce',0);profit=number(p['baselineProfit'],'baselineProfit');goal=number(target['value'],'target profit');coef=number(slope['value'],'sensitivity',.000001)
    if not lo<=base<=hi:return {'status':'blocked','reason':'基准运价超出声明适用区间'}
    result=number(base+(goal-profit)/coef,'implied TCE')
    if not lo<=result<=hi:return {'status':'blocked','reason':'反推结果超出局部适用区间，禁止跨极端区间线性外推'}
    return {'status':'conditional-local-scenario','impliedTce':result,'sourceVerified':False,'limits':'仅计算声明的有基准线性情景，不认证公司利润、市场共识、会计保本或安全边际'}

def main():
    ap=argparse.ArgumentParser(description='口径和来源链反例核对，不认证证据');ap.add_argument('--input',required=True);args=ap.parse_args()
    try:
        def reject(s):raise ValueError('禁止非有限JSON常量')
        data=json.loads(Path(args.input).read_text(encoding='utf-8-sig'),parse_constant=reject);result=review(data);print(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False));return 0
    except (ValueError,TypeError,KeyError,OSError,OverflowError,AttributeError) as e:print('核对失败：'+str(e));return 1
if __name__=='__main__':raise SystemExit(main())
