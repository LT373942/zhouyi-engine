# -*- coding: utf-8 -*-
"""机械引擎：挂卦、验算（audit）、结构机会发现（discover）、叙事传导（cascade）、画像（profile）。

案例 JSON 结构：
{
  "case": "案例名",
  "dims": [{"name": "...", "yang": "阳爻取值含义", "yin": "阴爻取值含义"}, ...],   # 恰 6 项
  "entities": [{"id": "S1", "name": "...", "values": ["yang","yin","none",...]}, ...],
  "relations": [{"a": "S2", "op": "互", "b": "S5"}, ...],       # 已声明关系
  "dependencies": [["h", "t"], ...],                            # h 依赖 t
  "seeds": ["S18", ...],                                        # 事件受击种子
  "fracture": ["S2", ...]                                       # 真实断裂集（事后事实）
}
"""

import json
from .hexagram import OPS, hexagram_name, hamming, full_match, repair_set


def load_case(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def hang_gua(entity):
    """算法1 挂卦：实体六维属性 -> 六爻向量。"""
    m = {"yang": 1, "yin": 0, "none": None}
    return [m[v] for v in entity["values"]]


def gua_map(case):
    return {e["id"]: hang_gua(e) for e in case["entities"]}


def gua_names(case):
    gmap = gua_map(case)
    names = {}
    for eid, lines in gmap.items():
        names[eid] = hexagram_name(lines) if all(x is not None for x in lines) else None
    return names


def audit(case):
    """验算已声明关系。输出三态：一致（差0爻）/应变（差1爻）/断裂（差≥2爻），附最小修复集。"""
    gmap = gua_map(case)
    out = []
    for r in case.get("relations", []):
        expected = OPS[r["op"]](gmap[r["a"]])
        actual = gmap[r["b"]]
        d = hamming(expected, actual)
        if d is None:
            state = "未裁决"
        elif d == 0:
            state = "一致"
        elif d == 1:
            state = "应变"
        else:
            state = "断裂"
        out.append({"a": r["a"], "op": r["op"], "b": r["b"],
                    "state": state, "distance": d,
                    "repair": repair_set(expected, actual)})
    return out


def discover(case):
    """枚举卦象上成立但未声明的关系（结构机会）。

    错/综为对称关系，按无序对去重；互为非对称（内核抽取），保留方向。
    """
    gmap = gua_map(case)
    declared = set()
    for r in case.get("relations", []):
        declared.add((r["a"], r["op"], r["b"]))
    found = []
    seen_sym = set()
    ids = [e["id"] for e in case["entities"]]
    for a in ids:
        for op_name, op in OPS.items():
            img = op(gmap[a])
            for b in ids:
                if a == b:
                    continue
                if not full_match(img, gmap[b]):
                    continue
                if (a, op_name, b) in declared:
                    continue
                if op_name in ("错", "综"):
                    key = (op_name, frozenset((a, b)))
                    if key in seen_sym:
                        continue
                    seen_sym.add(key)
                found.append({"a": a, "op": op_name, "b": b})
    return found


def cascade(case, seeds=None):
    """算法2 叙事传导：依赖级联闭包。h 依赖 t；t 受击则 h 波及。

    返回 {"closure": [...], "rounds": [[第1轮波及...], ...]}，closure 含种子。
    """
    deps = case.get("dependencies", [])
    affected = list(seeds if seeds is not None else case.get("seeds", []))
    frontier = list(affected)
    rounds = []
    while frontier:
        nxt = []
        for h, t in deps:
            if t in frontier and h not in affected:
                affected.append(h)
                nxt.append(h)
        if nxt:
            rounds.append(sorted(set(nxt)))
        frontier = nxt
    return {"closure": affected, "rounds": rounds}


def clusters(case, min_size=3):
    """同构群：同卦实体簇（仅计六爻全定的实体）。"""
    names = gua_names(case)
    groups = {}
    for eid, name in names.items():
        if name is not None:
            groups.setdefault(name, []).append(eid)
    return {g: sorted(v) for g, v in groups.items() if len(v) >= min_size}


def profile(case):
    """传导性画像：每实体的依赖入/出度与作为种子的波及规模；案例级 T = 断裂集中可被传导解释的比例。"""
    deps = case.get("dependencies", [])
    indeg, outdeg = {}, {}
    for h, t in deps:
        outdeg[h] = outdeg.get(h, 0) + 1
        indeg[t] = indeg.get(t, 0) + 1
    per = {}
    for e in case["entities"]:
        eid = e["id"]
        clo = cascade(case, [eid])["closure"]
        per[eid] = {"depends_on": outdeg.get(eid, 0),
                    "depended_by": indeg.get(eid, 0),
                    "closure_size": len(clo) - 1}
    fracture = set(case.get("fracture", []))
    clo = set(cascade(case)["closure"])
    t_ratio = len(fracture & clo) / len(fracture) if fracture else None
    return {"entities": per, "T": t_ratio}
