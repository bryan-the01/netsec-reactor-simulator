import tkinter as tk
from datetime import datetime

from pymodbus.client import ModbusTcpClient

import config


class HMI:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Reactor — Operator Panel")
        self.window.geometry("600x570")

        self.client = ModbusTcpClient(
            config.PLC_IP,
            port=config.PLC_PORT,
            timeout=1,
        )
        self.device_id = config.DEVICE_ID

        self.connection_text = tk.StringVar(
            value="NOT CONNECTED"
        )
        self.temperature_text = tk.StringVar(
            value="--.- °C"
        )
        self.voting_text = tk.StringVar(
            value="Voting: UNKNOWN"
        )
        self.cooling_text = tk.StringVar(
            value="Cooling command: UNKNOWN"
        )
        self.alarm_text = tk.StringVar(
            value="High-temp alarm: UNKNOWN"
        )
        self.fault_text = tk.StringVar(
            value="Sensor fault alarm: UNKNOWN"
        )
        self.last_update_text = tk.StringVar(
            value="Last successful PLC read: --"
        )

        tk.Label(
            self.window,
            text="REACTOR — OPERATOR PANEL",
            font=("Arial", 17, "bold"),
        ).pack(pady=15)

        self.connection_label = tk.Label(
            self.window,
            textvariable=self.connection_text,
            fg="gray",
        )
        self.connection_label.pack()

        tk.Label(
            self.window,
            text="PLC VOTED TEMPERATURE",
            font=("Arial", 11),
        ).pack(pady=(15, 0))

        self.temperature_label = tk.Label(
            self.window,
            textvariable=self.temperature_text,
            font=("Arial", 32, "bold"),
        )
        self.temperature_label.pack()

        self.voting_label = tk.Label(
            self.window,
            textvariable=self.voting_text,
        )
        self.voting_label.pack()

        sensor_frame = tk.LabelFrame(
            self.window,
            text="Sensor measurements received by PLC",
            padx=15,
            pady=10,
        )
        sensor_frame.pack(
            fill="x",
            padx=20,
            pady=15,
        )

        self.sensor_values = []
        self.sensor_statuses = []
        self.sensor_status_labels = []

        for index in range(3):
            value = tk.StringVar(value="--.- °C")
            status = tk.StringVar(value="UNKNOWN")

            tk.Label(
                sensor_frame,
                text=f"Sensor {index + 1}",
            ).grid(
                row=index,
                column=0,
                padx=10,
                pady=5,
            )

            tk.Label(
                sensor_frame,
                textvariable=value,
                font=("Arial", 13, "bold"),
            ).grid(
                row=index,
                column=1,
                padx=15,
            )

            status_label = tk.Label(
                sensor_frame,
                textvariable=status,
            )
            status_label.grid(
                row=index,
                column=2,
                padx=10,
            )

            self.sensor_values.append(value)
            self.sensor_statuses.append(status)
            self.sensor_status_labels.append(status_label)

        tk.Label(
            self.window,
            textvariable=self.cooling_text,
            font=("Arial", 13),
        ).pack(pady=5)

        self.alarm_label = tk.Label(
            self.window,
            textvariable=self.alarm_text,
        )
        self.alarm_label.pack(pady=5)

        self.fault_label = tk.Label(
            self.window,
            textvariable=self.fault_text,
        )
        self.fault_label.pack(pady=5)

        tk.Label(
            self.window,
            textvariable=self.last_update_text,
        ).pack(pady=15)

    def check_response(self, response, description):
        if response.isError():
            raise RuntimeError(
                f"{description}: {response}"
            )
        return response

    def read_plc(self):
        # %IW0, %IW1, %IW2: individual sensor measurements.
        sensors = self.check_response(
            self.client.read_input_registers(
                address=0,
                count=3,
                device_id=self.device_id,
            ),
            "Sensor read failed",
        )

        # %MW0: voted temperature, scaled by 10.
        voted = self.check_response(
            self.client.read_holding_registers(
                address=1024,
                count=1,
                device_id=self.device_id,
            ),
            "Voted-temperature read failed",
        )

        # %QX0.0 through %QX0.6: outputs and voting flags.
        outputs = self.check_response(
            self.client.read_coils(
                address=0,
                count=7,
                device_id=self.device_id,
            ),
            "PLC status read failed",
        )

        return (
            [value / 10.0 for value in sensors.registers],
            voted.registers[0] / 10.0,
            [bool(value) for value in outputs.bits[:7]],
        )

    def update_values(self, temperatures, voted, flags):
        (
            cooling,
            high_alarm,
            voting_valid,
            rejected1,
            rejected2,
            rejected3,
            sensor_fault,
        ) = flags

        self.connection_text.set("PLC READ SUCCESSFUL")
        self.connection_label.config(fg="green")

        if voting_valid:
            self.temperature_text.set(f"{voted:.1f} °C")
            self.temperature_label.config(fg="black")
            self.voting_text.set("Voting: AGREEMENT FOUND")
            self.voting_label.config(fg="green")
        else:
            self.temperature_text.set("UNAVAILABLE")
            self.temperature_label.config(fg="red")
            self.voting_text.set(
                "Voting: NO AGREEMENT — COOLING FALLBACK"
            )
            self.voting_label.config(fg="red")

        rejected_flags = [
            rejected1,
            rejected2,
            rejected3,
        ]

        for index, temperature in enumerate(temperatures):
            self.sensor_values[index].set(
                f"{temperature:.1f} °C"
            )

            if not voting_valid:
                status = "NO CONSENSUS"
                color = "red"
            elif rejected_flags[index]:
                status = "REJECTED"
                color = "red"
            else:
                status = "WITHIN TOLERANCE"
                color = "green"

            self.sensor_statuses[index].set(status)
            self.sensor_status_labels[index].config(
                fg=color
            )

        self.cooling_text.set(
            f"Cooling command: {'ON' if cooling else 'OFF'}"
        )

        if voting_valid:
            self.alarm_text.set(
                f"High-temp alarm: {'ON' if high_alarm else 'OFF'}"
            )
        else:
            self.alarm_text.set(
                "High-temp assessment: UNAVAILABLE"
            )

        self.alarm_label.config(
            fg="red" if high_alarm or not voting_valid else "black"
        )

        self.fault_text.set(
            f"Sensor fault alarm: {'ON' if sensor_fault else 'OFF'}"
        )
        self.fault_label.config(
            fg="red" if sensor_fault else "black"
        )

        timestamp = datetime.now().strftime("%H:%M:%S")
        self.last_update_text.set(
            f"Last successful PLC read: {timestamp}"
        )

    def poll_plc(self):
        try:
            if not self.client.connect():
                raise ConnectionError(
                    "Could not connect to OpenPLC"
                )

            self.update_values(*self.read_plc())

        except Exception as error:
            print(f"HMI update failed: {error}")
            self.client.close()
            self.mark_stale()

        self.window.after(1000, self.poll_plc)

    def mark_stale(self):
        self.connection_text.set(
            "PLC READ FAILED — ALL DISPLAYED VALUES STALE"
        )
        self.connection_label.config(fg="red")

        for status, label in zip(
            self.sensor_statuses,
            self.sensor_status_labels,
        ):
            status.set("STALE")
            label.config(fg="gray")

    def run(self):
        self.window.after(0, self.poll_plc)

        try:
            self.window.mainloop()
        finally:
            self.client.close()


if __name__ == "__main__":
    HMI().run()