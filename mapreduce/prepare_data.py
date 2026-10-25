from pathlib import Path
import pyarrow.parquet as pq

source = Path.home()
output = source / "smart-traffic" / "hourly_input.txt"
files = sorted(source.glob("yellow_tripdata_*.parquet"))

if len(files) != 24:
    raise SystemExit(
        f"Expected 24 Parquet files in {source}, found {len(files)}"
    )

with output.open("w", encoding="utf-8") as out:
    for file in files:
        print(f"Processing {file.name}", flush=True)
        parquet = pq.ParquetFile(file)

        if "tpep_pickup_datetime" not in parquet.schema.names:
            raise SystemExit(
                f"Pickup timestamp column missing in {file.name}"
            )

        for batch in parquet.iter_batches(
            columns=["tpep_pickup_datetime"],
            batch_size=100_000
        ):
            for value in batch.column(0).to_pylist():
                if value is not None:
                    out.write(value.strftime("%Y-%m-%d %H") + "\n")

print(f"Prepared input: {output}")
