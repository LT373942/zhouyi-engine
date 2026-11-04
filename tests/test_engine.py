# -*- coding: utf-8 -*-
"""引擎单元测试：19 项，覆盖卦名表、算子代数性质、验算三态、传导闭包、统计函数。"""

import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from yijing.hexagram import (OPS, cuo, zong, hu, hexagram_name, hamming,
                             full_match, repair_set)
from yijing import engine
from yijing.metrics import stouffer, zscore

QIAN = [1, 1, 1, 1, 1, 1]
KUN = [0, 0, 0, 0, 0, 0]
YI = [1, 0, 0, 0, 0, 1]       # 颐
ZHONGFU = [1, 1, 0, 0, 1, 1]  # 中孚
TAI = [1, 1, 1, 0, 0, 0]      # 泰
PI = [0, 0, 0, 1, 1, 1]       # 否
BI = [0, 0, 0, 0, 1, 0]       # 比


def mk_case(entities, relations=None, deps=None, seeds=None, fracture=None):
    return {"case": "测试", "dims": [{}] * 6, "entities": entities,
            "relations": relations or [], "dependencies": deps or [],
            "seeds": seeds or [], "fracture": fracture or []}


def ent(eid, lines):
    m = {1: "yang", 0: "yin", None: "none"}
    return {"id": eid, "name": eid, "values": [m[x] for x in lines]}


class TestHexagram(unittest.TestCase):
    def test_01_name_qian_kun(self):
        self.assertEqual(hexagram_name(QIAN), "乾")
        self.assertEqual(hexagram_name(KUN), "坤")

    def test_02_name_yi(self):
        self.assertEqual(hexagram_name(YI), "颐")

    def test_03_name_zhongfu(self):
        self.assertEqual(hexagram_name(ZHONGFU), "中孚")

    def test_04_name_tai_pi(self):
        self.assertEqual(hexagram_name(TAI), "泰")
        self.assertEqual(hexagram_name(PI), "否")

    def test_05_name_bi(self):
        self.assertEqual(hexagram_name(BI), "比")

    def test_06_name_requires_full(self):
        with self.assertRaises(ValueError):
            hexagram_name([1, 0, None, 0, 0, 1])

    def test_07_cuo_involution(self):
        self.assertEqual(cuo(cuo(YI)), YI)

    def test_08_cuo_qian_kun(self):
        self.assertEqual(cuo(QIAN), KUN)

    def test_09_zong_involution(self):
        self.assertEqual(zong(zong(ZHONGFU)), ZHONGFU)

    def test_10_zong_tai_pi(self):
        self.assertEqual(zong(TAI), PI)

    def test_11_hu_yi_is_kun(self):
        self.assertEqual(hu(YI), KUN)

    def test_12_hu_zhongfu_is_yi(self):
        self.assertEqual(hu(ZHONGFU), YI)

    def test_13_hu_not_involutive(self):
        # 互卦一般不对合：hu(hu(乾)) = 乾 属特例，取中孚验证非对合
        self.assertNotEqual(hu(hu(ZHONGFU)), ZHONGFU)

    def test_14_none_preserved(self):
        x = [1, None, 0, 0, None, 1]
        self.assertEqual(cuo(x), [0, None, 1, 1, None, 0])


class TestEngine(unittest.TestCase):
    def test_15_audit_three_states(self):
        case = mk_case(
            [ent("A", QIAN), ent("B", KUN), ent("C", [0, 0, 0, 0, 0, 1]),
             ent("D", [0, 0, 1, 1, 0, 1])],
            relations=[{"a": "A", "op": "错", "b": "B"},   # 一致
                       {"a": "A", "op": "错", "b": "C"},   # 应变（差1爻）
                       {"a": "A", "op": "错", "b": "D"}])  # 断裂（差2爻以上）
        states = [r["state"] for r in engine.audit(case)]
        self.assertEqual(states, ["一致", "应变", "断裂"])

    def test_16_repair_set_minimal(self):
        case = mk_case([ent("A", QIAN), ent("C", [0, 0, 0, 0, 0, 1])],
                       relations=[{"a": "A", "op": "错", "b": "C"}])
        r = engine.audit(case)[0]
        self.assertEqual(r["repair"], [6])

    def test_17_cascade_closure(self):
        case = mk_case([ent(x, QIAN) for x in "ABCDEF"],
                       deps=[["B", "A"], ["C", "A"], ["D", "B"], ["E", "F"]],
                       seeds=["A"])
        res = engine.cascade(case)
        self.assertEqual(set(res["closure"]), {"A", "B", "C", "D"})
        self.assertEqual(res["rounds"][0], ["B", "C"])
        self.assertEqual(res["rounds"][1], ["D"])

    def test_18_discover_excludes_declared_and_dedupes(self):
        case = mk_case([ent("A", QIAN), ent("B", KUN), ent("C", YI)],
                       relations=[{"a": "C", "op": "互", "b": "B"}])
        found = engine.discover(case)
        pairs = {(r["a"], r["op"], r["b"]) for r in found}
        # 乾错坤对称去重后只出现一次
        self.assertEqual(sum(1 for r in found if r["op"] == "错"), 1)
        # 已声明的 C—互—B 不再出现
        self.assertNotIn(("C", "互", "B"), pairs)


class TestMetrics(unittest.TestCase):
    def test_19_stouffer(self):
        self.assertAlmostEqual(stouffer([2.0, 2.0, 2.0]), 6.0 / math.sqrt(3))
        self.assertAlmostEqual(zscore(3.0, [1.0, 2.0, 3.0, 4.0, 5.0]), 0.0)


if __name__ == "__main__":
    unittest.main()
