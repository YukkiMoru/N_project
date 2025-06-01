import time
import board
import busio

# I2Cの初期化
i2c = busio.I2C(board.SCL1, board.SDA1, frequency=400000)

# マルチプレクサのチャンネル選択用関数
def pcaselect(channel):
    if channel > 7:
        return  # チャンネルが範囲外の場合は何もしない
    if not i2c.try_lock():
        print("Failed to acquire I2C lock for pcaselect")
        return
    try:
        i2c.writeto(0x70, bytes([1 << channel]))  # マルチプレクサのアドレスは0x70
    finally:
        i2c.unlock()

# マルチプレクサの各ポートで利用可能なI2Cアドレスを確認する関数
def scan_i2c_addresses():
    for channel in range(8):
        print(f"Scanning channel {channel}...")
        pcaselect(channel)
        if not i2c.try_lock():
            print(f"Failed to acquire I2C lock for scanning on channel {channel}")
            continue
        try:
            addresses = i2c.scan()
            if addresses:
                print(f"Channel {channel}: Found addresses {', '.join(hex(addr) for addr in addresses)}")
            else:
                print(f"Channel {channel}: No devices found")
        finally:
            i2c.unlock()

# 実行部分
if __name__ == "__main__":
    scan_i2c_addresses()
