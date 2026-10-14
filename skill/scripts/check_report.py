# SPDX-License-Identifier: MIT
"""Static HTML checks; no data authenticity or browser-render certification."""
import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

VOID = set("area base br col embed hr img input link meta param source track wbr".split())
class Inspector(HTMLParser):
    def __init__(self):
        super().__init__(); self.stack=[]; self.ids=set(); self.issues=[]; self.scripts=[]; self.current=None; self.script_type=''; self.external=False
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if a.get('id'):
            if a['id'] in self.ids: self.issues.append('duplicate id: '+a['id'])
            self.ids.add(a['id'])
        if tag not in VOID: self.stack.append(tag)
        if tag=='script':
            self.script_type=a.get('type','').lower(); self.external='src' in a; self.current=[]
    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag,attrs)
        if tag not in VOID: self.handle_endtag(tag)
    def handle_data(self,data):
        if self.current is not None: self.current.append(data)
    def handle_endtag(self,tag):
        if tag in VOID: self.issues.append('closing void tag: '+tag); return
        if not self.stack or self.stack[-1]!=tag:
            self.issues.append('line %d: unexpected </%s>, open=%s' % (self.getpos()[0],tag,self.stack[-1] if self.stack else 'none'))
            if tag in self.stack:
                self.stack=self.stack[:len(self.stack)-1-self.stack[::-1].index(tag)]
        else: self.stack.pop()
        if tag=='script' and self.current is not None:
            if not self.external and self.script_type in ('','text/javascript','application/javascript','module'):
                self.scripts.append((''.join(self.current),self.script_type=='module'))
            self.current=None

def inspect(text,node=None,skip_js=False):
    parser=Inspector(); parser.feed(text); parser.close()
    issues=list(parser.issues)
    if parser.stack: issues.append('unclosed tags: '+', '.join(parser.stack))
    # Only literal ECharts init calls are checked; dynamic containers need browser review.
    inits=re.findall(r"echarts\.init\s*\(\s*document\.getElementById\(\s*['\"]([^'\"]+)['\"]\s*\)", '\n'.join(s for s,_ in parser.scripts))
    for name in inits:
        if name not in parser.ids: issues.append('chart target missing: '+name)
    if len(inits)!=len(set(inits)): issues.append('chart target initialized more than once')
    for name in parser.ids:
        if name.startswith('chart_') and name not in inits: issues.append('chart container uninitialized: '+name)
    js='not-applicable' if not parser.scripts else 'skipped'
    if parser.scripts and not skip_js:
        exe=shutil.which(node or 'node')
        if not exe: js='unavailable'
        else:
            js='checked'
            with tempfile.TemporaryDirectory() as tmp:
                for i,(script,module) in enumerate(parser.scripts):
                    path=Path(tmp)/('block%d.'%i+('mjs' if module else 'js')); path.write_text(script,encoding='utf-8')
                    try: result=subprocess.run([exe,'--check',str(path)],capture_output=True,text=True,timeout=15)
                    except (OSError,subprocess.TimeoutExpired) as e: issues.append('JS checker failed: '+str(e)); break
                    if result.returncode: issues.append('JS block %d: %s'%(i,result.stderr.strip()))
    status='failed' if issues else ('incomplete' if js in ('skipped','unavailable') else 'passed-static-checks')
    return {'status':status,'issues':issues,'javascript':js,'charts':len(inits),'scope':'HTML explicit nesting, ids, literal chart targets and per-script syntax; no runtime, factual or source verification'}

def main():
    ap=argparse.ArgumentParser(description='HTML静态核对，不认证数据或浏览器效果'); ap.add_argument('report'); ap.add_argument('--node'); ap.add_argument('--no-js',action='store_true'); ap.add_argument('--json-out'); args=ap.parse_args()
    try: result=inspect(Path(args.report).read_text(encoding='utf-8-sig'),args.node,args.no_js)
    except (OSError,UnicodeError) as e: result={'status':'failed','issues':[str(e)]}
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if args.json_out: Path(args.json_out).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return 1 if result['status']=='failed' else (2 if result['status']=='incomplete' else 0)
if __name__=='__main__': raise SystemExit(main())
