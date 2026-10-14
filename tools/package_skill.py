"""Build a standalone skill archive, excluding reports, evidence and caches."""
import argparse,hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);args=ap.parse_args()
    destination=Path(args.output).resolve()
    if destination.exists():raise FileExistsError('输出已存在，使用新文件名')
    skill=ROOT/'skill';files=[p for p in skill.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.pyc','.pyo')]
    entries={str(p.relative_to(skill)).replace('\\','/'):p.read_bytes() for p in files}
    for name in ('LICENSE','THIRD_PARTY_NOTICES.md'):entries[name]=(ROOT/name).read_bytes()
    manifest={name:hashlib.sha256(raw).hexdigest() for name,raw in sorted(entries.items())}
    entries['PACKAGE_MANIFEST.json']=(json.dumps({'skill':'oil-tanker-research','files':manifest},ensure_ascii=False,indent=2)+'\n').encode()
    destination.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(destination,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for name,raw in sorted(entries.items()):
            info=zipfile.ZipInfo('oil-tanker-research/'+name,date_time=(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16;z.writestr(info,raw)
    print(json.dumps({'output':str(destination),'files':len(entries),'sha256':hashlib.sha256(destination.read_bytes()).hexdigest()},ensure_ascii=False))
if __name__=='__main__':main()
