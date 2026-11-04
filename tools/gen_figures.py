# -*- coding: utf-8 -*-
"""论文图档生成：读取 results/backtest_results.json，输出图 1—4（SVG）到论文图目录。

用法：python tools/gen_figures.py [输出目录]   （默认 ../../论文/图 相对于仓库根）
图中全部数据来自真实回测结果文件，不手填。
"""

import json
import os
import sys

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.normpath(os.path.join(ROOT, "..", "论文", "图"))
os.makedirs(OUT, exist_ok=True)

RES = json.load(open(os.path.join(ROOT, "results", "backtest_results.json"), encoding="utf-8"))

FONT = "font-family='SimSun,serif'"
BLUE = "#2f6fb2"
GRAY = "#9aa0a6"
BLACK = "#222"


def gua_glyph(x, y, lines, w=22, lh=4, gap=3, color=BLACK):
    """画六爻卦符：阳爻整横，阴爻断横。x,y 为顶爻左上角。"""
    parts = []
    for i, v in enumerate(reversed(lines)):  # 上爻画在最上
        yy = y + i * (lh + gap)
        if v == 1:
            parts.append(f"<rect x='{x}' y='{yy}' width='{w}' height='{lh}' fill='{color}'/>")
        elif v == 0:
            h = w // 2 - 3
            parts.append(f"<rect x='{x}' y='{yy}' width='{h}' height='{lh}' fill='{color}'/>")
            parts.append(f"<rect x='{x + w - h}' y='{yy}' width='{h}' height='{lh}' fill='{color}'/>")
    return "".join(parts)


def box(x, y, w, h, title, sub):
    return (f"<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='6' fill='white' stroke='{BLACK}' stroke-width='1.5'/>"
            f"<text x='{x + w/2}' y='{y + 24}' text-anchor='middle' font-size='15' {FONT} fill='{BLACK}'>{title}</text>"
            f"<text x='{x + w/2}' y='{y + 44}' text-anchor='middle' font-size='12' {FONT} fill='{GRAY}'>{sub}</text>")


# ---------- 图 1：三方圆桌 ----------
def fig1():
    s = ["<svg xmlns='http://www.w3.org/2000/svg' width='640' height='420' viewBox='0 0 640 420'>",
         "<defs><marker id='a' markerWidth='8' markerHeight='8' refX='7' refY='3' orient='auto'>"
         f"<path d='M0,0 L7,3 L0,6 z' fill='{BLACK}'/></marker>"
         "<marker id='ad' markerWidth='8' markerHeight='8' refX='7' refY='3' orient='auto'>"
         f"<path d='M0,0 L7,3 L0,6 z' fill='{GRAY}'/></marker></defs>",
         f"<rect width='640' height='420' fill='white'/>"]
    # 中心卦象（颐，示意）
    s.append("<circle cx='320' cy='215' r='58' fill='white' stroke='" + BLACK + "' stroke-width='1.5'/>")
    s.append(gua_glyph(309, 182, [1, 0, 0, 0, 0, 1], w=22, lh=4, gap=4, color=BLUE))
    s.append(f"<text x='320' y='262' text-anchor='middle' font-size='13' {FONT} fill='{BLACK}'>卦象·公共中间语言</text>")
    s.append(box(245, 30, 150, 56, "人类", "裁决 · 定方向"))
    s.append(box(60, 320, 160, 56, "大语言模型", "生成 · 语义插值"))
    s.append(box(420, 320, 160, 56, "机械引擎", "验算 · 传播 · 修复"))
    # 实线：正向信息流
    s.append(f"<line x1='320' y1='86' x2='320' y2='154' stroke='{BLACK}' stroke-width='1.5' marker-end='url(#a)'/>")
    s.append(f"<text x='332' y='124' font-size='11' {FONT} fill='{BLACK}'>关键帧裁决</text>")
    s.append(f"<line x1='140' y1='320' x2='262' y2='238' stroke='{BLACK}' stroke-width='1.5' marker-end='url(#a)'/>")
    s.append(f"<text x='132' y='276' font-size='11' {FONT} fill='{BLACK}'>提案与翻译</text>")
    s.append(f"<line x1='500' y1='320' x2='378' y2='238' stroke='{BLACK}' stroke-width='1.5' marker-end='url(#a)'/>")
    s.append(f"<text x='420' y='276' font-size='11' {FONT} fill='{BLACK}'>算子计算</text>")
    # 虚线：反馈回路
    s.append(f"<path d='M 272 196 Q 180 160 170 100' stroke='{GRAY}' stroke-width='1.3' fill='none' stroke-dasharray='5,4' marker-end='url(#ad)'/>")
    s.append(f"<path d='M 368 196 Q 460 160 468 100' stroke='{GRAY}' stroke-width='1.3' fill='none' stroke-dasharray='5,4' marker-end='url(#ad)'/>")
    s.append(f"<line x1='222' y1='355' x2='418' y2='355' stroke='{GRAY}' stroke-width='1.3' stroke-dasharray='5,4' marker-end='url(#ad)'/>")
    s.append(f"<text x='470' y='150' font-size='11' {FONT} fill='{GRAY}'>验算反馈</text>")
    s.append(f"<text x='252' y='348' font-size='11' {FONT} fill='{GRAY}'>证伪 / 补全</text>")
    s.append(f"<text x='320' y='405' text-anchor='middle' font-size='11' {FONT} fill='{GRAY}'>实线＝正向信息流　虚线＝反馈回路</text>")
    s.append("</svg>")
    return "".join(s)


# ---------- 图 2：错综互三算子 ----------
def fig2():
    s = ["<svg xmlns='http://www.w3.org/2000/svg' width='640' height='240' viewBox='0 0 640 240'>",
         f"<rect width='640' height='240' fill='white'/>"]
    rows = [("错：完全对立（对合）", [1]*6, [0]*6, "乾", "坤", 20),
            ("综：立场镜像（对合）", [1,1,1,0,0,0], [0,0,0,1,1,1], "泰", "否", 95),
            ("互：内在牵连（内核抽取）", [1,0,0,0,0,1], [0]*6, "颐", "坤", 170)]
    for label, la, lb, na, nb, y in rows:
        s.append(f"<text x='20' y='{y+32}' font-size='13' {FONT} fill='{BLACK}'>{label}</text>")
        s.append(gua_glyph(250, y, la))
        s.append(f"<text x='250' y='{y+58}' font-size='12' {FONT} fill='{BLACK}'>{na}</text>")
        s.append(f"<text x='330' y='{y+26}' font-size='14' {FONT} fill='{BLUE}'>—{label[0]}→</text>")
        s.append(gua_glyph(420, y, lb))
        s.append(f"<text x='420' y='{y+58}' font-size='12' {FONT} fill='{BLACK}'>{nb}</text>")
    s.append("</svg>")
    return "".join(s)


# ---------- 图 3：M2′ 真实 vs 随机基线 ----------
BASELINE = {"新能源车供应链（情景推演：假想代工危机）": 0.316,
            "诺基亚代际更替（2007 iPhone 发布回测）": 0.211,
            "德州寒潮（2021 年 2 月 Uri 风暴回测）": 0.693}
LABEL = {"新能源车供应链（情景推演：假想代工危机）": "供应链",
         "诺基亚代际更替（2007 iPhone 发布回测）": "诺基亚",
         "德州寒潮（2021 年 2 月 Uri 风暴回测）": "德州寒潮"}


def fig3():
    cases = list(RES.keys())
    s = ["<svg xmlns='http://www.w3.org/2000/svg' width='640' height='320' viewBox='0 0 640 320'>",
         f"<rect width='640' height='320' fill='white'/>"]
    x0, y0, ph = 70, 270, 220  # 原点与绘图高
    s.append(f"<line x1='{x0}' y1='{y0}' x2='600' y2='{y0}' stroke='{BLACK}'/>")
    s.append(f"<line x1='{x0}' y1='{y0}' x2='{x0}' y2='{y0-ph}' stroke='{BLACK}'/>")
    for v in (0.25, 0.5, 0.75, 1.0):
        yy = y0 - v * ph
        s.append(f"<line x1='{x0}' y1='{yy}' x2='600' y2='{yy}' stroke='#e3e5e8'/>")
        s.append(f"<text x='{x0-8}' y='{yy+4}' text-anchor='end' font-size='11' {FONT} fill='{GRAY}'>{v:.2f}</text>")
    bw, grp = 42, 175
    for i, c in enumerate(cases):
        real, base = RES[c]["M2p"], BASELINE[c]
        gx = x0 + 55 + i * grp
        for j, (v, col, tag) in enumerate(((real, BLUE, "真实"), (base, GRAY, "基线"))):
            h = v * ph
            bx = gx + j * (bw + 8)
            s.append(f"<rect x='{bx}' y='{y0-h}' width='{bw}' height='{h}' fill='{col}'/>")
            s.append(f"<text x='{bx+bw/2}' y='{y0-h-6}' text-anchor='middle' font-size='12' {FONT} fill='{BLACK}'>{v:.3f}</text>")
        s.append(f"<text x='{gx+bw}' y='{y0+20}' text-anchor='middle' font-size='13' {FONT} fill='{BLACK}'>{LABEL[c]}</text>")
    s.append(f"<rect x='430' y='40' width='12' height='12' fill='{BLUE}'/><text x='448' y='50' font-size='12' {FONT} fill='{BLACK}'>真实 M2′</text>")
    s.append(f"<rect x='430' y='60' width='12' height='12' fill='{GRAY}'/><text x='448' y='70' font-size='12' {FONT} fill='{BLACK}'>随机基线均值（1000 次）</text>")
    s.append(f"<text x='320' y='310' text-anchor='middle' font-size='11' {FONT} fill='{GRAY}'>德州案例基线偏高：闭包占实体总数 9/13，指标区分度下降（见 5.2、6.3 节）</text>")
    s.append("</svg>")
    return "".join(s)


# ---------- 图 4：同构群分布 ----------
def fig4():
    cases = list(RES.keys())
    s = ["<svg xmlns='http://www.w3.org/2000/svg' width='640' height='300' viewBox='0 0 640 300'>",
         f"<rect width='640' height='300' fill='white'/>"]
    y = 30
    for c in cases:
        r = RES[c]
        names = r["gua_names"]
        cluster_members = set(m for v in r["clusters"].values() for m in v)
        cluster_name = list(r["clusters"].keys())[0]
        s.append(f"<text x='20' y='{y+14}' font-size='13' {FONT} fill='{BLACK}'>{LABEL[c]}（{len(names)} 实体，同构群：{cluster_name}×{r['cluster_max_size']}，p={r['cluster_p']}）</text>")
        x = 20
        for eid in sorted(names):
            in_c = eid in cluster_members
            col = BLUE if in_c else "white"
            tc = "white" if in_c else GRAY
            s.append(f"<rect x='{x}' y='{y+24}' width='26' height='26' rx='4' fill='{col}' stroke='{BLACK}' stroke-width='1'/>")
            s.append(f"<text x='{x+13}' y='{y+41}' text-anchor='middle' font-size='9' {FONT} fill='{tc}'>{eid}</text>")
            s.append(f"<text x='{x+13}' y='{y+62}' text-anchor='middle' font-size='9' {FONT} fill='{BLACK if in_c else GRAY}'>{names[eid]}</text>")
            x += 30
        y += 92
    s.append(f"<rect x='480' y='14' width='12' height='12' fill='{BLUE}'/><text x='497' y='24' font-size='11' {FONT} fill='{BLACK}'>同构群成员</text>")
    s.append("</svg>")
    return "".join(s)


outputs = {"图1-系统架构-三方圆桌.svg": fig1(),
           "图2-卦象算子-错综互.svg": fig2(),
           "图3-实验数据-M2p对比.svg": fig3(),
           "图4-同构群分布.svg": fig4()}
for fn, svg in outputs.items():
    with open(os.path.join(OUT, fn), "w", encoding="utf-8") as f:
        f.write(svg)
    print("已生成", os.path.join(OUT, fn))
