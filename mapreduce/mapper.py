#!/usr/bin/env python3
import sys

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue

    try:
        date_hour, count = line.split("\t")
        hour = date_hour.split()[-1]
        print(f"{hour}\t{int(count)}")
    except (ValueError, IndexError):
        continue
