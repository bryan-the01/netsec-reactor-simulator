from pymodbus.client import ModbusTcpClient

class PLCModule:
    def __init__(
        self,
        ip,
        port,
        device_id,
        temperature_register,
        cooling_coil,
        alarm_coil
    ):
        self.device_id = device_id
        self.temperature_register = temperature_register
        self.cooling_coil = cooling_coil
        self.alarm_coil = alarm_coil
        self.client = ModbusTcpClient(ip, port=port)

    def connect(self):
        if not self.client.connect():
            raise ConnectionError("Could not connect to OpenPLC")

    def write_temperature(self, temperature_x10):
        # Send the scaled sensor measurement to OpenPLC
        write_response = self.client.write_register(
            address=self.temperature_register,
            value=temperature_x10,
            device_id=self.device_id
        )

        if write_response.isError():
            raise RuntimeError(
                f"Modbus write failed: {write_response}"
            )

    def read_temperature(self):
        # Read the measurement stored in OpenPLC.
        read_response = self.client.read_holding_registers(
            address=self.temperature_register,
            count=1,
            device_id=self.device_id
        )

        if read_response.isError():
            raise RuntimeError(
                f"Temperature read failed: {read_response}"
            )

        return read_response.registers[0] / 10.0

    def read_cooling_command(self):
        # Read the cooling command
        cooling_response = self.client.read_coils(
            address=self.cooling_coil,
            count=1,
            device_id=self.device_id
        )

        if cooling_response.isError():
            raise RuntimeError(
                f"Cooling coil read failed: {cooling_response}"
            )

        cooling_active = cooling_response.bits[0]
        return cooling_active

    def read_high_temp_alarm(self):
        # Read the high-temperature alarm
        alarm_response = self.client.read_coils(
            address=self.alarm_coil,
            count=1,
            device_id=self.device_id
        )

        if alarm_response.isError():
            raise RuntimeError(
                f"Alarm coil read failed: {alarm_response}"
            )

        high_temp_alarm = alarm_response.bits[0]
        return high_temp_alarm

    def close(self):
        self.client.close()

class GRFICSVisualizerBridge:
    def __init__(self, ip, port, pressure_reg, valve_reg):
        self.valve_reg = valve_reg  # Address 1 (confirmed in modbusdevice.py)
        # Feed 2 (192.168.95.11) = Cooling flow into reactor
        self.cooling_client = ModbusTcpClient(ip, port=port)
        # Purge (192.168.95.12) = Heat/steam relief proportional to reactor temp
        self.purge_client = ModbusTcpClient("192.168.95.12", port=port)

    def connect(self):
        if not self.cooling_client.connect():
            raise ConnectionError("Could not connect to GRFICSv3 Feed 2 (192.168.95.11)")
        if not self.purge_client.connect():
            raise ConnectionError("Could not connect to GRFICSv3 Purge (192.168.95.12)")

    def sync_reactor_state(self, temperature_c, cooling_active):
        # GRFICSv3 computes (value / 65535.0) * 100.0 from Holding Register 1
        cooling_sp = 65535 if cooling_active else 0

        # Scale reactor temperature (50°C to 110°C) into 0-65535 for the purge valve
        temp_ratio = max(0.0, min(1.0, (temperature_c - 50.0) / 60.0))
        purge_sp = int(temp_ratio * 65535)

        self.cooling_client.write_register(address=self.valve_reg, value=cooling_sp, device_id=1)
        self.purge_client.write_register(address=self.valve_reg, value=purge_sp, device_id=1)

    def close(self):
        self.cooling_client.close()
        self.purge_client.close()
