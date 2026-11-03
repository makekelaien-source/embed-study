# Teacher-prepared dependency: existing dictionary comparison,
# adapted from d7-python-dictionary.py to return a status string.
def status_when_complete(sample):
    if sample["temperature"] >= sample["limit"]:
        return "ALARM"
    else:
        return "NORMAL"


# Student: define safe_status(sample) below.
def safe(sample):
    if "limit" in sample :
        return (status_when_complete(sample))
    else :
        return ("NO_LIMIT")

sample = {"teperature": 26}
print(safe(sample))
