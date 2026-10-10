"""Перевіряє, що кожен атрибут і сутність з model.mmd згадані у spec.md (AC-6)."""
import re, sys, pathlib

root = pathlib.Path(__file__).resolve().parent.parent
spec = (root / "spec.md").read_text(encoding="utf-8")
model = (root / "model.mmd").read_text(encoding="utf-8")

errors = []
for entity, body in re.findall(r"^\s*(\w+)\s*\{(.*?)\}", model, re.S | re.M):
    if f"### {entity}" not in spec:
        errors.append(f"сутність {entity} відсутня у spec.md")
    for line in body.strip().splitlines():
        parts = line.split()
        if len(parts) >= 2:
            typ, name = parts[0], parts[1]
            row = re.search(rf"\|\s*`{name}`\s*\|\s*{typ}\s*\|", spec)
            if not row:
                errors.append(f"{entity}.{name} ({typ}) не збігається зі spec.md")

print("\n".join(errors) if errors else "OK: spec ↔ model узгоджені")
sys.exit(1 if errors else 0)
