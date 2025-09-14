"""
走行体と通信するWebサーバプログラム.

@file fastapi_server.py
@author Hara1274
"""

import platform
import socket
import os
import uvicorn
import random

from fastapi import FastAPI, UploadFile, File, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from ..minifig_detector import MinifigDetector
from ..official_interface import OfficialInterface


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # すべてのオリジンを許可
    allow_methods=["*"],      # すべてのHTTPメソッドを許可
    allow_headers=["*"],      # すべてのヘッダーを許可
)

# MinifigDetectorのインスタンスを生成
minifig_detector = MinifigDetector()

# ミニフィグ検出結果の最良結果を保持
best_minifig_result = {
    "image_count": 0,
    "best_image_path": None,
    "best_confidence": 0.0,
    "best_direction": None
}

# 走行体から受け取った画像パスを保存するリスト
uploaded_image_paths = []


@app.get("/", response_class=JSONResponse)
def health_check() -> JSONResponse:
    """
    サーバー起動確認用のヘルスチェック関数.

    Returns:
        JSONResponse: レスポンスメッセージとステータスコード
    """
    return JSONResponse(
        content={"message": "I'm healthy!"},
        status_code=status.HTTP_200_OK
    )


@app.post("/images", response_class=JSONResponse)
def get_image(file: UploadFile = File(...)) -> JSONResponse:
    """
    走行体から、画像ファイルを取得し、競技システムにアップロードする関数.

    Args:
        file (UploadFile): アップロードされた画像ファイル、FastAPIのFileで受け取る

    Returns:
        JSONResponse: 結果メッセージとステータスコード
    """
    if not file.filename:
        return JSONResponse(
            content={"error": "No filename provided in uploaded file"},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # 画像のファイル名の取得
    file_name = file.filename

    # 画像保存用ディレクトリのパスを設定
    image_data_dir = os.path.join('image_data')

    # image_dataディレクトリが存在しない場合は作成
    os.makedirs(image_data_dir, exist_ok=True)

    # etrobocon2025-comm-device-system\image_dataに画像を保存
    file_path = os.path.join(image_data_dir, file_name)
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(file.file.read())
    except Exception as error:
        return JSONResponse(
            content={"error": f"Failed to save file: {str(error)}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    # 競技システムにアップロード
    upload_success = OfficialInterface.upload_snap(file_path)

    if upload_success:
        return JSONResponse(
            content={
                "message": "File uploaded successfully",
                "filePath": file_path
            },
            status_code=status.HTTP_200_OK
        )
    else:
        return JSONResponse(
            content={
                "error": (
                    "File saved locally but failed to upload to "
                    "official system"
                ),
                "filePath": file_path
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@app.post("/minifig/detect", response_class=JSONResponse)
def upload_minifig_image(file: UploadFile = File(...)) -> JSONResponse:
    """
    走行体から、受け取った４枚のミニフィグの画像から一番正面らしいものを競技システムにアップロードする関数.

    Args:
        file (UploadFile): アップロードされた画像ファイル、FastAPIのFileで受け取る

    Returns:
        JSONResponse: 結果メッセージとステータスコード
    """
    # 画像のファイル名の取得
    file_name = file.filename

    # 画像保存用ディレクトリのパスを設定
    image_data_dir = os.path.join("image_data")

    # image_dataディレクトリが存在しない場合は作成
    os.makedirs(image_data_dir, exist_ok=True)

    # etrobocon2025-comm-device-system\image_dataに画像を保存
    file_path = os.path.join(image_data_dir, file_name)
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(file.file.read())
    except Exception as error:
        return JSONResponse(
            content={"error": f"Failed to save file: {str(error)}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    # MinifigDetectorで推論を実行
    detection_result = minifig_detector.detect(file_path)

    # 走行体からミニフィグを送信された回数を増加
    best_minifig_result["image_count"] += 1

    # 走行体から受け取った画像パスをリストに追加
    uploaded_image_paths.append(file_path)

    # 最良画像を更新（front優先、次に信頼度優先）
    if detection_result["wasDetected"]:
        # 検出結果がfrontの場合
        if detection_result["direction"] == "front":
            # frontは既存がfront以外なら即更新、frontなら高信頼度で更新
            if (best_minifig_result["best_direction"] != "front" or
                    detection_result["confidence"] >
                    best_minifig_result["best_confidence"]):
                # それぞれの値を更新
                best_minifig_result["best_image_path"] = file_path
                best_minifig_result["best_confidence"] = (
                    detection_result["confidence"])
                best_minifig_result["best_direction"] = (
                    detection_result["direction"])

        # 既存の最良画像がfrontでなく、検出結果の信頼度が高い場合
        elif (best_minifig_result["best_direction"] != "front" and
              detection_result["confidence"] >
              best_minifig_result["best_confidence"]):
            # それぞれの値を更新
            best_minifig_result["best_image_path"] = file_path
            best_minifig_result["best_confidence"] = (
                detection_result["confidence"])
            best_minifig_result["best_direction"] = (
                detection_result["direction"])

    # 4枚未満の場合
    if best_minifig_result["image_count"] < 4:
        return JSONResponse(
            content={
                "message": (f"Image {best_minifig_result['image_count']} "
                            "processed successfully"),
                "detection_result": detection_result,
                "images_received": best_minifig_result["image_count"],
                "remaining": 4 -
                best_minifig_result["image_count"]},
            status_code=status.HTTP_200_OK)

    # 競技システムへアップロード対象画像を決定
    if best_minifig_result["best_image_path"]:
        upload_image_path = best_minifig_result["best_image_path"]
    else:
        # ４枚すべて検出失敗時はランダムで選択
        upload_image_path = random.choice(uploaded_image_paths)

    # 競技システムへのアップロード実行
    upload_success = OfficialInterface.upload_snap(upload_image_path)

    # リセット
    best_minifig_result["image_count"] = 0
    best_minifig_result["best_image_path"] = None
    best_minifig_result["best_confidence"] = 0.0
    best_minifig_result["best_direction"] = None
    uploaded_image_paths.clear()

    if upload_success:
        return JSONResponse(
            content={
                "message": "Image uploaded successfully",
                "imagePath": upload_image_path
            },
            status_code=status.HTTP_200_OK
        )
    else:
        return JSONResponse(
            content={"error": "Failed to upload image to official system"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ポート番号の設定
if __name__ == "__main__":
    ip = "127.0.0.1"

    if platform.system() == "Windows":
        host = platform.node()
    else:
        host = os.uname()[1]

    if host == "KatLabLaptop":
        # ソケットを作成し、GoogleのDNSサーバ("8.8.8.8:80")に接続し、IPアドレスを取得する。
        # 参考: https://qiita.com/suzu12/items/b5c3d16aae55effb67c0
        connect_interface = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        connect_interface.connect(("8.8.8.8", 80))
        ip = connect_interface.getsockname()[0]
        connect_interface.close()

    uvicorn.run(
        "src.server.fastapi_server:app",
        host=ip,
        port=8000,
        reload=True,
        # .venvディレクトリ下のコード変更で、無駄な再起動を防ぐ
        reload_excludes=[".venv/*"], 
    )
