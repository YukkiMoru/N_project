# 初期設定
## trans.shの初期設定
1. WSL上でNTFSドライブをマウントします。
   ```bash
   sudo mount -t drvfs D: /mnt/d
   ```
2. スクリプトに実行権限を付与します。
   ```bash
   chmod +x trans.sh
   ```

# trans.shの概要
`trans.sh`は、WSL (Linux) 上からAdafruit QT Py RP2040の記憶領域 (DドライブまたはEドライブ) にデータを転送するためのスクリプトです。

# trans.shの使い方
1. ターミナルを開きます。
2. `cd`コマンドを使用して、`N_Project`ディレクトリに移動します。
   ```bash
   cd ~/N_project/invistigate/python_workspace
   ```
3. スクリプトを実行します。
   ```bash
   ./trans.sh
   ```



