
from collections import defaultdict
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

DATA_DIR = Path("DATASET")
OUTPUT_DIR = Path("data")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

LOOKUP_FILE = DATA_DIR / "taxi_zone_lookup.csv"
BATCH_SIZE = 100000

required = [
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime",
    "passenger_count",
    "trip_distance",
    "PULocationID",
    "DOLocationID",
    "payment_type",
    "fare_amount",
    "total_amount"
]

monthly = defaultdict(int)
hourly = defaultdict(int)
weekday = defaultdict(int)
pickup = defaultdict(int)
dropoff = defaultdict(int)
payment = defaultdict(int)
passengers = defaultdict(int)

month_summary = defaultdict(lambda: {
    "trips": 0,
    "sum_fare": 0.0,
    "sum_distance": 0.0,
    "sum_total_amount": 0.0
})

month_weekday_hour = defaultdict(int)
month_pickup = defaultdict(int)
month_dropoff = defaultdict(int)
month_payment = defaultdict(int)
month_passengers = defaultdict(int)

total_trips = 0
total_fare = 0.0
total_amount = 0.0
total_distance = 0.0

valid_fare_count = 0
valid_amount_count = 0
valid_distance_count = 0

files = sorted(DATA_DIR.glob("*.parquet"))

if not files:
    raise FileNotFoundError("No Parquet files found in DATASET")

if not LOOKUP_FILE.exists():
    raise FileNotFoundError(
        "taxi_zone_lookup.csv not found in DATASET folder"
    )

zone_lookup = pd.read_csv(LOOKUP_FILE)
zone_lookup["LocationID"] = pd.to_numeric(
    zone_lookup["LocationID"], errors="coerce"
)

for file_index, file in enumerate(files, 1):
    print(f"Processing {file_index}/{len(files)}: {file.name}")

    parquet = pq.ParquetFile(file)
    available_columns = parquet.schema.names

    missing = [c for c in required if c not in available_columns]
    if missing:
        print(f"Skipping {file.name}; missing columns: {missing}")
        continue

    for batch in parquet.iter_batches(
        batch_size=BATCH_SIZE,
        columns=required
    ):
        df = batch.to_pandas()

        df["tpep_pickup_datetime"] = pd.to_datetime(
            df["tpep_pickup_datetime"], errors="coerce"
        )

        df = df.dropna(subset=["tpep_pickup_datetime"])

        df = df[
            df["tpep_pickup_datetime"].dt.year.isin([2024, 2025])
        ].copy()

        if df.empty:
            continue

        df["month"] = (
            df["tpep_pickup_datetime"].dt.to_period("M").astype(str)
        )
        df["hour"] = df["tpep_pickup_datetime"].dt.hour
        df["weekday"] = df["tpep_pickup_datetime"].dt.day_name()

        fares = pd.to_numeric(df["fare_amount"], errors="coerce")
        amounts = pd.to_numeric(df["total_amount"], errors="coerce")
        distances = pd.to_numeric(df["trip_distance"], errors="coerce")

        fare_valid = fares.notna()
        amount_valid = amounts.notna()
        distance_valid = distances.notna() & (distances >= 0)

        total_trips += len(df)

        total_fare += fares[fare_valid].sum()
        total_amount += amounts[amount_valid].sum()
        total_distance += distances[distance_valid].sum()

        valid_fare_count += int(fare_valid.sum())
        valid_amount_count += int(amount_valid.sum())
        valid_distance_count += int(distance_valid.sum())

        df["_fare"] = fares.fillna(0)
        df["_distance"] = distances.where(distance_valid, 0).fillna(0)
        df["_amount"] = amounts.fillna(0)

        grouped = df.groupby("month").agg(
            trips=("month", "size"),
            sum_fare=("_fare", "sum"),
            sum_distance=("_distance", "sum"),
            sum_total_amount=("_amount", "sum")
        )

        for month, row in grouped.iterrows():
            target = month_summary[month]
            target["trips"] += int(row["trips"])
            target["sum_fare"] += float(row["sum_fare"])
            target["sum_distance"] += float(row["sum_distance"])
            target["sum_total_amount"] += float(row["sum_total_amount"])

        for key, value in df.groupby("month").size().items():
            monthly[key] += int(value)

        for key, value in df.groupby("hour").size().items():
            hourly[int(key)] += int(value)

        for key, value in df.groupby("weekday").size().items():
            weekday[key] += int(value)

        for key, value in df.groupby(
            ["month", "weekday", "hour"]
        ).size().items():
            month_weekday_hour[key] += int(value)

        for key, value in df.groupby(
            ["month", "PULocationID"]
        ).size().items():
            if pd.notna(key[1]):
                month_pickup[(key[0], int(key[1]))] += int(value)

        for key, value in df.groupby(
            ["month", "DOLocationID"]
        ).size().items():
            if pd.notna(key[1]):
                month_dropoff[(key[0], int(key[1]))] += int(value)

        for key, value in df.groupby(
            ["month", "payment_type"]
        ).size().items():
            if pd.notna(key[1]):
                month_payment[(key[0], int(key[1]))] += int(value)

        for key, value in df.groupby(
            ["month", "passenger_count"]
        ).size().items():
            if pd.notna(key[1]):
                month_passengers[(key[0], float(key[1]))] += int(value)

        for key, value in df["PULocationID"].value_counts().items():
            if pd.notna(key):
                pickup[int(key)] += int(value)

        for key, value in df["DOLocationID"].value_counts().items():
            if pd.notna(key):
                dropoff[int(key)] += int(value)

        for key, value in df["payment_type"].value_counts().items():
            if pd.notna(key):
                payment[int(key)] += int(value)

        for key, value in df["passenger_count"].value_counts().items():
            if pd.notna(key):
                passengers[float(key)] += int(value)


def save_dict(filename, data, columns):
    result = pd.DataFrame(
        [(key, value) for key, value in data.items()],
        columns=columns
    )
    result.to_csv(OUTPUT_DIR / filename, index=False)


save_dict("monthly_trips.csv", monthly, ["month", "trips"])
save_dict("hourly_trips.csv", hourly, ["hour", "trips"])
save_dict("weekday_trips.csv", weekday, ["weekday", "trips"])

pickup_df = pd.DataFrame(
    list(pickup.items()),
    columns=["LocationID", "trips"]
).merge(zone_lookup, on="LocationID", how="left")

dropoff_df = pd.DataFrame(
    list(dropoff.items()),
    columns=["LocationID", "trips"]
).merge(zone_lookup, on="LocationID", how="left")

pickup_df.to_csv(OUTPUT_DIR / "pickup_zones.csv", index=False)
dropoff_df.to_csv(OUTPUT_DIR / "dropoff_zones.csv", index=False)

save_dict("payment_types.csv", payment, ["payment_type", "trips"])
save_dict("passenger_counts.csv", passengers, ["passenger_count", "trips"])

summary = pd.DataFrame([{
    "total_trips": total_trips,
    "average_fare": total_fare / total_trips if total_trips else 0,
    "average_total_amount": total_amount / total_trips if total_trips else 0,
    "average_distance": total_distance / total_trips if total_trips else 0,
    "valid_fare_records": valid_fare_count,
    "valid_amount_records": valid_amount_count,
    "valid_distance_records": valid_distance_count
}])

summary.to_csv(OUTPUT_DIR / "summary.csv", index=False)

monthly_summary_df = pd.DataFrame.from_dict(
    month_summary, orient="index"
).rename_axis("month").reset_index()

monthly_summary_df.to_csv(
    OUTPUT_DIR / "monthly_summary.csv", index=False
)

weekday_hour_df = pd.DataFrame(
    [
        (m, w, h, trips)
        for (m, w, h), trips in month_weekday_hour.items()
    ],
    columns=["month", "weekday", "hour", "trips"]
)

weekday_hour_df.to_csv(
    OUTPUT_DIR / "month_weekday_hour.csv", index=False
)


def save_monthly_counts(filename, data, second_column):
    result = pd.DataFrame(
        [
            (month, location, trips)
            for (month, location), trips in data.items()
        ],
        columns=["month", second_column, "trips"]
    )
    result.to_csv(OUTPUT_DIR / filename, index=False)


save_monthly_counts(
    "month_pickup.csv", month_pickup, "location_id"
)
save_monthly_counts(
    "month_dropoff.csv", month_dropoff, "location_id"
)
save_monthly_counts(
    "month_payment.csv", month_payment, "payment_type"
)
save_monthly_counts(
    "month_passengers.csv", month_passengers, "passenger_count"
)

print("\n" + "=" * 50)
print("ANALYTICS GENERATION COMPLETE")
print("=" * 50)
print("Parquet files processed:", len(files))
print("Total filtered trips:", f"{total_trips:,}")
print("Average fare:", round(total_fare / total_trips, 2) if total_trips else 0)
print("Average total amount:", round(total_amount / total_trips, 2) if total_trips else 0)
print("Average distance:", round(total_distance / total_trips, 2) if total_trips else 0)
print("Peak hour:", max(hourly, key=hourly.get) if hourly else "N/A")
print("Output directory:", OUTPUT_DIR.resolve())
print("CSV files generated:", len(list(OUTPUT_DIR.glob("*.csv"))))
print("=" * 50)
