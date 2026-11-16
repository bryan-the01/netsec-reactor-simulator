import time
import sensor, plc_module, reactor, config, data_logger


# ==========================================
# Initial configuration
# ==========================================

plant = reactor.Reactor(
    initial_temperature = config.temperature
)

temperature_sensor = sensor.TemperatureSensor(plant)

plc = plc_module.PLCModule(
    ip = config.PLC_IP,
    port = config.PLC_PORT,
    device_id = config.DEVICE_ID,
    temperature_register = config.TEMPERATURE_REGISTER,
    cooling_coil = config.COOLING_COIL,
    alarm_coil = config.ALARM_COIL
)

cooling_active = config.cooling_active
high_temp_alarm = config.high_temp_alarm
simulation_duration = config.simulation_duration
delta_time = config.delta_time


# ==========================================
# MAIN SIMULATION LOOP
# ==========================================

print("====================================")
print(" SIMPLIFIED REACTOR THERMAL CONTROL")
print("====================================")

logger = None

try:
    plc.connect()
    logger = data_logger.create_log()

    for step in range(simulation_duration):

        # Step 1: Record actual temperature before the update
        actual_temperature = plant.temperature

        # Step 2: Read the scaled sensor measurement
        temperature_x10 = temperature_sensor.read_temperature()

        # Step 3: Send temperature to OpenPLC
        plc.write_temperature(temperature_x10)

        # Step 4: Allow PLC to process the measurement
        time.sleep(0.1)

        # Step 5: Read cooling and alarm states
        cooling_active = plc.read_cooling_command()
        high_temp_alarm = plc.read_high_temp_alarm()

        # Step 6–7: Calculate heating/cooling and update the reactor
        plant.update(cooling_active, delta_time)

        # Step 8: Display simulation results
        elapsed_time = (step + 1) * delta_time
        cooling_status = "ON" if cooling_active else "OFF"
        alarm_status = "ON" if high_temp_alarm else "OFF"

        print(
            f"Time: {elapsed_time:.1f}s | "
            f"Temperature: {plant.temperature:.1f}°C | "
            f"Cooling: {cooling_status} | "
            f"Alarm: {alarm_status}"
        )

        # Record simulation data
        data_logger.write_row(
            logger,
            elapsed_time,
            actual_temperature,
            temperature_x10 / 10.0,
            cooling_active,
            high_temp_alarm,
            plant.temperature
        )

        # Step 9: Wait until next simulation step
        time.sleep(delta_time)

finally:
    try:
        plc.close()
    finally:
        if logger is not None:
            data_logger.close_log(logger)


print("\nSimulation complete.")