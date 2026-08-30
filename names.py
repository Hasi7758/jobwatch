"""
公司名匹配。

难点:同一家公司在招聘信息里和在 IG Metall 名单里写法常常不一样。
    "Knorr-Bremse AG"  vs  "Knorr Bremse Systeme für Nutzfahrzeuge GmbH"
    "MAN Truck & Bus"  vs  "MAN Truck und Bus SE"
    "Krauss-Maffei"    vs  "KraussMaffei Technologies GmbH"
所以要先剥掉法律后缀和噪音词,再做多级匹配。
"""

import re
import unicodedata
from difflib import SequenceMatcher

# 德语公司名里的法律形式和通用词,匹配时一律剥掉
NOISE = {
    "gmbh", "ag", "kg", "kgaa", "se", "mbh", "ohg", "gbr", "ug", "ev", "eg",
    "co", "cokg", "gmbhcokg", "holding", "group", "gruppe", "deutschland",
    "germany", "international", "global", "europe", "europa", "und", "and",
    "the", "werk", "werke", "niederlassung", "zweigniederlassung",
    "verwaltung", "verwaltungs", "beteiligungs", "beteiligungen",
    "systeme", "systems", "technologies", "technologie", "technik",
    "industrie", "industries", "solutions", "services", "service",
    "produktion", "produktions", "manufacturing", "automotive",
}

UMLAUT = {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss",
          "Ä": "ae", "Ö": "oe", "Ü": "ue"}


def fold(s: str) -> str:
    """德语字符归一:ä->ae, ß->ss,再去掉其余变音符号。"""
    s = s or ""
    for k, v in UMLAUT.items():
        s = s.replace(k, v)
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c))


def tokens(name: str):
    """切成有意义的词,剥掉法律形式。"""
    s = fold(name).lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    out = [t for t in s.split() if t and t not in NOISE and not t.isdigit()]
    return out


def normalize(name: str) -> str:
    """归一化成一个可直接比较的字符串。"""
    return "".join(tokens(name))


def core_tokens(name: str):
    """长度 >=4 的实词,用来防止 'six' 误配 'sixt' 这类短词事故。"""
    return {t for t in tokens(name) if len(t) >= 4}


class NameMatcher:
    """把职位里的公司名匹配到白名单上的某一家。"""

    def __init__(self, names, aliases=None, threshold=0.88):
        """
        names   : 白名单公司名
        aliases : {别名: 白名单上的正式名},用于缩写等算法搞不定的情况,
                  例如 {"Bayerische Motoren Werke": "BMW AG"}
        """
        self.threshold = threshold
        self.entries = []          # (对外返回的名字, normalized, core_token集合)
        self.by_norm = {}

        def add(display, source):
            nm = normalize(source)
            if not nm:
                return
            self.entries.append((display, nm, core_tokens(source)))
            self.by_norm.setdefault(nm, display)

        for n in names:
            if n and str(n).strip():
                add(str(n).strip(), str(n).strip())

        for alias, canonical in (aliases or {}).items():
            if alias and canonical:
                add(str(canonical).strip(), str(alias).strip())

    def __len__(self):
        return len(self.entries)

    def match(self, query: str):
        """返回 (白名单原名, 匹配方式) 或 None。"""
        if not query or not str(query).strip():
            return None
        q = str(query).strip()
        qn = normalize(q)
        if not qn:
            return None

        # 1) 归一化后完全相同
        if qn in self.by_norm:
            return (self.by_norm[qn], "exact")

        qc = core_tokens(q)
        qt = set(tokens(q))

        # 2a) 白名单公司名本身就是查询里的一个完整词。
        #     处理短名字 + 后缀噪音:"BMW AG" vs "BMW Group Werk München"。
        #     要求是完整词而非任意子串,免得 "man" 撞上 "management"。
        for orig, nm, ct in self.entries:
            if len(nm) >= 3 and (nm in qt or (len(qt) == 1 and nm == qn)):
                return (orig, "token")

        # 2b) 一方是另一方的子串
        for orig, nm, ct in self.entries:
            if len(nm) >= 5 and len(qn) >= 5 and (nm in qn or qn in nm):
                # 要求至少共享一个实词,避免纯字符串巧合
                if not qc or not ct or (qc & ct):
                    return (orig, "substring")

        # 3) 实词重合度(处理词序不同、多余修饰词)
        best, best_score = None, 0.0
        for orig, nm, ct in self.entries:
            if not ct or not qc:
                continue
            inter = qc & ct
            if not inter:
                continue
            score = len(inter) / min(len(qc), len(ct))
            if score > best_score:
                best, best_score = orig, score
        if best and best_score >= 0.75:
            return (best, f"tokens {best_score:.2f}")

        # 4) 整体字符串相似度兜底
        best, best_score = None, 0.0
        for orig, nm, ct in self.entries:
            if abs(len(nm) - len(qn)) > 12:
                continue
            r = SequenceMatcher(None, qn, nm).ratio()
            if r > best_score:
                best, best_score = orig, r
        if best and best_score >= self.threshold:
            return (best, f"fuzzy {best_score:.2f}")

        return None


def slug_candidates(name: str):
    """由公司名猜 ATS slug,喂给 discover 命令。"""
    ts = tokens(name)
    if not ts:
        return []
    cands = ["".join(ts)]
    if len(ts) > 1:
        cands.append("-".join(ts))
        cands.append(ts[0])
        cands.append("".join(ts[:2]))
    seen, out = set(), []
    for c in cands:
        c = c.strip("-")
        if len(c) >= 3 and c not in seen:
            seen.add(c)
            out.append(c)
    return out[:4]
