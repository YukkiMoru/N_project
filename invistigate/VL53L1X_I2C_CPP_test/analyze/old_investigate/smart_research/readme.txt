"""
このスクリプトは、VL53L1X距離センサとシリアル通信を行い、計測コマンドを送信します。
'q'キーを押すことでデータ取得を終了できます。

使い方:
    - シリアルポート(PORT)とボーレート(BAUD)を正しく設定してください。
    - 最初にセンサへ計測開始コマンドを送信します。
    - "OK"応答を受信後、距離データの受信・プロットを開始します。
    - ターミナルで'q'を押すとデータ取得を終了し、プロットを閉じます。

センサへのコマンド書式例:
    "medium,33000,10\n"
    # <mode>,<timing_budget_us>,<inter_measurement_ms>
    # 例: "medium,33000,10" の意味（デフォルト）
    #   - mode: "medium"（計測モード。例: "short", "medium", "long"）
    #   - timing_budget_us: 33000（1回の計測にかける時間[マイクロ秒]。精度と速度に影響）
    #   - inter_measurement_ms: 10（計測間隔[ミリ秒]）

他の設定例（解説付き）:
    # ser.write(b"short,20000,5\n")
    #   - "short"モード: 近距離向け。高速だが精度はやや低い。
    #   - timing_budget_us: 20000（20ms/回。高速・低精度）
    #   - inter_measurement_ms: 5（5msごとに計測。高サンプリングレート）

    # ser.write(b"medium,33000,33\n")
    #   - "medium"モード: バランス型。速度と精度の中間。
    #   - timing_budget_us: 33000（33ms/回）
    #   - inter_measurement_ms: 33（33msごとに計測。約30Hzサンプリング）

    # ser.write(b"long,50000,50\n")
    #   - "long"モード: 長距離向け。遅いが精度・レンジが高い。
    #   - timing_budget_us: 50000（50ms/回。高精度・低速）
    #   - inter_measurement_ms: 50（50msごとに計測。低サンプリングレート）

必要なライブラリ:
    - pyserial
注意:
    - センサが上記コマンドプロトコルに対応している必要があります。
    - timing_budget_usやinter_measurement_msは用途に応じて調整してください。
"""