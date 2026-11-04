# -*- coding: utf-8 -*-
"""命令行入口：
  python -m yijing.cli gua      cases/supply_chain.json
  python -m yijing.cli audit    cases/supply_chain.json
  python -m yijing.cli discover cases/supply_chain.json
  python -m yijing.cli cascade  cases/supply_chain.json [--seed S18]
  python -m yijing.cli profile  cases/supply_chain.json
  python -m yijing.cli backtest cases/supply_chain.json [--n 1000]
"""

import argparse
import json
import sys

from . import engine
from .metrics import backtest


def main(argv=None):
    ap = argparse.ArgumentParser(prog="yijing")
    ap.add_argument("cmd", choices=["gua", "audit", "discover", "cascade", "profile", "backtest"])
    ap.add_argument("case")
    ap.add_argument("--seed", action="append", default=None)
    ap.add_argument("--n", type=int, default=1000)
    args = ap.parse_args(argv)

    case = engine.load_case(args.case)

    if args.cmd == "gua":
        names = engine.gua_names(case)
        for e in case["entities"]:
            g = engine.hang_gua(e)
            print(f"{e['id']} {e['name']} -> 卦={names[e['id']]}  lines={g}")
    elif args.cmd == "audit":
        for r in engine.audit(case):
            print(f"[{r['state']}] {r['a']} —{r['op']}— {r['b']}  差={r['distance']}  修复={r['repair']}")
    elif args.cmd == "discover":
        found = engine.discover(case)
        print(f"结构机会：{len(found)} 条")
        for r in found:
            print(f"  {r['a']} —{r['op']}— {r['b']}")
    elif args.cmd == "cascade":
        res = engine.cascade(case, args.seed)
        print(f"波及闭包：{len(res['closure'])} 实体 -> {sorted(res['closure'])}")
        for i, rd in enumerate(res["rounds"], 1):
            print(f"  第{i}轮: {', '.join(rd)}")
    elif args.cmd == "profile":
        p = engine.profile(case)
        for eid, d in p["entities"].items():
            print(f"{eid}: 依赖他人={d['depends_on']} 被依赖={d['depended_by']} 波及规模={d['closure_size']}")
        print(f"案例传导性画像 T = {p['T']}")
    elif args.cmd == "backtest":
        res = backtest(case, n=args.n)
        print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
