Smart Traffic Analytics is a data-processing project that analyzes traffic data using Python and MapReduce concepts. It processes traffic records, organizes information into hourly counts, and generates aggregated results that can support traffic pattern analysis.
- Process traffic data efficiently.
- Transform raw records into structured input.
- Use a mapper to emit intermediate key-value pairs.
- Use a reducer to aggregate traffic counts.
- Generate output that can be used for further analysis.
- Python
- MapReduce
- Linux / Ubuntu (WSL)
```
smart-traffic-analytics/
├── mapreduce/
│   ├── mapper.py
│   ├── prepare_data.py
│   └── reducer.py
└── README.md
```
1. Data Preparation: prepare_data.py prepares the input data for processing.
2. Mapping: mapper.py processes input records and emits intermediate key-value pairs.
3. Reducing: reducer.py aggregates the intermediate results.
4. Analysis: The aggregated output can be used to examine traffic counts and patterns.
- Python 3 installed
- Ubuntu or another Linux environment
- Input traffic dataset in the format expected by the scripts
```
git clone https://github.com/ayeshamaniyar26/smart-traffic-analytics.git
cd smart-traffic-analytics
```
Check the command-line arguments and expected input format in each Python script before running it.
```
python3 mapreduce/prepare_data.py
python3 mapreduce/mapper.py
python3 mapreduce/reducer.py
```
The scripts may require input redirection, arguments, or intermediate files depending on their implementation.
- Analyze traffic trends by hour.
- Add visualizations of traffic patterns.
- Improve processing efficiency for large datasets.
- Build a dashboard for exploring traffic statistics.
