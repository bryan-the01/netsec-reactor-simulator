import time
from pymodbus.client import ModbusTcpClient

client = ModbusTcpClient("127.0.0.1", port=502)

if not client.connect():
    raise ConnectionError("Could not connect to OpenPLC")

try:
    # Send 85.0°C as a scaled integer
    write_response = client.write_register(
        address=1024,
        value=850,
        device_id=1
    )

    if write_response.isError():
        raise RuntimeError(f"Write failed: {write_response}")

    # Read cooling and alarm states
    read_response = client.read_coils(
        address=0,
        count=2,
        device_id=1
    )

    if read_response.isError():
        raise RuntimeError(f"Read failed: {read_response}")

    print("Temperature sent: 85.0°C")
    print("Cooling ON:", read_response.bits[0])
    print("High Temp Alarm:", read_response.bits[1])

finally:
    client.close()
