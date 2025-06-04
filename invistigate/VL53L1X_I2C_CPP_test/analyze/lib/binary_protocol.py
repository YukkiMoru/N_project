import struct

class VL53L1XBinaryProtocol:
    """
    VL53L1X用バイナリ通信プロトコル変換クラス
    - 8バイト: <uint32_t時刻, uint32_t距離>
    """

    @staticmethod
    def decode(data: bytes):
        """
        8バイトのバイナリデータを (t, d) タプルに変換
        """
        if len(data) != 8:
            raise ValueError("データ長が8バイトではありません")
        t, d = struct.unpack('<II', data)
        return t, d

    @staticmethod
    def encode(t: int, d: int) -> bytes:
        """
        (t, d) タプルを8バイトのバイナリに変換
        """
        return struct.pack('<II', t, d)
