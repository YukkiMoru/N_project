import serial
import struct
import time

PORT = 'COM6'
BAUD = 115200
DATA_SIZE = 7  # 4バイト(ms) + 2バイト(dist) + 1バイト(timeout)

def main():
    # --- センサ設定コマンド送信 ---
    with serial.Serial(PORT, BAUD, timeout=1) as ser:
        ser.write(b"long,50000,50\n")
        # "OK"が返るまで最大5行読む
        for _ in range(5):
            response = ser.readline().decode().strip()
            if response == "OK":
                print("コマンドが正常に受け付けられました")
                break
        else:
            print("OK応答が得られませんでした")
            return
        # C++側のdelay(1000)+delay(3000)に合わせて4秒待つ
        ser.reset_input_buffer()  # 追加: バッファクリア
        time.sleep(4)

    # --- データ受信 ---
    with serial.Serial(PORT, BAUD, timeout=0.1) as ser:
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        print("シリアルポートからのデータ受信開始...（Ctrl+Cで終了）")
        try:
            buffer = b''
            while True:
                buffer += ser.read(ser.in_waiting or 1)
                while len(buffer) >= DATA_SIZE:
                    chunk = buffer[:DATA_SIZE]
                    buffer = buffer[DATA_SIZE:]
                    try:
                        ms, dist, timeout = struct.unpack('<IHB', chunk)
                        if timeout:
                            print(f"{ms}, TIMEOUT")
                        else:
                            print(f"{ms}, {dist}")
                    except struct.error:
                        # データずれ時はバッファを1バイトずらして再同期
                        buffer = buffer[1:]
        except KeyboardInterrupt:
            print("終了します")

if __name__ == "__main__":
    main()