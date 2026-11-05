from build_change_report import build_change_report

if __name__ == "__main__":
    expected = {"east": 28, "west": 26, "north": 32, "south": 25, "lobby": 20}
    actual = {"east": 30, "west": 30, "south": 24, "lobby": 20, "roof": 35}
    report = build_change_report(expected, actual, "changes.txt")
    print(report["by_value"])
    print(report["report_path"])
