import csv
from pathlib import Path


def create_log(sensor_ids=None, filename=None):
    # Create the results folder
    results_dir = Path(__file__).resolve().parent / "results"
    results_dir.mkdir(exist_ok=True)

    if filename is None:
        filename = "baseline.csv" if sensor_ids is None else "baseline-three-sensors.csv"
    csv_path = results_dir / filename
    csv_file = open(csv_path, "w", newline="", encoding="utf-8")

    csv_writer = csv.writer(csv_file)

    temperature_columns = (
        ["Reported_Temperature"] if sensor_ids is None
        else [f"Sensor_{device_id}_Temperature" for device_id in sensor_ids]
    )
    csv_writer.writerow([
        "Time",
        "Actual_Temperature",
        *temperature_columns,
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
    # main.py supplies the same device order used to create the CSV header.
    temperature_values = (
        list(reported_temperature.values())
        if isinstance(reported_temperature, dict)
        else [reported_temperature]
    )
    csv_writer.writerow([
        elapsed_time,
        actual_temperature,
        *temperature_values,
        cooling_active,
        high_temp_alarm,
        next_temperature
    ])

    csv_file.flush()


def close_log(logger):
    csv_file, _ = logger
    csv_file.close()
