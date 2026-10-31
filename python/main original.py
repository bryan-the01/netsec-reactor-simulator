
import time


# ==========================================
# REACTOR CONFIGURATION
# ==========================================

temperature = 60.0        # Initial temperature (°C)
cooling_active = False    # Cooling starts OFF

cooling_on_threshold = 80.0
cooling_off_threshold = 70.0

delta_time = 1.0          # Simulation time step (seconds)
simulation_duration = 60  # Total simulation steps


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
# TEMPORARY CONTROLLER (FUTURE OPENPLC)
# ==========================================

def update_cooling_state(
    sensor_reading,
    cooling_active
):
    """
    Temporary Python controller.

    This logic will eventually be implemented
    in OpenPLC using ladder logic.
    """

    if sensor_reading >= cooling_on_threshold:
        return True

    if sensor_reading <= cooling_off_threshold:
        return False

    return cooling_active


# ==========================================
# MAIN SIMULATION LOOP
# ==========================================

print("====================================")
print(" SIMPLIFIED REACTOR THERMAL CONTROL")
print("====================================")

for second in range(simulation_duration):

    # Step 1: Read simulated temperature sensor
    sensor_reading = temperature

    # Step 2: Temporary controller decides cooling
    cooling_active = update_cooling_state(
        sensor_reading,
        cooling_active
    )

    # Step 3: Calculate physical heating and cooling
    heating_rate = calculate_heat_rate()
    cooling_rate = calculate_cool_rate()

    # Step 4: Update physical reactor temperature
    temperature = calculate_temperature(
        temperature,
        heating_rate,
        cooling_rate,
        cooling_active,
        delta_time
    )

    # Step 5: Display simulation results
    cooling_status = "ON" if cooling_active else "OFF"

    print(
        f"Time: {second + 1:02d}s | "
        f"Temperature: {temperature:.1f}°C | "
        f"Cooling: {cooling_status}"
    )

    # Step 6: Wait until next simulation step
    time.sleep(delta_time)


print("\nSimulation complete.")
