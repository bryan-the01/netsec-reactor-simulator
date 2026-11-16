import csv
from pathlib import Path


def create_log():
    # Create the results folder
    results_dir = Path(__file__).resolve().parent / "results"
    results_dir.mkdir(exist_ok=True)

    csv_path = results_dir / "baseline.csv"
    csv_file = open(csv_path, "w", newline="", encoding="utf-8")

    csv_writer = csv.writer(csv_file)

    csv_writer.writerow([
        "Time",
        "Actual_Temperature",
        "Reported_Temperature",
        "Cooling_ON",
        "High_Temp_Alarm",
        "Next_Temperature"
    ])

    return csv_file, csv_writer


def write_row(
    logger,
    elapsed_time,
    actual_temperature,
    reported_temperature,
    cooling_active,
    high_temp_alarm,
    next_temperature
):
    csv_file, csv_writer = logger

    # Record simulation data
    csv_writer.writerow([
        elapsed_time,
        actual_temperature,
        reported_temperature,
        cooling_active,
        high_temp_alarm,
        next_temperature
    ])

    csv_file.flush()


def close_log(logger):
    csv_file, _ = logger
    csv_file.close()