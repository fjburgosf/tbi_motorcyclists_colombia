# -*- coding: utf-8 -*-
"""
Verify integrity / coherence / correct matching of in-text citations vs the
reference list (self-contained, no git dependency).

Checks:
  1. Every in-text citation number is in 1..48.
  2. First-appearance order is exactly 1,2,...,48 (order-of-appearance numbering).
  3. Reference list has exactly 48 entries numbered 1..48.
  4. Bijection: every reference is cited at least once; every cited number has an entry.
  5. Semantic cross-reference: for each [n], the reference title must be topically
     consistent with the sentence(s) that cite it (keyword-overlap heuristic).
  6. The .docx citation set matches the .md citation set.
"""
import re
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
MD = BASE / "manuscript" / "manuscript_safety_final_EN.md"
DOCX = BASE / "manuscript" / "manuscript_safety_final_EN.docx"

cur = MD.read_bytes().decode("utf-8")

DASH_CLASS = "[\u2013\u2014-]"
CITE_RE = re.compile(r"\[[^\]]*\]")
NUM_ONLY = re.compile(r"[\d,\s\u2013\u2014-]+")
RANGE_RE = re.compile(r"^(\d+)%s(\d+)$" % DASH_CLASS)


def parse_nums(inner):
    nums = []
    for part in re.split(r"[,\s]+", inner.strip()):
        if not part:
            continue
        m = RANGE_RE.match(part)
        if m:
            nums.extend(range(int(m.group(1)), int(m.group(2)) + 1))
        elif part.isdigit():
            nums.append(int(part))
        else:
            raise ValueError("unparsed part %r" % part)
    return nums


def extract_citations(text):
    """Return list of (token, [nums], start_pos) in order of appearance."""
    out = []
    for m in CITE_RE.finditer(text):
        t = m.group(0)
        inner = t[1:-1]
        if NUM_ONLY.fullmatch(inner):
            out.append((t, parse_nums(inner), m.start()))
    return out


def extract_refs(text):
    refs = {}
    idx = text.find("## References")
    for line in text[idx:].splitlines():
        m = re.match(r"^(\d+)\.\s+(.*)$", line)
        if m:
            refs[int(m.group(1))] = m.group(2)
    return refs


body = cur[: cur.find("## References")]
cits = extract_citations(cur)          # citations are all in the body
refs = extract_refs(cur)

errors = []
warnings = []

# 1 & 2: numbers in range + first-appearance order
first_appearance = []
for t, nums, _pos in cits:
    for n in nums:
        if not (1 <= n <= 48):
            errors.append("out-of-range citation %d in %s" % (n, t))
        if n not in first_appearance:
            first_appearance.append(n)

if first_appearance != list(range(1, 49)):
    errors.append("first-appearance order != 1..48: %s" % first_appearance)

# 3: reference list exactly 1..48
if sorted(refs) != list(range(1, 49)):
    errors.append("reference list keys != 1..48")

# 4: bijection
text_cited = set(first_appearance)
list_nums = set(refs)
if text_cited - list_nums:
    errors.append("cited but missing from list: %s" % sorted(text_cited - list_nums))
if list_nums - text_cited:
    errors.append("in list but never cited: %s" % sorted(list_nums - text_cited))

# 5: semantic cross-reference (keyword overlap title vs citing context)
STOP = set("the a an of in on for and or to with by from et al into using among across as is are was were be been than that this these those their its".split())


def sig_words(s):
    return {w.lower() for w in re.findall(r"[A-Za-z\u00c0-\u024f]{4,}", s) if w.lower() not in STOP}


def first_context(num):
    """Return ~150-char window around the first citation of `num`."""
    for t, nums, pos in cits:
        if num in nums:
            lo = max(0, pos - 90)
            hi = min(len(body), pos + len(t) + 60)
            return body[lo:hi].replace("\r", " ").replace("\n", " ")
    return ""


sem_table = []
for n in range(1, 49):
    title = refs[n]
    ctx = first_context(n)
    tw = sig_words(title)
    cw = sig_words(ctx)
    overlap = tw & cw
    sem_table.append((n, title, ctx, overlap))

for n, title, ctx, overlap in sem_table:
    if not overlap:
        warnings.append("no keyword overlap for [%d]: %s" % (n, title[:70]))

print("citation tokens:", len(cits))
print("distinct cited refs:", len(first_appearance))
print("reference-list entries:", len(refs))
print("first-appearance order is 1..48:", first_appearance == list(range(1, 49)))

if errors:
    print("\nERRORS (%d):" % len(errors))
    for e in errors:
        print("  -", e)
    raise SystemExit(1)

print("\nSTRUCTURAL CHECKS PASSED (integrity + coherence).\n")

print("=== SEMANTIC CROSS-REFERENCE (reference vs first-citing context) ===")
for n, title, ctx, overlap in sem_table:
    flag = "" if overlap else "  <-- CHECK"
    print("[%2d] %s" % (n, title[:78]))
    print("     ctx: %s%s" % (ctx[:110], flag))

if warnings:
    print("\nWARNINGS:")
    for w in warnings:
        print("  -", w)

# 6: docx consistency
from docx import Document  # noqa: E402
d = Document(str(DOCX))
docx_text = "\n".join(p.text for p in d.paragraphs)
docx_cits = extract_citations(docx_text)
md_tokens = [t for t, _n, _p in cits]
dx_tokens = [t for t, _n, _p in docx_cits]
print("\n=== DOCX vs MD ===")
print("md citation tokens:", len(md_tokens))
print("docx citation tokens:", len(dx_tokens))
print("token sets identical:", sorted(set(md_tokens)) == sorted(set(dx_tokens)))
