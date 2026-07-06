# CPU Scheduling Calculator

A Flask and JavaScript web app for calculating CPU scheduling results.

## Features

- First Come, First Served (FCFS)
- Non-Preemptive Priority (NPP)
- Round Robin (RR)
- Shortest Job First (SJF)
- REST API using JSON at `POST /api/schedule`
- Gantt chart, scheduling table, average waiting time, and average turnaround time

## Run

```bash
pip install -r requirements.txt
python app.py
```

Then open `http://127.0.0.1:5000`.
