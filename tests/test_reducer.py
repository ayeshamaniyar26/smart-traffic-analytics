import sys
from collections import defaultdict

counts = defaultdict(int)

for line in sys.stdin:
    parts = line.strip().split("\t")
    if len(parts) != 2:
        continue

    try:
        counts[parts[0]] += int(parts[1])
    except ValueError:
        continue

for hour in sorted(counts):
    print(f"{hour}\t{counts[hour]}")
