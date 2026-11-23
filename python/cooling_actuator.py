"""Simulated cooling actuator: Modbus TCP coil 0, port 1503.

OpenPLC writes the command; the reactor simulation reads cooling_active.
Requires PyModbus 3.11.1. This module makes no control decisions.
"""
import argparse
import asyncio
import time
from contextlib import suppress

from pymodbus.datastore import (
    ModbusDeviceContext,
    ModbusSequentialDataBlock,
    ModbusServerContext,
)
from pymodbus.server import ModbusTcpServer


class _ActuatorDeviceContext(ModbusDeviceContext):
    def __init__(self, block, on_command):
        super().__init__(co=block)
        self.on_command = on_command

    def setValues(self, fc_as_hex, address, values):
        result = super().setValues(fc_as_hex, address, values)
        if result is None and fc_as_hex in (5, 15) and address == 0 and len(values) == 1:
            self.on_command()
        return result


class CoolingActuator:
    def __init__(self, host="127.0.0.1", port=1503, device_id=1):
        self.address = (host, port)
        self.started_at = time.monotonic()
        self.first_command_at = None
        self.last_command_at = None
        # Wire offset 0 maps to internal datastore address 1 in 3.11.1.
        self.coils = ModbusSequentialDataBlock(1, [False])
        self.store = _ActuatorDeviceContext(self.coils, self._record_command)
        self.context = ModbusServerContext(
            devices={device_id: self.store}, single=False
        )

    def _record_command(self):
        now = time.monotonic()
        self.last_command_at = now
        if self.first_command_at is None:
            self.first_command_at = now
            print(
                f"Actuator: first cooling command received "
                f"after {now - self.started_at:.1f}s",
                flush=True,
            )

    @property
    def cooling_active(self):
        """Latest PLC command; False until the first ON command arrives.

        The last command is retained if the PLC disconnects. A command
        timeout/fail-safe policy is not implemented in this first version.
        """
        return bool(self.coils.getValues(1, count=1)[0])

    async def run(self):
        """Listen until stopped; call from the simulation's event loop."""
        server = ModbusTcpServer(self.context, address=self.address)
        try:
            await server.serve_forever()
        finally:
            await server.shutdown()

    async def _display_changes(self):
        previous = None
        while True:
            active = self.cooling_active
            if active != previous:
                print(f"Cooling command: {'ON' if active else 'OFF'}", flush=True)
                previous = active
            await asyncio.sleep(0.1)

    async def preview(self):
        """Standalone command receiver for checking OpenPLC writes."""
        display = asyncio.create_task(self._display_changes())
        try:
            await self.run()
        finally:
            display.cancel()
            with suppress(asyncio.CancelledError):
                await display


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=1503)
    parser.add_argument("--device-id", type=int, default=1)
    args = parser.parse_args()
    actuator = CoolingActuator(args.host, args.port, args.device_id)
    print(f"Cooling actuator endpoint: {args.host}:{args.port}", flush=True)
    print(f"Device ID {args.device_id}; coil offset 0; write FC 5 or FC 15.", flush=True)
    print("Command check only: reactor integration comes next. Ctrl+C to stop.", flush=True)
    try:
        asyncio.run(actuator.preview())
    except KeyboardInterrupt:
        print("Cooling actuator stopped.")


if __name__ == "__main__":
    main()
