# SPDX-License-Identifier: MIT
"""Refresh ledger cards and historical badges; --check is read-only."""
import argparse,collections,html,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
LABELS={"unverified":"未完成取证","scope-error":"口径不匹配","secondary-only":"仅有转引","withdrawn-inference":"撤回推断","partial-benchmark":"仅核对邻近日基准","supported-disclosure":"披露原文支持","supported-mirror":"镜像披露支持","recomputed":"已复算限定口径","needs-definition":"须补定义","contradicted":"与所引期间披露冲突","arithmetic-error":"算式错误","partial-vendor":"供应商部分核对","recomputed-vendor":"供应商采样复算","partial-disclosure":"披露部分支持","supported-presentation":"公司推介原文支持","period-conflict":"查到原数但期间错用"}
def esc(value):return html.escape(str(value),quote=True)
def render(data,registry,page):
    lookup={s['id']:s for s in registry['sources']}
    if len(lookup)!=len(registry['sources']):raise ValueError('source IDs duplicated')
    claims=data['claims'];ids=[c['id'] for c in claims]
    if len(ids)!=len(set(ids)):raise ValueError('claim IDs duplicated')
    if dict(collections.Counter(c['status'] for c in claims))!=data['counts']:raise ValueError('counts inconsistent')
    prefix=page[:page.index('<section><h2>逐项台账</h2>')]
    counts=' · '.join(esc(LABELS[k])+': '+str(v) for k,v in data['counts'].items())
    tail='<section><h2>逐项台账</h2><p>'+counts+'</p><label>检索原文、编号或章节 <input id="query" type="search"></label> <label>状态 <select id="status" aria-label="状态"><option value="">全部</option>'+''.join('<option value="'+esc(k)+'">'+esc(v)+'</option>' for k,v in LABELS.items())+'</select></label><p id="match-count" aria-live="polite">'+str(len(claims))+'项</p></section>'
    for c in claims:
        refs=[]
        for sid in c['sources']:
            s=lookup[sid]
            if not s['url'].startswith(('https://','http://')):raise ValueError('unsupported source link')
            pages=c.get('sourcePages',{}).get(sid)
            refs.append('<a href="'+esc(s['url'])+'">'+esc(sid)+'</a>（'+esc(s['tier'])+('，第'+'、'.join(str(p) for p in pages)+'页' if pages else '')+'）')
        tail+='<details class="claim" id="'+esc(c['id'])+'" data-status="'+esc(c['status'])+'"><summary>'+esc(c['id'])+' · '+esc(LABELS[c['status']])+' · '+esc(c['original'][:95])+'</summary><p class="muted">'+esc(c['report'])+' · '+esc(c['section'])+' · 原文件第'+str(c['line'])+'行 · '+esc(c.get('context',''))+'</p><p>原文：'+esc(c['original'])+'</p><p>复核：'+esc(c['ruling'])+'</p><p>原来源声明：'+esc(c.get('sourceClaimed') or '未提供')+'</p><p>本轮证据：'+(' · '.join(refs) or '未取得可定位原始证据')+'</p></details>'
    return prefix+tail+page[page.rfind('<script>'):]
def badges(data,page):
    lookup={c['id']:c for c in data['claims']}
    return re.sub(r'(<a class="recheck" href="evidence-review\.html#([^"]+)">)[^<]*(</a>)',lambda m:m[1]+'〔复核：'+LABELS[lookup[m[2]]['status']]+'〕'+m[3],page)
def main():
    ap=argparse.ArgumentParser();group=ap.add_mutually_exclusive_group();group.add_argument('--write',action='store_true');group.add_argument('--check',action='store_true');args=ap.parse_args()
    data=json.loads((ROOT/'evidence/claims-20261014.json').read_text(encoding='utf-8'));registry=json.loads((ROOT/'evidence/sources-20261014.json').read_text(encoding='utf-8'));changed=[]
    files=['evidence-review.html','油运行业数据拆解-20261014.html','油运行业状态仪表盘-20261014.html']
    for name in files:
        p=ROOT/name;old=p.read_text(encoding='utf-8');new=render(data,registry,old) if name=='evidence-review.html' else badges(data,old)
        if old!=new:
            changed.append(name)
            if args.write:p.write_text(new,encoding='utf-8')
    print(json.dumps({'changed':changed,'mode':'write' if args.write else 'check'},ensure_ascii=False))
    return 0 if args.write or not changed else 1
if __name__=='__main__':raise SystemExit(main())
