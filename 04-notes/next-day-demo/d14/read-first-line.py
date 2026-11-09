from pathlib import Path


def read_first_line(path):
    try:
        with path.open("r", encoding="utf-8") as stream:
            return stream.readline().rstrip("\n")
    except FileNotFoundError:
        return None


if __name__ == "__main__":
    folder = Path(__file__).resolve().parent
    print(read_first_line(folder / "sample.txt"))
    print(read_first_line(folder / "missing.txt"))
