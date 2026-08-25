# -*- coding: utf-8 -*-
"""
Verify the numeric order and in-text referencing of TABLES and FIGURES by
order of appearance in the manuscript.

Reports:
  * caption order (actual placement in the file)
  * first-appearance order in the body text
  * sequential-numbering check
  * every caption referenced? / every in-text reference has a caption?
"""
import re
from pathlib import Path

P = Path(r"D:/ACADEMICO/Papers/TBI_data_analysis/manuscript/manuscript_safety_final_EN.md")
lines = P.read_text(encoding="utf-8").splitlines()

CAP_RE = re.compile(r"^\*\*(Table|Figure)\s+([S]?\d+)\.\*\*")
REF_RE = re.compile(r"(?:Supplementary\s+)?(Table|Figure)\s+([S]?\d+)")

captions = []       # (type, label, line_no) in file order
references = []     # (type, label, line_no) in text order (excluding caption lines)

for ln_no, line in enumerate(lines, 1):
    s = line.strip()
    m = CAP_RE.match(s)
    if m:
        captions.append((m.group(1), m.group(2), ln_no))
        continue  # caption line: do not treat as in-text reference
    for r in REF_RE.finditer(line):
        references.append((r.group(1), r.group(2), ln_no))


def norm(t, n):
    return "%s %s" % (t, n)


cap_labels = [norm(t, n) for t, n, _ in captions]
ref_labels = [norm(t, n) for t, n, _ in references]

# first appearance order in text
first_appearance = []
for lab in ref_labels:
    if lab not in first_appearance:
        first_appearance.append(lab)

print("=== CAPTIONS (placement order in file) ===")
for t, n, ln in captions:
    print("  %-9s %-9s (line %d)" % (t, n, ln))

print("\n=== IN-TEXT REFERENCES (first-appearance order) ===")
for lab in first_appearance:
    print("  %s" % lab)

# sequential checks: main and supplementary sequences are numbered INDEPENDENTLY
GROUPS = [
    ("main tables",      ["Table 1", "Table 2", "Table 3"]),
    ("supplementary tables", ["Table S1", "Table S2", "Table S3", "Table S4"]),
    ("main figures",     ["Figure 1", "Figure 2", "Figure 3"]),
    ("supplementary figures", ["Figure S1"]),
]

errors = []

for gname, expected in GROUPS:
    text_seq = [l for l in first_appearance if l in expected]
    cap_seq = [l for l in cap_labels if l in expected]
    if text_seq != expected:
        errors.append("%s: text first-appearance order != expected -> %s" % (gname, text_seq))
    if cap_seq != expected:
        errors.append("%s: caption placement order != expected -> %s" % (gname, cap_seq))

# every caption referenced somewhere?
for lab in cap_labels:
    if lab not in ref_labels:
        errors.append("caption never referenced in text: %s" % lab)

# every in-text reference has a caption?
for lab in set(ref_labels):
    if lab not in cap_labels:
        errors.append("in-text reference without a caption: %s" % lab)

print("\n=== CHECKS ===")
for gname, expected in GROUPS:
    text_seq = [l for l in first_appearance if l in expected]
    cap_seq = [l for l in cap_labels if l in expected]
    print("  %-22s text: %s" % (gname, text_seq))
    print("  %-22s captions: %s" % ("", cap_seq))
print("total table captions:", len([l for l in cap_labels if l.startswith('Table')]),
      "| total figure captions:", len([l for l in cap_labels if l.startswith('Figure')]))
print("distinct table refs in text:", len(set(l for l in ref_labels if l.startswith('Table'))))
print("distinct figure refs in text:", len(set(l for l in ref_labels if l.startswith('Figure'))))

if errors:
    print("\nERRORS (%d):" % len(errors))
    for e in errors:
        print("  -", e)
    raise SystemExit(1)

print("\nALL CHECKS PASSED: table/figure numbering and referencing are consistent "
      "and ordered by first appearance (main and supplementary sequenced independently).")

# per-item reference count (how many times each is mentioned)
from collections import Counter
cnt = Counter(ref_labels)
print("\n=== MENTION COUNTS ===")
for lab in cap_labels:
    print("  %-9s cited %d time(s)" % (lab, cnt.get(lab, 0)))

