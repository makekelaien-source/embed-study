"""Teacher-only import/path example. It constructs a path without reading a file."""
import d8_value_tools
from pathlib import Path

answer = d8_value_tools.add_one(4)
print(answer)
script_folder = Path(__file__).resolve().parent
data_path = script_folder / "readings.csv"
print(data_path.name)
print(data_path.is_absolute())
