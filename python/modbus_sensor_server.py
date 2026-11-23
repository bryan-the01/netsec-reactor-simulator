"""Expose multiple sensor devices on one TCP port (PyModbus 3.11.1)."""
import asyncio
import time
from contextlib import suppress

from pymodbus.datastore import (
    ModbusDeviceContext,
    ModbusSequentialDataBlock,
    ModbusServerContext,
)
from pymodbus.server import ModbusTcpServer


class _SensorDeviceContext(ModbusDeviceContext):
    def __init__(self, block, on_poll):
        super().__init__(ir=block)
        self.on_poll = on_poll

    def getValues(self, fc_as_hex, address, count=1):
        result = super().getValues(fc_as_hex, address, count)
        if fc_as_hex == 4 and address == 0 and count == 1 and isinstance(result, list):
            self.on_poll()
        return result


class ModbusSensorServer:
    def __init__(self, read_measurements, host="127.0.0.1", port=1502,
                 sample_interval=0.1):
        if sample_interval <= 0:
            raise ValueError("sample_interval must be positive")
        if not read_measurements:
            raise ValueError("At least one sensor is required")
        if any(type(device_id) is not int or not 1 <= device_id <= 247
               for device_id in read_measurements):
            raise ValueError("Sensor device IDs must be integers from 1 to 247")
        self.read_measurements = dict(read_measurements)
        self.address = (host, port)
        self.sample_interval = sample_interval
        self.started_at = time.monotonic()
        self.first_poll_at = {}
        self.last_poll_at = {}
        # PyModbus 3.11.1 maps wire offset 0 to internal address 1.
        self.registers = {}
        devices = {}
        for device_id, read_measurement in self.read_measurements.items():
            block = ModbusSequentialDataBlock(1, [self._sample(read_measurement)])
            self.registers[device_id] = block
            devices[device_id] = _SensorDeviceContext(
                block, lambda device_id=device_id: self._record_poll(device_id)
            )
        self.context = ModbusServerContext(
            devices=devices, single=False
        )

    def _record_poll(self, device_id):
        now = time.monotonic()
        self.last_poll_at[device_id] = now
        if device_id not in self.first_poll_at:
            self.first_poll_at[device_id] = now
            print(
                f"Sensor {device_id}: first input-register poll serviced "
                f"after {now - self.started_at:.1f}s",
                flush=True,
            )

    def _sample(self, read_measurement):
        value = read_measurement()
        if not isinstance(value, int) or not 0 <= value <= 65535:
            raise ValueError("Measurement must be an integer from 0 to 65535")
        return value

    def get_measurements(self):
        """Local exposed readings by ID; these are not PLC readbacks."""
        return {
            device_id: block.getValues(1, count=1)[0]
            for device_id, block in self.registers.items()
        }

    async def _update_measurement(self):
        while True:
            # Local update only: no outgoing network writes to OpenPLC.
            for device_id, read_measurement in self.read_measurements.items():
                self.registers[device_id].setValues(
                    1, [self._sample(read_measurement)]
                )
            await asyncio.sleep(self.sample_interval)

    async def run(self):
        server = ModbusTcpServer(self.context, address=self.address)
        updater = asyncio.create_task(self._update_measurement())
        listener = asyncio.create_task(server.serve_forever())
        try:
            done, _ = await asyncio.wait(
                (updater, listener), return_when=asyncio.FIRST_COMPLETED
            )
            for task in done:
                task.result()
        finally:
            updater.cancel()
            listener.cancel()
            for task in (updater, listener):
                with suppress(asyncio.CancelledError):
                    await task
            await server.shutdown()
