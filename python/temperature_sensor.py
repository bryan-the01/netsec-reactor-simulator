from builtins import round

class TemperatureSensor:
    def __init__(self, reactor, fixed_reported_temperature=None):
        self.reactor = reactor
        # None = honest measurement. A value simulates a stuck/compromised output.
        self.fixed_reported_temperature = fixed_reported_temperature

    def read_temperature(self):
        # Read the actual temperature from the assigned reactor
        sensor_reading = self.reactor.temperature

        # Alter only the reported reading, never the physical reactor state.
        if self.fixed_reported_temperature is not None:
            sensor_reading = self.fixed_reported_temperature

        # Scale for the PLC register: 60.5°C becomes 605
        temperature_x10 = round(sensor_reading * 10)

        return temperature_x10
