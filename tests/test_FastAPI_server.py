"""
走行体と通信するWebサーバ用のテスト.

@author Hara1274
"""
from fastapi.testclient import TestClient
from server.FastAPI_server import app
import os

# テスト用クライアントの生成
client = TestClient(app)


def test_check_health():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "I'm healthy!"}


def test_upload_no_file():
    response = client.post("/images", files={})
    # FastAPIの仕様でバリデーションエラーになる
    assert response.status_code == 422


def test_upload_real_image_file():
    # アップロードする実際の画像ファイルのパス
    image_path = "tests/testdata/img/test_data.JPEG"
    file_name = "black.JPEG"

    # ファイルをバイナリで読み込んでアップロード
    with open(image_path, "rb") as image_file:
        response = client.post(
            "/images",
            files={"file": (file_name, image_file, "image/JPEG")}
        )
    
    # 正常レスポンスを検証
    assert response.status_code == 200
    # 成功メッセージが返っていることを検証
    json_data = response.json()
    assert json_data["message"] == "File uploaded successfully"

    # 実際にファイルが保存されたかを確認
    assert "filePath" in json_data
    saved_path = json_data["filePath"]
    assert os.path.exists(saved_path)
    # テスト終了後、保存ファイルを削除
    os.remove(saved_path)
