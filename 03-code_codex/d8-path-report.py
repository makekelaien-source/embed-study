from pathlib import Path
target = Path("reports") / "alert.csv"
print(Path.cwd(),
      target.name,
      target.resolve())
a = Path(__file__).resolve().parent
target = a / "reports" / "alert.csv"
print(Path.cwd(),target.name,target.resolve())