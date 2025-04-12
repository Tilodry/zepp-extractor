"""
main.py
Retrieves swimming workouts via the Mi Fit API, extracts and analyzes metrics,
and exports the data into a well-structured CSV for easier processing.
"""

import csv
import logging
import os
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

# Get the API token from the environment variable
token = os.environ['ZEPP_TOKEN']

# Output directory for CSV files
output_dir = Path('workouts')

# Theoretical max heart rate (e.g., 220 - age)
hr_max_theoretical = 196

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_ENDPOINT = "https://api-mifit.huami.com"


def get_workout_history(token):
    """Fetch workout history from Mi Fit API."""
    url = f"{API_ENDPOINT}/v1/sport/run/history.json"
    headers = {
        "apptoken": token,
        "appPlatform": "web",
        "appname": "com.xiaomi.hm.health"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def get_workout_detail(token, track_id, source):
    """Fetch workout details given a track_id and source."""
    url = f"{API_ENDPOINT}/v1/sport/run/detail.json"
    headers = {
        "apptoken": token,
        "appPlatform": "web",
        "appname": "com.xiaomi.hm.health"
    }
    params = {"trackid": track_id, "source": source}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()


def parse_times(detail_data):
    """Parse the time series string into a list of timestamps."""
    t_str = detail_data.get("time", "")
    return [t.strip() for t in t_str.split(";") if t.strip()]


def parse_hr(detail_data):
    """
    Parse heart rate data in the format 'timestamp,hr;timestamp,hr;...'.
    The first value is absolute, subsequent ones are cumulative differences.
    """
    hr_str = detail_data.get("heart_rate", "")
    if hr_str:
        segments = [seg for seg in hr_str.split(";") if seg]
        hr_values = []
        for segment in segments:
            parts = segment.split(",")
            if len(parts) > 1:
                try:
                    hr_val = int(parts[1])
                    hr_values.append(hr_val)
                except ValueError:
                    hr_values.append(0)
        return hr_values
    return []


def parse_pace(detail_data):
    """Parse the pace string and ensure a consistent decimal format."""
    pace_str = detail_data.get("pace", "").replace(",", ".")
    return [v.strip() for v in pace_str.split(";") if v.strip()]


def generate_timestamps(start_time, count):
    """Generate a list of formatted timestamps starting from start_time."""
    return [(start_time + timedelta(seconds=i)).strftime("%H:%M:%S") for i in range(count)]


def export_csv(output_path, workout_summary, timestamps, hr_variations, current_hr, paces, computed_metrics):
    # Convert track_id (timestamp) to local time (Montreal)
    track_id = workout_summary.get("trackid")
    workout_start_time = datetime.fromtimestamp(int(track_id), tz=timezone.utc)\
                              .astimezone(ZoneInfo("America/Montreal")).strftime("%H:%M:%S")

    # Calculate run_time from the total elapsed seconds (number of timestamps - 1)
    run_time_sec = len(timestamps) - 1
    h = run_time_sec // 3600
    m = (run_time_sec % 3600) // 60
    s = run_time_sec % 60
    formatted_run_time = f"{h:02d}:{m:02d}:{s:02d}"

    # Extract additional workout info
    calories = workout_summary.get("calorie", "")
    exercise_load = workout_summary.get("exercise_load", "")
    laps = workout_summary.get("total_trips", "")
    pool_length = workout_summary.get("swim_pool_length", "")
    avg_heart_rate = workout_summary.get("avg_heart_rate", "")
    swolf = workout_summary.get("swolf", "")

    # Build the basic info dictionary in the desired order.
    basic_info = {
        "total_distance": computed_metrics["total_distance"],
        "laps": laps,
        "calories": calories,
        "exercise_load": exercise_load,
        "run_time (HH:MM:SS)": formatted_run_time,
        "workout_start_time": workout_start_time,
        "avg_heart_rate": avg_heart_rate,
        "swolf": swolf,
        "percentage_moving": f"{computed_metrics['percentage_moving']:.2f}%",
        "percentage_idle": f"{computed_metrics['percentage_idle']:.2f}%",
        "track_id": track_id,
        "pool_length": pool_length
    }

    # Global metrics from the summary (more specific details)
    global_metrics = {
        "total_strokes": workout_summary.get("total_strokes", ""),
        "avg_stroke_speed": workout_summary.get("avg_stroke_speed", ""),
        "max_stroke_speed": workout_summary.get("max_stroke_speed", ""),
        "avg_distance_per_stroke": workout_summary.get("avg_distance_per_stroke", ""),
        "training_effect": workout_summary.get("te", ""),
        "swim_style": workout_summary.get("swim_style", "")
    }

    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)

        writer.writerow(["# Section: Basic Workout Info"])
        headers_basic = list(basic_info.keys())
        writer.writerow(headers_basic)
        writer.writerow([basic_info[key] for key in headers_basic])
        writer.writerow([])

        writer.writerow(["# Section: Global Metrics"])
        header_global = list(global_metrics.keys())
        writer.writerow(header_global)
        writer.writerow([global_metrics[k] for k in header_global])
        writer.writerow([])

        writer.writerow(["# Section: HR Metrics"])
        writer.writerow(["hr_max", "hr_min", "hr_start", "hr_end", "hr_variance"])
        writer.writerow([
            computed_metrics["hr_max"],
            computed_metrics["hr_min"],
            computed_metrics["hr_start"],
            computed_metrics["hr_end"],
            f"{computed_metrics['hr_variance']:.2f}"
        ])
        writer.writerow([])
        writer.writerow(["Zone", "Percentage"])
        for zone, pct in computed_metrics["zone_percentages"].items():
            writer.writerow([zone, f"{pct:.2f}%"])
        writer.writerow([])

        writer.writerow(["# Section: Effort/Rest Durations"])
        writer.writerow(["avg_effort_duration_s", "avg_rest_duration_s"])
        writer.writerow([
            f"{computed_metrics['avg_effort_duration']:.2f}",
            f"{computed_metrics['avg_rest_duration']:.2f}"
        ])
        writer.writerow([])

        writer.writerow(["# Section: Time Series Data"])
        writer.writerow(["timestamp", "relative (s)", "elapsed_time", "hr_variation", "current_hr", "pace"])
        for i in range(len(timestamps)):
            minutes = i // 60
            seconds = i % 60
            elapsed = f"{minutes}m{seconds}s"
            writer.writerow([timestamps[i], i, elapsed, hr_variations[i], current_hr[i], paces[i]])

    logger.info(f"CSV exported to {output_path}")


def process_workout(workout, token, output_dir):
    """Processes an individual workout and exports its CSV."""
    track_id = workout.get("trackid")
    logger.info(f"Processing workout with track_id {track_id}")

    detail_json = get_workout_detail(token, track_id, workout.get("source"))
    detail_data = detail_json.get("data", {})

    raw_times = parse_times(detail_data)
    hr_values = parse_hr(detail_data)
    raw_paces = parse_pace(detail_data)

    num_points = min(len(raw_times), len(hr_values), len(raw_paces))
    if num_points == 0:
        logger.warning(f"No usable data for workout {track_id}")
        return

    start_time = datetime.fromtimestamp(int(track_id), tz=timezone.utc)\
                        .astimezone(ZoneInfo("America/Montreal"))
    timestamps = generate_timestamps(start_time, num_points)

    base_hr = float(hr_values[0]) if hr_values else 70.0
    hr_differences = hr_values[1:] if len(hr_values) > 1 else []
    current_hr = [base_hr]
    cumulative = base_hr
    for diff in hr_differences:
        cumulative += diff
        current_hr.append(cumulative)
    current_hr = (current_hr + [current_hr[-1]] * num_points)[:num_points]

    hr_variations = [0] + hr_differences
    hr_variations = hr_variations[:num_points]

    try:
        processed_pace = [float(x) for x in raw_paces[:num_points]]
    except Exception:
        processed_pace = [0.0] * num_points

    hr_max_val = max(current_hr)
    hr_min_val = min(current_hr)
    hr_start = current_hr[0]
    hr_end = current_hr[-1]

    if len(hr_variations) > 1:
        diffs = hr_variations[1:]
        mean_diff = sum(diffs) / len(diffs)
        hr_variance = sum((d - mean_diff) ** 2 for d in diffs) / len(diffs)
    else:
        hr_variance = 0.0

    hr_zones = {
        "Z1 (50-60%)": (0.5 * hr_max_theoretical, 0.6 * hr_max_theoretical),
        "Z2 (60-70%)": (0.6 * hr_max_theoretical, 0.7 * hr_max_theoretical),
        "Z3 (70-80%)": (0.7 * hr_max_theoretical, 0.8 * hr_max_theoretical),
        "Z4 (80-90%)": (0.8 * hr_max_theoretical, 0.9 * hr_max_theoretical),
        "Z5 (90-100%)": (0.9 * hr_max_theoretical, hr_max_theoretical)
    }
    zone_counts = {zone: 0 for zone in hr_zones}
    for hr in current_hr:
        for zone, (low, high) in hr_zones.items():
            if low <= hr < high:
                zone_counts[zone] += 1
                break
    zone_percentages = {zone: (count / num_points) * 100 for zone, count in zone_counts.items()}

    effort_durations = []
    rest_durations = []
    state = "idle" if processed_pace[0] == 0 else "effort"
    duration = 0
    for p in processed_pace:
        if p > 0:
            if state == "effort":
                duration += 1
            else:
                rest_durations.append(duration)
                duration = 1
                state = "effort"
        else:
            if state == "idle":
                duration += 1
            else:
                effort_durations.append(duration)
                duration = 1
                state = "idle"
    if state == "effort":
        effort_durations.append(duration)
    else:
        rest_durations.append(duration)

    avg_effort_duration = sum(effort_durations) / len(effort_durations) if effort_durations else 0
    avg_rest_duration = sum(rest_durations) / len(rest_durations) if rest_durations else 0

    laps = float(workout.get("total_trips", 0))
    pool_length = float(workout.get("swim_pool_length", 0))
    total_distance = laps * pool_length
    average_pace = sum(processed_pace) / num_points if num_points > 0 else 0
    moving = sum(1 for p in processed_pace if p > 0)
    percentage_moving = (moving / num_points) * 100
    percentage_idle = 100 - percentage_moving

    computed_metrics = {
        "total_distance": total_distance,
        "average_pace": average_pace,
        "percentage_moving": percentage_moving,
        "percentage_idle": percentage_idle,
        "hr_max": hr_max_val,
        "hr_min": hr_min_val,
        "hr_start": hr_start,
        "hr_end": hr_end,
        "hr_variance": hr_variance,
        "avg_effort_duration": avg_effort_duration,
        "avg_rest_duration": avg_rest_duration,
        "zone_percentages": zone_percentages
    }

    file_name = start_time.strftime("%Y-%m-%d_%H-%M-%S.csv")
    file_path = output_dir / file_name
    export_csv(file_path, workout, timestamps, hr_variations, current_hr, processed_pace, computed_metrics)


def main():
    logger.info("Retrieving workouts...")
    history_json = get_workout_history(token)
    workouts = history_json.get("data", {}).get("summary", [])

    # Filter swimming workouts by checking if swim_pool_length is positive
    swimming_workouts = [w for w in workouts if w.get("swim_pool_length") and float(w.get("swim_pool_length")) > 0]

    if not swimming_workouts:
        logger.warning("No swimming workouts found.")
        return
    else:
        logger.info(f"Found {len(swimming_workouts)} swimming workout(s). Retrieving details...")

    output_dir.mkdir(parents=True, exist_ok=True)
    for workout in swimming_workouts:
        process_workout(workout, token, output_dir)

if __name__ == "__main__":
    main()
