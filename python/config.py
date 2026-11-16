# ==========================================
# REACTOR CONFIGURATION
# ==========================================

temperature = 60.0          # Initial temperature (°C)
cooling_active = False      # Initial cooling state
high_temp_alarm = False     # Initial 

delta_time = 1.0            # Simulation time step (seconds)
simulation_duration = 60    # Total simulation steps


# ==========================================
# MODBUS CONFIGURATION
# ==========================================

PLC_IP = "127.0.0.1"
PLC_PORT = 502
DEVICE_ID = 1

TEMPERATURE_REGISTER = 1024
COOLING_COIL = 0
ALARM_COIL = 1


