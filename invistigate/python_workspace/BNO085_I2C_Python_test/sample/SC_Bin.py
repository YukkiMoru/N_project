# serial_console.py
import serial
import serial.tools.list_ports
import threading
import struct # 追加: バイナリデータ処理のため

# CRC16-CCITT (0x1021, 初期値0xFFFF)
def crc16_ccitt(data: bytes, poly=0x1021, init=0xFFFF) -> int:
    crc = init
    for b in data:
        crc ^= b << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ poly
            else:
                crc <<= 1
            crc &= 0xFFFF
    return crc

# 利用可能なCOMポートを表示して選択する
def select_com_port():
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("利用可能なCOMポートがありません。デバイスが接続されているか確認してください。")
        return None
    
    print("利用可能なCOMポート:")
    for i, port in enumerate(ports):
        print(f"{i+1}: {port.device} - {port.description}")
    
    selection = input("使用するポート番号を入力してください (1, 2, ...): ")
    try:
        index = int(selection) - 1
        if 0 <= index < len(ports):
            return ports[index].device
        else:
            print("無効な選択です。")
            return None
    except ValueError:
        print("数字を入力してください。")
        return None

# ポート選択
PORT = select_com_port()
if not PORT:
    print("有効なCOMポートが選択されていません。プログラムを終了します。")
    exit()

BAUD = 115200

ser = serial.Serial(PORT, BAUD, timeout=1)

HEADER = b'\xAA\x55'  # 2バイトの開始シンボル

def read_serial():
    expected_data_length = 2 + 14 * 4 + 2  # HEADER(2) + 14 floats(56) + CRC16(2) = 60バイト
    buffer = b''
    while True:
        buffer += ser.read(ser.in_waiting or 1)
        while True:
            header_pos = buffer.find(HEADER)
            if header_pos == -1:
                # HEADERが見つからなければバッファを短く保つ
                buffer = buffer[-1:]
                break
            if len(buffer) < header_pos + expected_data_length:
                # パケット全体が揃うまで待つ
                break
            packet = buffer[header_pos:header_pos+expected_data_length]
            buffer = buffer[header_pos+expected_data_length:]
            data = packet[2:-2]
            recv_crc_bytes = packet[-2:]
            recv_crc = struct.unpack('<H', recv_crc_bytes)[0]
            calc_crc = crc16_ccitt(data)
            if recv_crc != calc_crc:
                print(f"[ERROR] CRC mismatch! Received: {recv_crc:04X}, Calculated: {calc_crc:04X}")
                continue
            try:
                unpacked_data = struct.unpack("<14f", data)
                timestamp = unpacked_data[0]
                accel = unpacked_data[1:4]
                gyro = unpacked_data[4:7]
                mag = unpacked_data[7:10]
                quat = unpacked_data[10:14]
                print(f"{timestamp:.3f}", end=",")
                print(f"{accel[0]:.3f},{accel[1]:.3f},{accel[2]:.3f}", end=",")
                print(f"{gyro[0]:.3f},{gyro[1]:.3f},{gyro[2]:.3f}", end=",")
                print(f"{mag[0]:.3f},{mag[1]:.3f},{mag[2]:.3f},{quat[0]:.3f},{quat[1]:.3f},{quat[2]:.3f},{quat[3]:.3f}")
            except struct.error as e:
                print(f"[ERROR] Failed to unpack data: {e}")
            except Exception as e:
                print(f"[ERROR] Unexpected error processing data: {e}")

threading.Thread(target=read_serial, daemon=True).start()

print("Enter text to send. Type 'reboot' to send Ctrl+D. Ctrl+C to exit.")
try:
    while True:
        cmd = input("> ")
        if cmd.lower() == 'reboot':
            print("[INFO] Sending Ctrl+D to the device...")
            ser.write(b'\x04') # Send Ctrl+D character
        else:
            data_bytes = (cmd + "\r\n").encode()
            ser.write(data_bytes)
            ser.flush()
except KeyboardInterrupt:
    ser.close()
    print("\nSerial closed.")
