# Simplified Reactor-Inspired Thermal Control System

A simulated Cyber-Physical System (CPS) developed using **Python, OpenPLC Runtime v4, and Modbus TCP**.

This project models a simplified reactor-inspired thermal regulation system, where a software-based Programmable Logic Controller (PLC) manages cooling based on simulated temperature measurements.

The primary research objective is to investigate **False Data Injection (FDI) attacks**, their effects on industrial control behavior, and potential detection and mitigation techniques.

> **Disclaimer:** This is an educational simulation. It does not model the complete physics, safety systems, or operational characteristics of a real nuclear reactor.

## 1. System Architecture

The project separates the simulated physical process from the industrial controller.

| Component | Responsibility |
|---|---|
| Python (`main.py`) | Simulates heating, cooling, and temperature changes |
| OpenPLC Runtime v4 | Executes the temperature regulation logic |
| Modbus TCP | Exchanges temperature measurements and cooling commands |
| CSV logging | Records simulation data for future analysis |

**Communication sequence:**

1. Python calculates the simulated reactor temperature.
2. Python transmits the temperature to OpenPLC through Modbus TCP.
3. OpenPLC evaluates the measurement using hysteresis control logic.
4. OpenPLC determines whether cooling should be ON or OFF.
5. Python retrieves the cooling command and updates the reactor temperature.
6. Simulation measurements are recorded in a CSV file.

The process repeats throughout the simulation.

## 2. Current Functionality

### Thermal Simulation

The initial prototype uses a simplified linear thermal model:

\[
T_{next} = T_{current} + (H - C \times A)\Delta t
\]

Where:

- \(T\): Reactor temperature in °C
- \(H\): Heating rate, currently 2°C/s
- \(C\): Cooling rate, currently 4°C/s
- \(A\): Cooling activation state (1 = ON, 0 = OFF)
- \(\Delta t\): Simulation time step, currently 1 second

The heating and cooling rates are intentionally simplified constants.

### PLC Hysteresis Controller

OpenPLC manages the cooling system using the following Structured Text logic:

```iecst
IF Temperature >= 80.0 THEN
    Cooling_ON := TRUE;
ELSIF Temperature <= 70.0 THEN
    Cooling_ON := FALSE;
END_IF;

High_Temp_Alarm := Temperature >= 90.0;
```

The controller follows three operating conditions:

- At or above 80°C: cooling activates.
- At or below 70°C: cooling deactivates.
- Between 70°C and 80°C: cooling retains its previous state.

This hysteresis behavior prevents unnecessary switching around a single threshold.

The high-temperature alarm activates at 90°C.

These thresholds are demonstration values, not real nuclear-reactor operating or safety limits.

## 3. Project Structure

```text
CPS Project/
├── OpenPLC/
│   ├── devices/
│   │   ├── configuration.json
│   │   ├── pin-mapping.json
│   │   └── servers/
│   │       └── Reactor_Modbus_Server.json
│   ├── pous/
│   │   └── programs/
│   │       └── main.st
│   └── project.json
├── python/
│   ├── main.py
│   ├── main original.py
│   └── test_modbus.py
├── results/
│   └── baseline.csv
├── .gitignore
└── README.md
```

**File descriptions:**

- `python/main.py`: Main closed-loop thermal simulation.
- `python/main original.py`: Original simulation retained for reference.
- `python/test_modbus.py`: Tests communication between Python and OpenPLC.
- `OpenPLC/`: OpenPLC Editor project files, including the controller program and device configuration.
- `results/baseline.csv`: Recorded normal-operation simulation data.

Generated OpenPLC build files are excluded from version control.

## 4. Requirements

The project was initially developed and tested on Windows 11.

Required software:

- Python 3
- OpenPLC Editor v4
- OpenPLC Runtime v4 (Community Edition)
- PyModbus
- Git (optional, for collaboration)

Official resources:

- [Python](https://www.python.org/downloads/)
- [OpenPLC](https://autonomylogic.com/products/openplc)
- [OpenPLC Runtime](https://autonomylogic.com/products/runtime)
- [PyModbus](https://pymodbus.readthedocs.io/)
- [Git](https://git-scm.com/)

Install the Python dependency:

```powershell
python -m pip install "pymodbus==3.16.1"
```

Version 3.16.1 is the PyModbus version used in the initial working environment.

## 5. OpenPLC Configuration

### Step 1: Open the PLC project

1. Install OpenPLC Editor v4.
2. Open the included `OpenPLC` project directory.
3. Verify the Structured Text program in `Programs → main`.

### Step 2: Start OpenPLC Runtime

1. Install and launch OpenPLC Runtime v4.
2. Keep the Runtime terminal running.
3. Confirm the management server is accessible at:

```text
https://127.0.0.1:8443
```

### Step 3: Connect the Editor

In OpenPLC Editor, navigate to:

`Device → Configuration`

Configure:

```text
Device: OpenPLC Runtime v4
IP Address: 127.0.0.1
```

Click **Connect** and authenticate if prompted.

### Step 4: Verify Modbus TCP

Open the included `Reactor_Modbus_Server` configuration.

Required settings:

| Setting | Value |
|---|---|
| Enabled | ON |
| Transport | Modbus TCP |
| Port | 502 |
| Slave ID | 1 |
| Buffer Mapping | Project defaults |

Keep communication local to the simulation environment wherever possible. Do not expose an unauthenticated Modbus server directly to untrusted networks.

### Step 5: Deploy the controller

In OpenPLC Editor:

1. Save the project.
2. Select **Build and upload**.
3. If prompted, select **Stop PLC and Continue**.
4. Confirm compilation and deployment succeeded.
5. Verify that the PLC status is `RUNNING`.

## 6. Modbus Memory Mapping

The current system uses the following memory addresses:

| Variable | PLC Location | Modbus Address | Data Type |
|---|---|---|---|
| `Temperature_x10` | `%MW0` | Holding Register 1024 | INT |
| `Cooling_ON` | `%QX0.0` | Coil 0 | BOOL |
| `High_Temp_Alarm` | `%QX0.1` | Coil 1 | BOOL |

Python transmits temperature using a scaled integer representation.

For example:

```text
Actual Temperature: 75.5°C
Transmitted Value: 755
PLC Conversion: 755 / 10 = 75.5°C
```

This approach uses a single 16-bit Modbus register and preserves one decimal place.

The listed Modbus addresses depend on the included OpenPLC server buffer mapping.

## 7. Running the Simulation

First, launch OpenPLC Runtime and verify the PLC is running with Modbus TCP enabled.

Optionally, verify port connectivity using PowerShell:

```powershell
Test-NetConnection 127.0.0.1 -Port 502
```

The expected result is:

```text
TcpTestSucceeded : True
```

From the repository's root directory, run the communication test:

```powershell
python .\python\test_modbus.py
```

Expected output:

```text
Temperature sent: 85.0°C
Cooling ON: True
High Temp Alarm: False
```

Then run the complete simulation:

```powershell
python .\python\main.py
```

The simulation runs for 60 steps and should demonstrate the reactor heating until cooling activates at 80°C, then cooling toward 70°C before the controller turns cooling off.

OpenPLC Runtime must remain running during the simulation. OpenPLC Editor can be closed after successful deployment.

## 8. Baseline CSV Logging

The simulation records its measurements in:

```text
results/baseline.csv
```

The dataset contains:

| Column | Description |
|---|---|
| Time | Elapsed simulation time |
| Actual_Temperature | Temperature before the physics update |
| Reported_Temperature | Measurement transmitted to OpenPLC |
| Cooling_ON | Cooling command returned by the PLC |
| High_Temp_Alarm | Alarm state returned by the PLC |
| Next_Temperature | Temperature following the physics update |

During normal operation, actual and reported temperatures should match to the resolution of the transmitted measurement.

These measurements will serve as a baseline for future FDI experiments.

The current implementation overwrites the baseline CSV when the simulation is rerun, so preserve any datasets needed for analysis.

## 9. Current Project Status

**Completed:**

- Python thermal simulation
- OpenPLC Structured Text hysteresis controller
- High-temperature alarm
- Modbus TCP communication
- Python/OpenPLC closed-loop integration
- Baseline CSV logging

**Planned Development:**

- Controlled false data injection experiments
- Detection of abnormal or inconsistent sensor readings
- Mitigation and recovery mechanisms
- HMI/SCADA visualization
- Additional sensors and simulated physical components
- Enhanced thermal modeling using reactor power, fission rate, and thermal properties

## 10. Research Objective

The project investigates how falsified sensor measurements can influence the behavior of a cyber-physical control system.

Future experiments will distinguish between:

- **Actual temperature:** The true state calculated by the Python simulation.
- **Reported temperature:** The measurement received by OpenPLC.
- **Controller response:** The cooling command issued by the PLC.

By comparing normal and compromised operation, the project aims to evaluate the impact of false data injection and explore potential methods of detection, mitigation, and recovery.

All experiments are intended for an isolated, simulated educational environment.