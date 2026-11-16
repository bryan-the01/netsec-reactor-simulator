class Reactor:
    def __init__(self, initial_temperature):
        self.temperature = initial_temperature

    def calculate_heat_rate(self):
        # Reactor heating rate in °C/s
        return 2.0

    def calculate_cool_rate(self):
        # Cooling rate in °C/s when cooling is active
        return 4.0

    def update(self, cooling_active, delta_time):
        # Calculate physical heating and cooling rates
        heating_rate = self.calculate_heat_rate()
        cooling_rate = self.calculate_cool_rate()

        # Apply cooling only when commanded by the PLC
        cooling_multiplier = int(cooling_active)

        temperature_change = (
            heating_rate - cooling_rate * cooling_multiplier
        ) * delta_time

        # Update this reactor's temperature
        self.temperature += temperature_change