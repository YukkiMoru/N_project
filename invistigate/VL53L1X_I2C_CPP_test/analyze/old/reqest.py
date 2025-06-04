import serial

ser = serial.Serial('COM6', 115200, timeout=1)
# 例: Mediumモード, 33000us, 33ms
ser.write(b"medium,33000,22\n")
print(ser.readline().decode().strip())  # "OK"が返る
ser.close()