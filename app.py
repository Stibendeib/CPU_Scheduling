import os
import sys

from flask import Flask, jsonify, render_template, request


def resource_path(relative_path):
    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


app = Flask(
    __name__,
    template_folder=resource_path("templates"),
    static_folder=resource_path("static"),
)


def validate_payload(payload):
    algorithm = str(payload.get("algorithm", "FCFS")).upper()
    processes = payload.get("processes", [])
    quantum = payload.get("quantum", 2)

    if algorithm not in {"FCFS", "NPP", "RR", "SJF"}:
        raise ValueError("Choose a supported scheduling algorithm.")
    if not isinstance(processes, list) or not processes:
        raise ValueError("Add at least one process.")

    normalized = []
    seen = set()
    for index, item in enumerate(processes):
        pid = str(item.get("pid", "")).strip() or f"P{index + 1}"
        if pid in seen:
            raise ValueError(f"Process ID '{pid}' is duplicated.")
        seen.add(pid)

        arrival = float(item.get("arrival_time", 0))
        burst = float(item.get("burst_time", 0))
        if arrival < 0:
            raise ValueError(f"{pid} has a negative arrival time.")
        if burst <= 0:
            raise ValueError(f"{pid} must have a burst time greater than zero.")

        priority_value = item.get("priority", 1)
        priority = int(priority_value) if str(priority_value).strip() != "" else 1
        normalized.append(
            {
                "pid": pid,
                "arrival_time": arrival,
                "burst_time": burst,
                "priority": priority,
                "order": index,
            }
        )

    if algorithm == "RR":
        quantum = float(quantum)
        if quantum <= 0:
            raise ValueError("Round Robin time quantum must be greater than zero.")

    return algorithm, normalized, quantum


def compact_number(value):
    rounded = round(value, 2)
    return int(rounded) if rounded.is_integer() else rounded


def idle_until(gantt, current_time, next_time):
    if next_time > current_time:
        gantt.append({"pid": "Idle", "start": current_time, "end": next_time})
        return next_time
    return current_time


def add_segment(gantt, pid, start, end):
    if end <= start:
        return
    if gantt and gantt[-1]["pid"] == pid and gantt[-1]["end"] == start:
        gantt[-1]["end"] = end
    else:
        gantt.append({"pid": pid, "start": start, "end": end})


def finish_table(processes, completion_times, start_times):
    rows = []
    total_waiting = 0
    total_turnaround = 0

    for process in sorted(processes, key=lambda item: item["order"]):
        pid = process["pid"]
        turnaround = completion_times[pid] - process["arrival_time"]
        waiting = turnaround - process["burst_time"]
        total_waiting += waiting
        total_turnaround += turnaround
        rows.append(
            {
                "pid": pid,
                "arrival_time": compact_number(process["arrival_time"]),
                "burst_time": compact_number(process["burst_time"]),
                "priority": process["priority"],
                "start_time": compact_number(start_times[pid]),
                "waiting_time": compact_number(waiting),
                "turnaround_time": compact_number(turnaround),
                "completion_time": compact_number(completion_times[pid]),
            }
        )

    count = len(processes)
    return {
        "table": rows,
        "average_waiting_time": compact_number(total_waiting / count),
        "average_turnaround_time": compact_number(total_turnaround / count),
    }


def schedule_fcfs(processes):
    current_time = 0
    gantt = []
    start_times = {}
    completion_times = {}

    for process in sorted(processes, key=lambda item: (item["arrival_time"], item["order"])):
        current_time = idle_until(gantt, current_time, process["arrival_time"])
        start_times[process["pid"]] = current_time
        completion_times[process["pid"]] = current_time + process["burst_time"]
        add_segment(gantt, process["pid"], current_time, completion_times[process["pid"]])
        current_time = completion_times[process["pid"]]

    return gantt, start_times, completion_times


def schedule_priority(processes):
    current_time = 0
    remaining = sorted(processes, key=lambda item: (item["arrival_time"], item["order"]))
    gantt = []
    start_times = {}
    completion_times = {}

    while remaining:
        available = [item for item in remaining if item["arrival_time"] <= current_time]
        if not available:
            current_time = idle_until(gantt, current_time, remaining[0]["arrival_time"])
            continue

        process = min(available, key=lambda item: (item["priority"], item["arrival_time"], item["order"]))
        remaining.remove(process)
        start_times[process["pid"]] = current_time
        completion_times[process["pid"]] = current_time + process["burst_time"]
        add_segment(gantt, process["pid"], current_time, completion_times[process["pid"]])
        current_time = completion_times[process["pid"]]

    return gantt, start_times, completion_times


def schedule_sjf(processes):
    current_time = 0
    remaining = sorted(processes, key=lambda item: (item["arrival_time"], item["order"]))
    gantt = []
    start_times = {}
    completion_times = {}

    while remaining:
        available = [item for item in remaining if item["arrival_time"] <= current_time]
        if not available:
            current_time = idle_until(gantt, current_time, remaining[0]["arrival_time"])
            continue

        process = min(available, key=lambda item: (item["burst_time"], item["arrival_time"], item["order"]))
        remaining.remove(process)
        start_times[process["pid"]] = current_time
        completion_times[process["pid"]] = current_time + process["burst_time"]
        add_segment(gantt, process["pid"], current_time, completion_times[process["pid"]])
        current_time = completion_times[process["pid"]]

    return gantt, start_times, completion_times


def schedule_round_robin(processes, quantum):
    ordered = sorted(processes, key=lambda item: (item["arrival_time"], item["order"]))
    remaining = {process["pid"]: process["burst_time"] for process in ordered}
    start_times = {}
    completion_times = {}
    queue = []
    gantt = []
    current_time = 0
    next_index = 0

    while next_index < len(ordered) or queue:
        if not queue and next_index < len(ordered) and current_time < ordered[next_index]["arrival_time"]:
            current_time = idle_until(gantt, current_time, ordered[next_index]["arrival_time"])

        while next_index < len(ordered) and ordered[next_index]["arrival_time"] <= current_time:
            queue.append(ordered[next_index])
            next_index += 1

        if not queue:
            continue

        process = queue.pop(0)
        pid = process["pid"]
        start_times.setdefault(pid, current_time)
        run_time = min(quantum, remaining[pid])
        segment_start = current_time
        current_time += run_time
        remaining[pid] -= run_time
        add_segment(gantt, pid, segment_start, current_time)

        while next_index < len(ordered) and ordered[next_index]["arrival_time"] <= current_time:
            queue.append(ordered[next_index])
            next_index += 1

        if remaining[pid] > 0:
            queue.append(process)
        else:
            completion_times[pid] = current_time

    return gantt, start_times, completion_times


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/schedule")
def schedule():
    try:
        payload = request.get_json(force=True)
        algorithm, processes, quantum = validate_payload(payload)

        if algorithm == "FCFS":
            gantt, start_times, completion_times = schedule_fcfs(processes)
        elif algorithm == "NPP":
            gantt, start_times, completion_times = schedule_priority(processes)
        elif algorithm == "SJF":
            gantt, start_times, completion_times = schedule_sjf(processes)
        else:
            gantt, start_times, completion_times = schedule_round_robin(processes, quantum)

        table_result = finish_table(processes, completion_times, start_times)
        return jsonify(
            {
                "algorithm": algorithm,
                "gantt": [
                    {
                        "pid": item["pid"],
                        "start": compact_number(item["start"]),
                        "end": compact_number(item["end"]),
                        "duration": compact_number(item["end"] - item["start"]),
                    }
                    for item in gantt
                ],
                **table_result,
            }
        )
    except (TypeError, ValueError) as error:
        return jsonify({"error": str(error)}), 400


if __name__ == "__main__":
    app.run(debug=True)
