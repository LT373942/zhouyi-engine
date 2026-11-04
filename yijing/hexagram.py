# -*- coding: utf-8 -*-
"""卦象系统：六爻编码、八卦/六十四卦名表、错综互三算子。

约定：lines 为长度 6 的列表，索引 0 为初爻（最下），索引 5 为上爻（最上）。
取值：1=阳，0=阴，None=未定爻（未裁决的部分知识）。
"""

# 八卦：bottom-to-top 三爻 -> 卦名
TRIGRAMS = {
    (1, 1, 1): "乾", (1, 1, 0): "兑", (1, 0, 1): "离", (1, 0, 0): "震",
    (0, 1, 1): "巽", (0, 1, 0): "坎", (0, 0, 1): "艮", (0, 0, 0): "坤",
}

TRI_ORDER = ["乾", "兑", "离", "震", "巽", "坎", "艮", "坤"]

# 六十四卦名表：HEX_MATRIX[下卦][上卦在 TRI_ORDER 中的序号]
HEX_MATRIX = {
    "乾": ["乾", "夬", "大有", "大壮", "小畜", "需", "大畜", "泰"],
    "兑": ["履", "兑", "睽", "归妹", "中孚", "节", "损", "临"],
    "离": ["同人", "革", "离", "丰", "家人", "既济", "贲", "明夷"],
    "震": ["无妄", "随", "噬嗑", "震", "益", "屯", "颐", "复"],
    "巽": ["姤", "大过", "鼎", "恒", "巽", "井", "蛊", "升"],
    "坎": ["讼", "困", "未济", "解", "涣", "坎", "蒙", "师"],
    "艮": ["遁", "咸", "旅", "小过", "渐", "蹇", "艮", "谦"],
    "坤": ["否", "萃", "晋", "豫", "观", "比", "剥", "坤"],
}


def trigram_name(lines3):
    """三爻（bottom-to-top）-> 八卦名。"""
    return TRIGRAMS[tuple(lines3)]


def hexagram_name(lines):
    """六爻 -> 六十四卦名。要求六爻全部已定（无 None）。"""
    if any(x is None for x in lines):
        raise ValueError("含未定爻，无法定卦名")
    lower = trigram_name(lines[0:3])
    upper = trigram_name(lines[3:6])
    return HEX_MATRIX[lower][TRI_ORDER.index(upper)]


def cuo(lines):
    """错卦：逐爻取反（完全对立）。对合：cuo∘cuo = id。None 保持 None。"""
    return [None if x is None else 1 - x for x in lines]


def zong(lines):
    """综卦：六爻倒置（立场镜像）。对合：zong∘zong = id。"""
    return list(reversed(lines))


def hu(lines):
    """互卦：取二三四爻为下卦、三四五爻为上卦（内在牵连）。一般不对合。"""
    return [lines[1], lines[2], lines[3], lines[2], lines[3], lines[4]]


OPS = {"错": cuo, "综": zong, "互": hu}


def hamming(a, b):
    """双侧已定位置上的汉明距离。无重叠已定位置时返回 None（未裁决）。"""
    pairs = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
    if not pairs:
        return None
    return sum(1 for x, y in pairs if x != y)


def full_match(a, b):
    """六位全部已定且逐位相等。"""
    return all(x is not None and y is not None and x == y for x, y in zip(a, b))


def repair_set(a, b):
    """最小修复集：使 a 变为 b 所需翻转的爻位（1-based，仅计双侧已定的不一致位）。"""
    return [i + 1 for i, (x, y) in enumerate(zip(a, b))
            if x is not None and y is not None and x != y]
