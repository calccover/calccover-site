"""Remove duplicate closing tags after the first </main> in E&O calculator."""
from pathlib import Path

path = Path("errors-omissions-insurance-calculator/index.html")
lines = path.read_text(encoding="utf-8").split("\n")

# Find first </main> and <footer>
first_main = next(i for i, l in enumerate(lines) if "</main>" in l)
footer = next(i for i, l in enumerate(lines) if "<footer>" in l)

print(f"First </main> at line {first_main + 1}")
print(f"<footer> at line {footer + 1}")
print(f"Lines between: {footer - first_main - 1}")
print()

# Remove stray closing tags between first </main> and <footer>
new_lines = []
removed = 0
for i, line in enumerate(lines):
    if first_main < i < footer:
        stripped = line.strip()
        if stripped in ("</main>", "</section>", "</div>"):
            print(f"  Removing line {i + 1}: {line}")
            removed += 1
            continue
    new_lines.append(line)

path.write_text("\n".join(new_lines), encoding="utf-8")
print(f"\n✅ Removed {removed} stray closing tags")