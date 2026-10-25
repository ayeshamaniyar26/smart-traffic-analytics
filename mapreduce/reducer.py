#!/usr/bin/env python3
import sys

current_hour = None
total = 0

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue

    try:
        hour, count = line.split("\t")
        count = int(count)
    except ValueError:
        continue

    if hour == current_hour:
        total += count
    else:
        if current_hour is not None:
            print(f"{current_hour}\t{total}")
        current_hour = hour
        total = count

if current_hour is not None:
    print(f"{current_hour}\t{total}")
