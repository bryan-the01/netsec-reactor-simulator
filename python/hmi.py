import tkinter as tk
import config, plc_module
from datetime import datetime


class HMI:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Reactor — Operator Panel")
        self.window.geometry("440x340")

        self.plc = plc_module.PLCModule(
        ip=config.PLC_IP,
        port=config.PLC_PORT,
        device_id=config.DEVICE_ID,
        temperature_register=config.TEMPERATURE_REGISTER,
        cooling_coil=config.COOLING_COIL,
        alarm_coil=config.ALARM_COIL
    )

        self.connection_text = tk.StringVar(value="NOT CONNECTED")
        self.temperature_text = tk.StringVar(value="--.- °C")
        self.cooling_text = tk.StringVar(value="Cooling: UNKNOWN")
        self.alarm_text = tk.StringVar(value="High-temp alarm: UNKNOWN")
        self.last_update_text = tk.StringVar(
            value="Last successful update: --"
        )

        tk.Label(
            self.window,
            text = "REACTOR — OPERATOR PANEL",
            font = ("Arial", 16, "bold")
        ).pack(pady=15)

        self.connection_label = tk.Label(
            self.window,
            textvariable=self.connection_text,
            fg="gray"
        )
        self.connection_label.pack()

        tk.Label(
            self.window,
            text = "TEMPERATURE",
            font = ("Arial", 12)
        ).pack(pady=(20, 0))

        tk.Label(
            self.window,
            textvariable = self.temperature_text,
            font = ("Arial", 32, "bold")
        ).pack()

        tk.Label(
            self.window,
            textvariable = self.cooling_text,
            font=("Arial", 14)
        ).pack(pady=10)

        self.alarm_label = tk.Label(
            self.window,
            textvariable = self.alarm_text,
            font=("Arial", 14)
        )
        self.alarm_label.pack()

        tk.Label(
            self.window,
            textvariable = self.last_update_text
        ).pack(pady=20)

    def update_values(
        self,
        temperature,
        cooling_active,
        high_temp_alarm
    ):
        # Display values obtained from OpenPLC.
        self.temperature_text.set(f"{temperature:.1f} °C")

        cooling_status = "ON" if cooling_active else "OFF"
        alarm_status = "ON" if high_temp_alarm else "OFF"

        self.cooling_text.set(f"Cooling: {cooling_status}")
        self.alarm_text.set(f"High-temp alarm: {alarm_status}")

        self.alarm_label.config(
            fg="red" if high_temp_alarm else "black"
        )

        self.connection_text.set("CONNECTED")
        self.connection_label.config(fg="green")

        timestamp = datetime.now().strftime("%H:%M:%S")
        self.last_update_text.set(
            f"Last successful update: {timestamp}"
        )

    def poll_plc(self):
        try:
            self.plc.connect()

            temperature = self.plc.read_temperature()
            cooling_active = self.plc.read_cooling_command()
            high_temp_alarm = self.plc.read_high_temp_alarm()

            self.update_values(
                temperature,
                cooling_active,
                high_temp_alarm
            )

        except Exception:
            print(f"HMI update failed: {error}")
            self.mark_stale()

        # Schedule another read in 1,000 milliseconds.
        self.window.after(1000, self.poll_plc)

    def mark_stale(self):
        # Retain the last values, but flag them as stale.
        self.connection_text.set("UPDATE FAILED — VALUES STALE")
        self.connection_label.config(fg="red")

    def run(self):
        self.window.after(0, self.poll_plc)
        
        try:
            self.window.mainloop()
        finally:
            self.plc.close()


# Preview the panel without connecting to OpenPLC.
if __name__ == "__main__":
    panel = HMI()
    panel.run()