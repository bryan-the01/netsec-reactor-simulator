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