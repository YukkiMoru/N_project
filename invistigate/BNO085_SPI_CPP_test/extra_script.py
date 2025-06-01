import shutil
import glob
import os

# RPI-RP2ドライブのパス（Windows例: E:\ など。環境に合わせて変更）
RPI_RP2_DRIVE = "D:\\"

def after_build(source, target, env):
    # .uf2ファイルのパスを取得
    uf2_files = glob.glob(os.path.join(env.subst("$BUILD_DIR"), "*.uf2"))
    if uf2_files and os.path.exists(RPI_RP2_DRIVE):
        print("Copying UF2 to RPI-RP2 drive...")
        shutil.copy(uf2_files[0], RPI_RP2_DRIVE)
    else:
        print("UF2ファイルまたはRPI-RP2ドライブが見つかりませんでした。")

Import("env") # type: ignore 
env.AddPostAction("buildprog", after_build) # type: ignore