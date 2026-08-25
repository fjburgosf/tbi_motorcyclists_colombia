# -*- coding: utf-8 -*-
"""
Renumber in-text citations and the reference list by order of first appearance.

Converts e.g. [37-39] ... [11] ... into [1] ... [2] ... and reorders the
reference list so that entry [n] is the n-th reference first cited in the text.
"""
import re
from pathlib import Path

P = Path(r"D:/ACADEMICO/Papers/TBI_data_analysis/manuscript/manuscript_safety_final_EN.md")

data = P.read_bytes().decode("utf-8")  # preserves CRLF
REF_MARKER = "## References"
idx = data.find(REF_MARKER)
body = data[:idx]
refs_text = data[idx:]

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


# ---- 1. extract citations in order of appearance
ordered = []
citation_tokens = []
for m in CITE_RE.finditer(body):
    t = m.group(0)
    inner = t[1:-1]
    if NUM_ONLY.fullmatch(inner):
        nums = parse_nums(inner)
        citation_tokens.append((t, nums))
        for n in nums:
            if n not in ordered:
                ordered.append(n)

mapping = {old: i + 1 for i, old in enumerate(ordered)}

# ---- 2. parse the reference list
ref_entries = {}
for line in refs_text.splitlines():
    m = re.match(r"^(\d+)\.\s+(.*)$", line)
    if m:
        ref_entries[int(m.group(1))] = m.group(2)

list_nums = sorted(ref_entries.keys())

# ---- 3. sanity checks
uncited = [n for n in list_nums if n not in mapping]
missing = [n for n in ordered if n not in ref_entries]
ok = (
    len(ordered) == len(list_nums) == 48
    and not uncited
    and not missing
    and set(ordered) == set(list_nums)
)

print("distinct cited refs:", len(ordered))
print("reference-list entries:", len(list_nums))
print("uncited (in list, never cited):", uncited)
print("cited but missing from list:", missing)
print("checks passed:", ok)
if not ok:
    raise SystemExit("ABORT: citation/ref-list mismatch, no file written.")


def render_nums(nums):
    nums = sorted(set(nums))
    parts = []
    i = 0
    while i < len(nums):
        j = i
        while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
            j += 1
        if j - i + 1 >= 3:
            parts.append("%d\u2013%d" % (nums[i], nums[j]))
        else:
            parts.extend(str(n) for n in nums[i:j + 1])
        i = j + 1
    return ",".join(parts)


def remap(m):
    t = m.group(0)
    inner = t[1:-1]
    if NUM_ONLY.fullmatch(inner):
        nums = parse_nums(inner)
        return "[" + render_nums([mapping[n] for n in nums]) + "]"
    return t


body_new = CITE_RE.sub(remap, body)

# ---- 4. reorder the reference list
out = ["## References", ""]
for new_no, old in enumerate(ordered, start=1):
    out.append("%d. %s" % (new_no, ref_entries[old]))
    out.append("")
refs_new = "\r\n".join(out).rstrip("\r\n") + "\r\n"

final = body_new + refs_new
P.write_bytes(final.encode("utf-8"))

# ---- 5. report
print("\nOLD -> NEW (order of appearance):")
for old, new in mapping.items():
    print("  %2d -> %2d" % (old, new))

print("\nIn-text citations rewritten:")
for t, nums in citation_tokens:
    new_nums = sorted(set(mapping[n] for n in nums))
    print("  %-16s -> [%s]" % (t, render_nums(new_nums)))

print("\nNew reference list order (old numbers):", ordered)
print("Done.")
