import smbus
import time

# Διεύθυνση I2C του γυροσκοπίου (π.χ., MPU6050)
GYRO_ADDRESS = 0x68

# Καταχωρητές του MPU6050
PWR_MGMT_1 = 0x6B
GYRO_XOUT_H = 0x43
GYRO_YOUT_H = 0x45
GYRO_ZOUT_H = 0x47

# Αρχικοποίηση I2C
bus = smbus.SMBus(1)  # Χρησιμοποιείται I2C bus 1 (RPi ή άλλο σύστημα)

# Συνάρτηση αρχικοποίησης του γυροσκοπίου και δοκιμής
def initialize_gyro():
    try:
        # Ενεργοποίηση του γυροσκοπίου (βγαίνει από sleep mode)
        bus.write_byte_data(GYRO_ADDRESS, PWR_MGMT_1, 0)
        print("Gyroscope initialized.")
        time.sleep(1)  # Αναμονή για σταθεροποίηση
        
        # Έλεγχος σωστής λειτουργίας
        test_value = bus.read_byte_data(GYRO_ADDRESS, PWR_MGMT_1)
        if test_value != 0:
            raise Exception("Gyroscope test failed. Check connections.")
        print("Gyroscope test passed.")
        
        # Αρχικοποίηση στο έδαφος
        print("Initializing gyro as being on the ground...")
        ground_offsets = calibrate_gyro()
        print(f"Offsets initialized: {ground_offsets}")
        return ground_offsets
    except Exception as e:
        print(f"Error during gyro initialization: {e}")
        exit(1)

# Συνάρτηση για ανάγνωση τριών byte από το γυροσκόπιο
def read_word_3bytes(register):
    try:
        high = bus.read_byte_data(GYRO_ADDRESS, register)  # Υψηλό byte
        mid = bus.read_byte_data(GYRO_ADDRESS, register + 1)  # Μεσαίο byte
        low = bus.read_byte_data(GYRO_ADDRESS, register + 2)  # Χαμηλό byte
        value = (high << 16) | (mid << 8) | low  # Συνδυασμός των τριών byte
        # Επεξεργασία για 2's complement (υπογραφή για αρνητικές τιμές)
        if value >= 0x800000:
            value = -((0xFFFFFF - value) + 1)
        print(f"Read 3 bytes from register {hex(register)}: {value}")
        return value
    except Exception as e:
        print(f"Error reading 3 bytes from register {hex(register)}: {e}")
        return None

# Συνάρτηση για ανάγνωση δεδομένων από το γυροσκόπιο
def read_gyro_data():
    try:
        gyro_x = read_word_3bytes(GYRO_XOUT_H)
        gyro_y = read_word_3bytes(GYRO_YOUT_H)
        gyro_z = read_word_3bytes(GYRO_ZOUT_H)
        data = {"x": gyro_x, "y": gyro_y, "z": gyro_z}
        print(f"Gyro data read successfully: {data}")
        return data
    except Exception as e:
        print(f"Error reading gyro data: {e}")
        return None

# Συνάρτηση για βαθμονόμηση γυροσκοπίου στο έδαφος
def calibrate_gyro():
    samples = 100
    offsets = {"x": 0, "y": 0, "z": 0}
    try:
        print("Calibrating gyro... Please keep it still.")
        for i in range(samples):
            data = read_gyro_data()
            if data:
                offsets["x"] += data["x"]
                offsets["y"] += data["y"]
                offsets["z"] += data["z"]
            time.sleep(0.01)  # Μικρή καθυστέρηση για σταθεροποίηση

        offsets["x"] //= samples
        offsets["y"] //= samples
        offsets["z"] //= samples
        print(f"Calibration completed: {offsets}")
        return offsets
    except Exception as e:
        print(f"Error during gyro calibration: {e}")
        return None

# Κύριος βρόχος για ανάγνωση και αποστολή δεδομένων
def main_loop():
    offsets = initialize_gyro()
    try:
        while True:
            # Ανάγνωση δεδομένων
            gyro_data = read_gyro_data()
            if gyro_data:
                corrected_data = {
                    "x": gyro_data["x"] - offsets["x"],
                    "y": gyro_data["y"] - offsets["y"],
                    "z": gyro_data["z"] - offsets["z"]
                }
                print(f"Corrected Gyro Data - X: {corrected_data['x']}, Y: {corrected_data['y']}, Z: {corrected_data['z']}")
            else:
                print("Error: Could not read gyro data.")
            
            time.sleep(0.5)  # Καθυστέρηση μισού δευτερολέπτου
    except KeyboardInterrupt:
        print("Terminating program.")
    except Exception as e:
        print(f"Error in main loop: {e}")

# Εκτέλεση
if __name__ == "__main__":
    main_loop()
