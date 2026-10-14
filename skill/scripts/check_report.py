#!/usr/bin/env python3
"""
HTML 研报交付前校验脚本。

校验四项：
  1. HTML 标签配对（div/table/tr/td/th/p/b/ul/li/h2/h3）
  2. 内联 JS 语法（需 node 可执行）
  3. ECharts 容器 id 与 echarts.init(getElementById(...)) 一一对应
  4. 按 <h2> 分段定位不平衡位置，便于精确定位

用法：
    python check_report.py <report.html>
    python check_report.py <report.html> --no-js      # 跳过 JS 校验
    python check_report.py <report.html> --node <path-to-node>

退出码：0 = 全部通过；1 = 存在问题

实测背景：本脚本在油运研报的四轮迭代中抓出过 3 处
`<div class="src">` 误用 `</p>` 闭合 —— 浏览器会容错解析，
肉眼在预览里完全看不出来，但会破坏后续所有嵌套结构。
"""

import argparse
import io
import os
import re
import subprocess
import sys
import tempfile

TAGS = ["div", "table", "tr", "td", "th", "p", "b", "ul", "li", "h2", "h3", "script"]

# 常见误闭合模式：<div class="xxx"> 内容 </p>
BAD_CLOSE_PATTERNS = [
    (r'<div class="(src|key|warn|note|sub|grid|box|kpi|card|disc)"[^>]*>[^<]*?</p>',
     'div 误用 </p> 闭合'),
]


def read_file(path):
    with io.open(path, encoding="utf-8") as f:
        return f.read()


def check_tags(html):
    """全文件标签配对。"""
    issues = []
    for t in TAGS:
        open_n = len(re.findall(r"<" + t + r"[ >]", html))
        close_n = len(re.findall(r"</" + t + r">", html))
        if open_n != close_n:
            issues.append((t, open_n, close_n))
    return issues


def check_bad_close(html):
    """检测 div 误用 </p> 闭合这类模式。"""
    hits = []
    for pat, desc in BAD_CLOSE_PATTERNS:
        for m in re.finditer(pat, html):
            line = html[:m.start()].count("\n") + 1
            hits.append((line, desc, m.group(0)[:80]))
    return hits


def check_by_section(html):
    """按 <h2> 分段统计 div/p 平衡，定位到具体章节。"""
    parts = re.split(r"(<h2>.*?</h2>)", html, flags=re.S)
    out = []
    cur = "（报告头部）"
    for p in parts:
        if p.startswith("<h2>"):
            cur = re.sub(r"<[^>]+>", "", p).strip()[:36]
            continue
        o = len(re.findall(r"<div\b", p))
        c = len(re.findall(r"</div>", p))
        po = len(re.findall(r"<p[ >]", p))
        pc = len(re.findall(r"</p>", p))
        if o != c or po != pc:
            out.append((cur, o, c, po, pc))
    return out


def check_charts(html):
    """ECharts 容器与 init 是否一一对应。"""
    divs = set(re.findall(r'id="(chart_[A-Za-z0-9_]+)"', html))
    inits = set(re.findall(r"getElementById\('(chart_[A-Za-z0-9_]+)'\)", html))
    return divs, inits, sorted(inits - divs), sorted(divs - inits)


def check_js(html, node_path):
    """抽取内联 JS 并用 node --check 校验语法。"""
    blocks = re.findall(r"<script(?![^>]*\ssrc=)[^>]*>(.*?)</script>", html, re.S)
    if not blocks:
        return None, "无内联 JS"
    js = "\n".join(blocks)
    fd, tmp = tempfile.mkstemp(suffix=".js")
    os.close(fd)
    try:
        with io.open(tmp, "w", encoding="utf-8") as f:
            f.write(js)
        r = subprocess.run([node_path, "--check", tmp],
                           capture_output=True, text=True)
        if r.returncode == 0:
            return True, "{} 个 script 块，{} 字符".format(len(blocks), len(js))
        return False, (r.stderr or r.stdout).strip()[:600]
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def main():
    ap = argparse.ArgumentParser(description="HTML 研报交付前校验")
    ap.add_argument("report", help="HTML 报告路径")
    ap.add_argument("--no-js", action="store_true", help="跳过 JS 语法校验")
    ap.add_argument("--node", default=None, help="node 可执行文件路径")
    args = ap.parse_args()

    if not os.path.exists(args.report):
        print("ERROR: 文件不存在: {}".format(args.report))
        return 1

    html = read_file(args.report)
    print("=" * 62)
    print("报告：{}".format(os.path.basename(args.report)))
    print("大小：{:,} 字节    h2 章节数：{}".format(
        len(html.encode("utf-8")), len(re.findall(r"<h2>", html))))
    print("=" * 62)

    failed = False

    # 1. 标签配对
    issues = check_tags(html)
    print("\n[1] 标签配对")
    if not issues:
        print("    OK  全部标签平衡")
    else:
        failed = True
        for t, o, c in issues:
            print("    MISMATCH  <{}>: open={} close={} (差 {})".format(t, o, c, o - c))

    # 2. 误闭合模式
    hits = check_bad_close(html)
    print("\n[2] 误闭合模式检测")
    if not hits:
        print("    OK  未发现 div 误用 </p> 闭合")
    else:
        failed = True
        for line, desc, snippet in hits:
            print("    第 {} 行  {}: {}".format(line, desc, snippet))

    # 3. 分段定位
    sec = check_by_section(html)
    print("\n[3] 按章节定位不平衡")
    net_div = sum(o - c for _, o, c, _, _ in sec)
    net_p = sum(po - pc for _, _, _, po, pc in sec)
    if not sec:
        print("    OK  各章节 div/p 均平衡")
    elif net_div == 0 and net_p == 0 and not check_tags(html):
        # 常见于外层 wrap 在头部开、在末节闭：章节间互相抵消，总数平衡
        print("    OK  各章节自平衡（存在跨节闭合，已确认总数平衡）")
        for cur, o, c, po, pc in sec:
            print("        注：「{}」div {}/{}  p {}/{}（跨节闭合，正常）".format(
                cur, o, c, po, pc))
    else:
        for cur, o, c, po, pc in sec:
            print("    「{}」  div {}/{}   p {}/{}".format(cur, o, c, po, pc))
        print("    提示：净差额 div={} p={}，若不为 0 见 [1]".format(net_div, net_p))

    # 4. 图表容器
    divs, inits, missing, orphan = check_charts(html)
    print("\n[4] ECharts 容器")
    print("    容器 {} 个，init {} 个".format(len(divs), len(inits)))
    if missing:
        failed = True
        print("    MISMATCH  init 了但无容器: {}".format(missing))
    if orphan:
        failed = True
        print("    MISMATCH  有容器但未 init: {}".format(orphan))
    if not missing and not orphan:
        print("    OK  一一对应")

    # 5. JS 语法
    print("\n[5] 内联 JS 语法")
    if args.no_js:
        print("    已跳过")
    else:
        node = args.node
        if not node:
            for cand in ["node", "node.exe"]:
                r = subprocess.run(["where", cand] if os.name == "nt" else ["which", cand],
                                   capture_output=True, text=True)
                if r.returncode == 0:
                    node = r.stdout.strip().splitlines()[0]
                    break
        if not node or not os.path.exists(node):
            print("    跳过：未找到 node。可用 --node 指定路径")
            print("    参考路径：~/.workbuddy/binaries/node/versions/<ver>/node.exe")
        else:
            ok, msg = check_js(html, node)
            if ok is None:
                print("    {}".format(msg))
            elif ok:
                print("    OK  {}".format(msg))
            else:
                failed = True
                print("    SYNTAX ERROR\n{}".format(msg))

    print("\n" + "=" * 62)
    if failed:
        print("结果：存在问题，修复后再交付")
        return 1
    print("结果：全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
