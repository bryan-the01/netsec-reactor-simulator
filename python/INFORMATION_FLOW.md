# Current information flow

## Working simulation

1. Reactor owns and updates the actual simulated temperature.
2. TemperatureSensor reads that reactor state and returns temperature scaled by 10.
3. Main schedules the operations. It is simulation orchestration, not a physical device.
4. PLCModule is the Python Modbus TCP client interface. It writes the scaled measurement to OpenPLC holding register 1024.
5. OpenPLC is the Modbus TCP server and runs the control logic. It determines cooling and high-temperature alarm states.
6. Python requests the cooling command from coil 0 and the alarm state from coil 1.
7. The reactor applies the cooling command when advancing its temperature.
8. The CSV logger records actual temperature, reported temperature, PLC outputs, and next temperature for experiment evaluation.

Python initiates both the temperature write and the output reads. The output values return from OpenPLC in response to those reads. PLCModule is a communication interface, not the PLC control program.

## Agreed HMI design (not yet connected)

The HMI will run independently and poll OpenPLC through its own client connection.
It will read temperature and cooling/alarm status from the PLC, not directly from
the sensor or reactor. It will show connection/update status and identify stale data.

Sensor -> Python Modbus write -> OpenPLC
HMI -> Modbus read requests -> OpenPLC -> responses -> HMI display
OpenPLC -> cooling response to Python -> reactor update

## Ground truth and future FDI experiment

Actual reactor temperature is simulation ground truth for CSV evaluation. It must
not be used as an independent live temperature source for the operator HMI or as
an automatic correction to the PLC measurement.

The planned communication-path FDI experiment will keep the sensor honest and
alter the measurement delivered to OpenPLC. If that value is altered before it
reaches the PLC, both PLC control and the HMI reading that register see the
altered value. Simulation-side value manipulation is not actual network interception.

An independent HMI-to-sensor monitoring path is not part of the current design;
it could be explored later as a separate discrepancy-detection mechanism.

## Architecture decision

Keep the working Python-client / OpenPLC-server arrangement. A common alternative
is for the PLC to poll sensor or remote I/O servers and command actuator outputs.
The current arrangement is a deliberate simulated-plant coupling choice, not a
claim to reproduce that alternative's exact field-device communication roles.
