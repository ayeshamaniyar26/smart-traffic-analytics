from pathlib import Path
from collections import Counter
import pyarrow.parquet as pq

project = Path.cwd()
source = project / "DATASET"
output = project / "hourly_input.txt"

files = sorted(source.glob("*.parquet"))

if len(files) != 24:
    raise SystemExit(f"Expected 24 Parquet files, found {len(files)}")

total_trips = 0

with output.open("w", encoding="utf-8") as out:
    for file in files:
        print(f"Processing {file.name}", flush=True)
        parquet = pq.ParquetFile(file)

        if "tpep_pickup_datetime" not in parquet.schema.names:
            raise SystemExit(f"Pickup timestamp missing in {file.name}")

        for batch in parquet.iter_batches(
            columns=["tpep_pickup_datetime"],
            batch_size=100000
        ):
            counts = Counter()

            for value in batch.column(0).to_pylist():
                if value is not None:
                    key = value.strftime("%Y-%m-%d %H")
                    counts[key] += 1

            for key, count in counts.items():
                out.write(f"{key}\t{count}\n")
                total_trips += count

print(f"\nPreparation complete!")
print(f"Files processed: {len(files)}")
print(f"Total trips: {total_trips:,}")
print(f"Output: {output}")
