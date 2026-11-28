# ==========================================
# REACTOR CONFIGURATION
# ==========================================

temperature = 60.0          # Initial temperature (°C)
cooling_active = False      # Initial cooling state
high_temp_alarm = False     # Initial 

delta_time = 1.0            # Simulation time step (seconds)
simulation_duration = 300    # Total simulation steps


# ==========================================
# MODBUS CONFIGURATION
# ==========================================

PLC_IP = "172.17.0.1"
PLC_PORT = 502
DEVICE_ID = 1

TEMPERATURE_REGISTER = 0
COOLING_COIL = 0
ALARM_COIL = 1

# ==========================================
# GRFICSv3 3D VISUALIZER CONFIGURATION
# ==========================================
GRFICS_ENABLED = True
GRFICS_SIM_IP = "192.168.95.11" # Reactor/tank remote IO IP in GRFICS
GRFICS_SIM_PORT = 502

# Maps reactor variables to GRFICS holding registers
GRFICS_PRESSURE_REG = 0
GRFICS_COOLING_VALVE_REG = 1
