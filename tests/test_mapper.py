import sys

for line in sys.stdin:
    timestamp = line.strip()
    if not timestamp:
        continue

    parts = timestamp.rsplit(" ", 1)
    if len(parts) == 2 and parts[1].isdigit():
        print(f"{parts[1]}\t1")
