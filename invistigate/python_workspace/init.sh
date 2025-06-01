#!/bin/bash

# ソースファイルのパス
SOURCE_FILE=$(cat ./init/trans_from)

# デスティネーションファイルのパス
DESTINATION_FILE=$(cat ./trans_to)

# ファイルの存在を確認
if [ ! -f "$SOURCE_FILE" ]; then
  echo "ソースファイルが存在しません: $SOURCE_FILE"
  exit 1
fi

if [ ! -f "$DESTINATION_FILE" ]; then
  echo "デスティネーションファイルが存在しません: $DESTINATION_FILE"
  exit 1
fi

# ファイルの内容をコピー
cp "$SOURCE_FILE" "$DESTINATION_FILE"

echo "ファイルをコピーしました: $SOURCE_FILE -> $DESTINATION_FILE"