"""
走行体と通信するWebサーバプログラム.

@file fastapi_server.py
@author Hara1274
"""

import platform
import socket
import os
import uvicorn

from fastapi import FastAPI, UploadFile, File, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from ..official_interface import OfficialInterface


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # すべてのオリジンを許可
    allow_methods=["*"],      # すべてのHTTPメソッドを許可
    allow_headers=["*"],      # すべてのヘッダーを許可
)


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
    走行体から、画像ファイルを取得するための関数.

    Args:
        file (UploadFile): アップロードされた画像ファイル、FastAPIのFileで受け取る

    Returns:
        JSONResponse: 結果メッセージとステータスコード
    """
    if not file.filename:
        return JSONResponse(
            content={"error": "No uploaded file"},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # 画像のファイル名の取得
    file_name = file.filename

    # etrobocon2025-comm-device-system>image_dataに画像を保存
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    image_data_dir = os.path.join(project_root, 'image_data')

    # image_dataディレクトリが存在しない場合は作成
    os.makedirs(image_data_dir, exist_ok=True)

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
                "message": (
                    "File uploaded successfully to both local and "
                    "official system"
                ),
                "filePath": file_path
            },
            status_code=status.HTTP_200_OK
        )
    else:
        return JSONResponse(
            content={
                "message": (
                    "File uploaded to local but failed to upload to "
                    "official system"
                ),
                "filePath": file_path
            },
            status_code=status.HTTP_207_MULTI_STATUS
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

    uvicorn.run("src.server.fastapi_server:app", host=ip, port=8000, reload=True)
