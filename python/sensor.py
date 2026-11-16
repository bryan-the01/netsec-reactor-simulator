class TemperatureSensor:
    def __init__(self, reactor):
        self.reactor = reactor

    def read_temperature(self):
        # Read the actual temperature from the assigned reactor
        sensor_reading = self.reactor.temperature

        # Scale for the PLC register: 60.5°C becomes 605
        temperature_x10 = round(sensor_reading * 10)

        return temperature_x10