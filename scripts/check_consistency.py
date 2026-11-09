"""Перевіряє spec.md <-> model.mmd (AC-1, AC-2, AC-6, AC-7, AC-8).

Двосторонньо: сутності, атрибути, типи, ключі (PK/FK/UK), FK = PK за назвою і типом,
кардинальності R1-R6. Кардинальності беруться зі списку у spec.md:
    - R1: PUBLISHER ||--o{ BOOK
НЕ перевіряє: 3NF, змістовні бізнес-правила, nullable. Це робить аудит (людина + ШІ).
"""
import re, sys, pathlib

root = pathlib.Path(__file__).resolve().parent.parent
spec = (root / "spec.md").read_text(encoding="utf-8")
model = (root / "model.mmd").read_text(encoding="utf-8")
errors = []

# --- spec: {сутність: {атрибут: (тип, ключ, ref)}}
spec_ent = {}
for m in re.finditer(r"^### (\w+)[^\n]*\n(.*?)(?=^### |^## |\Z)", spec, re.S | re.M):
    attrs = {}
    for r in re.finditer(r"^\|\s*`(\w+)`\s*\|\s*(\w+)\s*\|\s*([^|]*?)\s*\|", m.group(2), re.M):
        key = r.group(3).split()[0] if r.group(3).strip() else ""
        ref = re.search(r"→\s*(\w+)", r.group(3))
        attrs[r.group(1)] = (r.group(2), key, ref.group(1) if ref else None)
    spec_ent[m.group(1)] = attrs

# --- model
model_ent = {}
for name, body in re.findall(r"^\s*(\w+)\s*\{\s*$(.*?)^\s*\}\s*$", model, re.S | re.M):
    attrs = {}
    for line in body.strip().splitlines():
        p = line.split()
        if len(p) >= 2:
            attrs[p[1]] = (p[0], p[2] if len(p) > 2 else "")
    model_ent[name] = attrs

for e in spec_ent.keys() - model_ent.keys():
    errors.append(f"сутність {e} є в spec, немає в моделі")
for e in model_ent.keys() - spec_ent.keys():
    errors.append(f"сутність {e} є в моделі, немає в spec")

for e in spec_ent.keys() & model_ent.keys():
    s, m = spec_ent[e], model_ent[e]
    for a in s.keys() - m.keys():
        errors.append(f"{e}.{a}: є в spec, немає в моделі")
    for a in m.keys() - s.keys():
        errors.append(f"{e}.{a}: є в моделі, немає в spec")
    for a in s.keys() & m.keys():
        if s[a][0] != m[a][0]:
            errors.append(f"{e}.{a}: тип spec={s[a][0]}, модель={m[a][0]}")
        if s[a][1] != m[a][1]:
            errors.append(f"{e}.{a}: ключ spec='{s[a][1]}', модель='{m[a][1]}'")

# --- AC-1 / AC-2
for e, attrs in spec_ent.items():
    pks = [a for a, v in attrs.items() if v[1] == "PK"]
    stem = pks[0][:-3] if pks and pks[0].endswith("_id") else ""
    if len(pks) != 1 or stem not in (e.lower(), e.lower().split("_")[-1]) or attrs[pks[0]][0] != "int":
        errors.append(f"AC-1: {e} має некоректний PK {pks}")
    for a, (t, k, ref) in attrs.items():
        if k == "FK":
            tgt = spec_ent.get(ref, {})
            if a not in tgt or tgt[a][1] != "PK" or tgt[a][0] != t:
                errors.append(f"AC-2: {e}.{a} не збігається з PK у {ref}")

# --- AC-7: кардинальності
spec_rel = {}
for m in re.finditer(r"^- (R\d+): (\w+) (\S+--\S+) (\w+)", spec, re.M):
    spec_rel[(m.group(2), m.group(4))] = (m.group(1), m.group(3))
model_rel = {(m.group(1), m.group(3)): m.group(2) for m in
             re.finditer(r"^\s*(\w+)\s+(\S+--\S+)\s+(\w+)\s*(?::.*)?$", model, re.M)}
if not spec_rel:
    errors.append("AC-7: у spec.md немає списку '- R1: A ||--o{ B'")
for pair, (rid, nota) in spec_rel.items():
    got = model_rel.get(pair)
    if got is None:
        errors.append(f"AC-7: {rid} {pair[0]}-{pair[1]} немає в моделі (або інший порядок сутностей)")
    elif got != nota:
        errors.append(f"AC-7: {rid} {pair[0]}-{pair[1]}: spec {nota}, модель {got}")
for pair in model_rel.keys() - spec_rel.keys():
    errors.append(f"AC-7: зв'язок {pair[0]}-{pair[1]} є в моделі, немає в spec")

print("\n".join(errors) if errors else "OK: назви, типи, ключі, FK=PK і кардинальності збігаються")
sys.exit(1 if errors else 0)