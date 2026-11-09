# Smart Traffic Analytics – NYC Taxi Demand Intelligence

**Smart Traffic Analytics** is a Python-based Big Data project that analyzes historical NYC Yellow Taxi trip records to identify hourly demand patterns, busy periods, popular pickup and drop-off locations, and passenger trends.

The project uses **Hadoop HDFS and MapReduce** for large-scale data processing and **Streamlit** to present the results through an interactive analytics dashboard.

🌐 **Live Dashboard:** [Smart Traffic Analytics](https://smart-trafficanalytics.streamlit.app/)

## Problem Statement

Urban transportation generates large volumes of trip data every day. Analyzing this data manually makes it difficult to identify demand patterns, peak travel hours, high-demand pickup locations, and changes in passenger activity.

This project addresses the challenge by processing large-scale NYC Yellow Taxi trip data and transforming it into meaningful insights. It helps users understand when and where taxi demand is highest through data processing, aggregation, visualization, and interactive filtering.

## About the Project

Smart Traffic Analytics focuses on analyzing historical taxi demand rather than monitoring live road congestion or tracking vehicles in real time.

The project processes Yellow Taxi trip records stored in Parquet files, extracts relevant information, performs hourly aggregation using MapReduce, and generates analytical datasets for visualization.

The Streamlit dashboard allows users to explore demand patterns, compare trends, examine location-based insights, and understand key findings from the dataset.

## Dataset Used

- **Dataset:** NYC Yellow Taxi Trip Records
- **Source:** [NYC Taxi & Limousine Commission – Trip Record Data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page)
- **Time Period:** January 2024 – December 2025
- **Number of Files:** 24 monthly Parquet files
- **Total Dataset Size:** Approximately 1.5 GB
- **Format:** Parquet

The dataset contains information such as pickup and drop-off timestamps, pickup and drop-off location IDs, passenger counts, trip distances, fares, payment types, and other trip-related details.

## Key Features

- **Hourly Demand Analysis:** Identifies busy and quiet hours based on taxi pickup records.
- **Pickup and Drop-off Analysis:** Highlights locations with high taxi demand.
- **Monthly and Yearly Trends:** Explores changes in taxi demand over time.
- **Payment and Passenger Insights:** Analyzes payment methods and passenger patterns.
- **Interactive Filters:** Allows users to filter data by year, month, hour, and weekday.
- **Trend Comparison:** Compares demand across selected time periods.
- **Forecasting and Anomaly Analysis:** Explores potential demand trends and unusual patterns.
- **Data Quality Analysis:** Provides insights into the quality and consistency of the processed data.
- **Interactive Dashboard:** Presents analytical results through charts, KPIs, visualizations, and downloadable datasets.

## Technologies Used

- Python 3
- Pandas
- PyArrow
- Hadoop 3.5.0
- Hadoop Distributed File System (HDFS)
- Hadoop Streaming / MapReduce
- Streamlit
- Plotly
- Linux / Ubuntu (WSL)

## Project Structure

```text
smart-traffic-analytics/
│
├── analytics/
│   └── generate_analytics.py
│
├── mapreduce/
│   ├── prepare_data.py
│   ├── mapper.py
│   └── reducer.py
│
├── data/
│   ├── hourly_trips.csv
│   ├── monthly_summary.csv
│   ├── pickup_zones.csv
│   ├── dropoff_zones.csv
│   └── other analytical CSV files
│
├── tests/
│   ├── sample_input.txt
│   ├── test_mapper.py
│   └── test_reducer.py
│
├── app.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Project Workflow

1. **Data Collection:** Download the 24 monthly NYC Yellow Taxi Parquet files.
2. **Data Preparation:** Use Python and PyArrow to extract relevant trip information and prepare records for processing.
3. **HDFS Storage:** Store the prepared dataset in Hadoop Distributed File System (HDFS).
4. **Mapping:** The mapper extracts the hour from each pickup timestamp and emits an hourly key with a count of 1.
5. **Sorting:** Mapper output is sorted by key.
6. **Reduction:** The reducer aggregates the counts to calculate the total number of pickups for each hour.
7. **Analytics Generation:** Python and Pandas generate additional analytical CSV datasets from the source Parquet files.
8. **Visualization:** Streamlit and Plotly present the processed data through an interactive dashboard.

## Running the Project

### Prerequisites

- Python 3
- Java
- Hadoop 3.5.0
- PyArrow
- Pandas
- Streamlit
- Plotly

### Install Dependencies

From the project directory, activate your virtual environment and install the required packages:

```bash
pip install -r requirements.txt
```

### Run the Dashboard

```bash
streamlit run app.py
```

The dashboard will open in your browser.

### Run the Data Preparation Script

```bash
python3 mapreduce/prepare_data.py
```

The preparation script expects the 24 Yellow Taxi Parquet files in the configured source directory.

### Run the Sample MapReduce Pipeline

```bash
python3 tests/test_mapper.py < tests/sample_input.txt \
  | sort -k1,1 \
  | python3 tests/test_reducer.py
```

## Live Application

Explore the interactive dashboard:

[**https://smart-trafficanalytics.streamlit.app/**](https://smart-trafficanalytics.streamlit.app/)

---

**Smart Traffic Analytics | Developed by Ayesha Maniyar | KLE Technological University | Python, Hadoop, Pandas, Plotly & Streamlit**