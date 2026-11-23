"""Run three temperature devices and a cooling actuator on one reactor."""
import asyncio
import time

import config
import data_logger
import reactor
from temperature_sensor import TemperatureSensor
from cooling_actuator import CoolingActuator
from modbus_sensor_server import ModbusSensorServer


async def wait_for_plc(sensor_io, actuator):
    """Hold simulated time until all device paths have recent activity.

    This observes valid Modbus operations, not authenticated PLC identity
    or the HMI connection. It is a startup check, not a runtime watchdog.
    """
    started = time.monotonic()
    next_status = started
    while True:
        now = time.monotonic()
        missing_sensors = [
            device_id for device_id in sensor_io.read_measurements
            if now - sensor_io.last_poll_at.get(device_id, float("-inf"))
            > config.PLC_STARTUP_MAX_AGE
        ]
        latest_first_poll = max(sensor_io.first_poll_at.values(), default=float("inf"))
        command_ready = (
            actuator.last_command_at is not None
            and now - actuator.last_command_at <= config.PLC_STARTUP_MAX_AGE
            and actuator.last_command_at >= latest_first_poll
        )
        if not missing_sensors and command_ready:
            print(
                f"Communication ready after {now - started:.1f}s. "
                "Starting reactor simulation at t=0.",
                flush=True,
            )
            return

        pending = []
        if missing_sensors:
            pending.append(f"recent polls for sensor IDs {missing_sensors}")
        if not command_ready:
            pending.append("a recent cooling command after the initial sensor polls")
        status = "; ".join(pending)
        if now - started >= config.PLC_STARTUP_TIMEOUT:
            raise TimeoutError(
                f"PLC startup timed out: waiting for {status}. "
                "Reactor simulation was not started. Check PLC RUN state "
                "and Remote Device settings."
            )
        if now >= next_status:
            print(f"Waiting for PLC communication: {status}", flush=True)
            next_status = now + 1.0
        await asyncio.sleep(0.05)


async def simulation_loop(plant, sensor_io, actuator, logger):
    for step in range(config.simulation_duration):
        # Let the sensor refresh and OpenPLC poll/write while time passes.
        await asyncio.sleep(config.delta_time)

        actual_temperature = plant.temperature
        # This is the sensor's exposed measurement, not a PLC readback.
        reported_temperatures = {
            device_id: value / 10.0
            for device_id, value in sensor_io.get_measurements().items()
        }
        cooling_active = actuator.cooling_active

        plant.update(cooling_active, config.delta_time)

        elapsed_time = (step + 1) * config.delta_time
        cooling_status = "ON" if cooling_active else "OFF"
        sensor_status = " | ".join(
            f"Sensor {device_id}: {value:.1f} C"
            for device_id, value in reported_temperatures.items()
        )
        print(
            f"Time: {elapsed_time:.1f}s | "
            f"Temperature: {plant.temperature:.1f} C | "
            f"{sensor_status} | "
            f"Cooling applied: {cooling_status}",
            flush=True,
        )

        data_logger.write_row(
            logger,
            elapsed_time,
            actual_temperature,
            reported_temperatures,
            cooling_active,
            None,  # Alarm remains inside OpenPLC; CSV field is blank.
            plant.temperature,
        )


async def main():
    if config.delta_time <= 0 or config.simulation_duration <= 0:
        raise ValueError("delta_time and simulation_duration must be positive")
    if config.PLC_STARTUP_TIMEOUT <= 0 or config.PLC_STARTUP_MAX_AGE <= 0:
        raise ValueError("PLC startup timeout and maximum age must be positive")

    plant = reactor.Reactor(initial_temperature=config.temperature)
    # Independent simulated instruments measuring the same physical reactor.
    temperature_sensors = {
        1: TemperatureSensor(plant),
        2: TemperatureSensor(plant),
        3: TemperatureSensor(plant),
    }
    if config.SENSOR_ATTACK_ENABLED:
        if config.COMPROMISED_SENSOR_ID not in temperature_sensors:
            raise ValueError("COMPROMISED_SENSOR_ID must be 1, 2, or 3")
        temperature_sensors[
            config.COMPROMISED_SENSOR_ID
        ].fixed_reported_temperature = config.FALSE_TEMPERATURE
    sensor_io = ModbusSensorServer(
        read_measurements={
            device_id: instrument.read_temperature
            for device_id, instrument in temperature_sensors.items()
        },
        host="127.0.0.1", port=1502,
    )
    actuator = CoolingActuator(host="127.0.0.1", port=1503, device_id=1)

    print("====================================", flush=True)
    print(" SIMPLIFIED REACTOR THERMAL CONTROL", flush=True)
    print("====================================", flush=True)
    print("Temperature: port 1502, input register 0, device IDs 1/2/3", flush=True)
    print("Cooling: port 1503, coil 0, device 1", flush=True)
    if config.SENSOR_ATTACK_ENABLED:
        print(
            f"ATTACK: sensor {config.COMPROMISED_SENSOR_ID} reports a fixed "
            f"{config.FALSE_TEMPERATURE:.1f} C; other sensors remain honest.",
            flush=True,
        )
    else:
        print("Baseline: all sensors report honest measurements.", flush=True)
    print("OpenPLC must poll each sensor ID and write the cooling command.", flush=True)
    print("Sensor voting/isolation is not implemented by this Python launcher.", flush=True)
    print("Alarm logging unavailable; High_Temp_Alarm CSV cells are blank.", flush=True)

    log_filename = (
        f"sensor-{config.COMPROMISED_SENSOR_ID}-stuck.csv"
        if config.SENSOR_ATTACK_ENABLED else "baseline-three-sensors.csv"
    )
    print(f"CSV: results/{log_filename}", flush=True)
    logger = None
    try:
        # If any task fails, TaskGroup cancels the other tasks as well.
        async with asyncio.TaskGroup() as tasks:
            sensor_task = tasks.create_task(sensor_io.run())
            actuator_task = tasks.create_task(actuator.run())
            # Servers remain active while the physical model stays at t=0.
            await wait_for_plc(sensor_io, actuator)
            logger = data_logger.create_log(
                sensor_ids=tuple(temperature_sensors), filename=log_filename
            )
            loop_task = tasks.create_task(
                simulation_loop(plant, sensor_io, actuator, logger)
            )
            await loop_task
            # The finite simulation has completed; close both endpoints.
            sensor_task.cancel()
            actuator_task.cancel()
    finally:
        if logger is not None:
            data_logger.close_log(logger)

    print("\nSimulation complete.", flush=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nSimulation stopped.")
