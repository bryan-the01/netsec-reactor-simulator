import time
import csv
from pathlib import Path
from pymodbus.client import ModbusTcpClient

# ==========================================
# REACTOR CONFIGURATION
# ==========================================

temperature = 60.0        # Initial temperature (°C)
cooling_active = False    # Initial cooling state

delta_time = 1.0          # Simulation time step (seconds)
simulation_duration = 60  # Total simulation steps


# ==========================================
# MODBUS CONFIGURATION
# ==========================================

PLC_IP = "127.0.0.1"
PLC_PORT = 502
DEVICE_ID = 1

TEMPERATURE_REGISTER = 1024
COOLING_COIL = 0
ALARM_COIL = 1


# ==========================================
# PHYSICAL REACTOR SIMULATION (PYTHON)
# ==========================================

def calculate_heat_rate():
    """
    Returns the reactor's heating rate in °C/s.

    Future upgrade:
    Calculate heating based on reactor power,
    fission rate, and thermal properties.
    """
    return 2.0


def calculate_cool_rate():
    """
    Returns the cooling system's cooling rate
    in °C/s when cooling is active.

    Future upgrade:
    Model coolant flow, coolant temperature,
    and heat transfer.
    """
    return 4.0


def calculate_temperature(
    current_temperature,
    heating_rate,
    cooling_rate,
    cooling_active,
    delta_time
):
    """
    Calculates the reactor's next temperature.

    T_next = T_current + (H - C*A) * dt

    A = 1 when cooling is ON
    A = 0 when cooling is OFF
    """

    cooling_multiplier = int(cooling_active)

    temperature_change = (
        heating_rate - cooling_rate * cooling_multiplier
    ) * delta_time

    return current_temperature + temperature_change


# ==========================================
# MODBUS CONNECTION
# ==========================================

client = ModbusTcpClient(PLC_IP, port=PLC_PORT)

if not client.connect():
    raise ConnectionError("Could not connect to OpenPLC")


# ==========================================
# MAIN SIMULATION LOOP
# ==========================================

print("====================================")
print(" SIMPLIFIED REACTOR THERMAL CONTROL")
print("====================================")

# ==========================================
# CSV BASELINE LOGGING
# ==========================================

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

try:
    for second in range(simulation_duration):

        # Step 1: Read simulated temperature sensor
        sensor_reading = temperature

        # Step 2: Convert temperature to scaled integer
        temperature_x10 = round(sensor_reading * 10)

        # Step 3: Send temperature to OpenPLC
        write_response = client.write_register(
            address=TEMPERATURE_REGISTER,
            value=temperature_x10,
            device_id=DEVICE_ID
        )

        if write_response.isError():
            raise RuntimeError(
                f"Modbus write failed: {write_response}"
            )

        # Step 4: Allow PLC to process the measurement
        time.sleep(0.1)

        # Step 5: Read cooling and alarm states
        read_response = client.read_coils(
            address=COOLING_COIL,
            count=2,
            device_id=DEVICE_ID
        )

        if read_response.isError():
            raise RuntimeError(
                f"Modbus read failed: {read_response}"
            )

        cooling_active = read_response.bits[0]
        high_temp_alarm = read_response.bits[1]

        # Step 6: Calculate physical heating and cooling
        heating_rate = calculate_heat_rate()
        cooling_rate = calculate_cool_rate()

        # Step 7: Update physical reactor temperature
        temperature = calculate_temperature(
            temperature,
            heating_rate,
            cooling_rate,
            cooling_active,
            delta_time
        )

        # Step 8.5: Record simulation data
        csv_writer.writerow([
            (second + 1) * delta_time,
            sensor_reading,
            temperature_x10 / 10.0,
            cooling_active,
            high_temp_alarm,
            temperature
        ])

        csv_file.flush()

        # Step 8: Display simulation results
        cooling_status = "ON" if cooling_active else "OFF"
        alarm_status = "ON" if high_temp_alarm else "OFF"

        print(
            f"Time: {second + 1:02d}s | "
            f"Temperature: {temperature:.1f}°C | "
            f"Cooling: {cooling_status} | "
            f"Alarm: {alarm_status}"
        )

        # Step 9: Wait until next simulation step
        time.sleep(delta_time)

finally:
    client.close()
    csv_file.close()


print("\nSimulation complete.")
