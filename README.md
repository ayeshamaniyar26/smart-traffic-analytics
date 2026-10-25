Smart Traffic Analytics

A Python-based traffic data processing project that uses MapReduce-style processing to aggregate vehicle pickup records by hour.

## Overview

This project processes Yellow Taxi trip data stored in Parquet files. The preparation script extracts pickup timestamps and writes them to a text file. Mapper and reducer scripts demonstrate how records can be transformed and aggregated into hourly counts.

## Technologies

- Python 3
- PyArrow for Parquet processing
- MapReduce programming concepts
- Linux / Ubuntu (WSL)

## Project Structure

```text
smart-traffic-analytics/
├── mapreduce/
│   ├── prepare_data.py
│   ├── mapper.py
│   └── reducer.py
├── tests/
│   ├── sample_input.txt
│   ├── test_mapper.py
│   └── test_reducer.py
├── .gitignore
└── README.md
```

## Workflow

1. **Data preparation:** `prepare_data.py` reads the pickup timestamp column from 24 Parquet files and writes timestamps to `hourly_input.txt`.
2. **Mapping:** The mapper converts each timestamp into an hour key and emits a count of 1.
3. **Sorting:** Mapper output is sorted by key.
4. **Reduction:** The reducer aggregates counts for each hour.

The reusable sample scripts in `tests/` demonstrate the timestamp-to-hour aggregation workflow independently of the original scripts.

## Prerequisites

- Python 3
- PyArrow (`python3 -m pip install pyarrow`)
- The expected Yellow Taxi Parquet files in your home directory, named `yellow_tripdata_*.parquet`

## Running the Preparation Script

From the repository root:

```bash
python3 mapreduce/prepare_data.py
```

The script expects exactly 24 matching Parquet files in your home directory and writes `hourly_input.txt` under `~/smart-traffic/`.

**Note:** The preparation script processes the source files and writes the output file. Ensure the expected data is available before running it.

## Testing the Sample Pipeline

Run the sample mapper and reducer:

```bash
python3 tests/test_mapper.py < tests/sample_input.txt \
  | sort -k1,1 \
  | python3 tests/test_reducer.py
```

Expected output:

```text
08    3
09    2
10    1
```

## Future Improvements

- Integrate the preparation output directly with the MapReduce processing pipeline.
- Add validation and automated tests.
- Visualize hourly traffic patterns.
- Improve processing efficiency for large datasets.

## Author

Ayesha Maniyar

GitHub: [ayeshamaniyar26](https://github.com/ayeshamaniyar26)
**
