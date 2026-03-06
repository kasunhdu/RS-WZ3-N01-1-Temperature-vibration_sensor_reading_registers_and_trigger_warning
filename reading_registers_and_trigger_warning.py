import time
import csv
from datetime import datetime
from pymodbus.client import ModbusSerialClient
import os

# ---------------------------------------------------------
# 1. Configuration Settings
# ---------------------------------------------------------
PORT = 'COM15'
BAUDRATE = 9600
SLAVE_ID = 1

START_ADDR = 0x0001      # Start from X-speed
REGISTER_COUNT = 6       # X,Y,Z Speed + X,Y,Z Displacement

POLL_INTERVAL = 4.0

CSV_FILENAME = "H:/Internsip E gravity/Vibration sensor/reading registors and trigger warnning/compressor_vibration_log.csv"

WARNING_THRESHOLD = 4.5
DANGER_THRESHOLD = 7.1

# ---------------------------------------------------------
# 2. Initialize CSV File 
# ---------------------------------------------------------
file_exists = os.path.isfile(CSV_FILENAME)

with open(CSV_FILENAME, mode='a', newline='') as file:
    writer = csv.writer(file)
    if not file_exists:
        writer.writerow([
            "Timestamp",
            "X_Speed_mm_s",
            "Y_Speed_mm_s",
            "Z_Speed_mm_s",
            "X_Displacement_um",
            "Y_Displacement_um",
            "Z_Displacement_um",
            "Status"
        ])

# ---------------------------------------------------------
# 3. Initialize Modbus Client
# ---------------------------------------------------------
client = ModbusSerialClient(
    port=PORT,
    baudrate=BAUDRATE,
    timeout=1,
    parity='N',
    stopbits=1,
    bytesize=8
)

# ---------------------------------------------------------
# 4. Main Monitoring Loop
# ---------------------------------------------------------
print(f"Connecting to sensor on {PORT} at {BAUDRATE} baud...")

if client.connect():
    print("Connected successfully!")
    print(f"Logging to {CSV_FILENAME}\n")

    try:
        while True:

            response = client.read_holding_registers(
                address=START_ADDR,
                count=REGISTER_COUNT,
                slave=SLAVE_ID
            )

            if not response.isError():

                # ---------------- Speed (mm/s)
                x_speed = response.registers[0] / 10.0
                y_speed = response.registers[1] / 10.0
                z_speed = response.registers[2] / 10.0

                # ---------------- Displacement (µm)
                x_disp = response.registers[3] / 10.0
                y_disp = response.registers[4] / 10.0
                z_disp = response.registers[5] / 10.0

                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                max_vibration = max(x_speed, y_speed, z_speed)

                if max_vibration >= DANGER_THRESHOLD:
                    status = "DANGER"
                    print(f"[{timestamp}] 🚨 DANGER! {max_vibration} mm/s")
                elif max_vibration >= WARNING_THRESHOLD:
                    status = "WARNING"
                    print(f"[{timestamp}] ⚠ WARNING! {max_vibration} mm/s")
                else:
                    status = "NORMAL"
                    print(f"[{timestamp}] OK | "
                          f"Speed(mm/s) X:{x_speed} Y:{y_speed} Z:{z_speed} | "
                          f"Disp(µm) X:{x_disp} Y:{y_disp} Z:{z_disp}")

                # Save to CSV
                with open(CSV_FILENAME, mode='a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow([
                        timestamp,
                        x_speed,
                        y_speed,
                        z_speed,
                        x_disp,
                        y_disp,
                        z_disp,
                        status
                    ])

            else:
                print("Modbus Read Error")

            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        print("Stopped by user")

    finally:
        client.close()
        print("Serial port closed")

else:
    print("Connection failed")