"""
走行体と通信するWebサーバ用のテスト.

@author Hara1274
"""
from fastapi.testclient import TestClient
from src.server.fastapi_server import app
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
    image_path = "tests/test_data/img/test_data.JPEG"
    file_name = "black.JPEG"

    # ファイルをバイナリで読み込んでアップロード
    with open(image_path, "rb") as image_file:
        response = client.post(
            "/images",
            files={"file": (file_name, image_file, "image/JPEG")}
        )

    # 正常レスポンスを検証（ローカル保存成功、競技システム送信は失敗の可能性）
    json_data = response.json()

    if response.status_code == 200:
        # 両方成功の場合
        assert json_data["message"] == (
            "File uploaded successfully to both local and official system")
    elif response.status_code == 207:
        # ローカル保存のみ成功の場合
        assert json_data["message"] == (
            "File uploaded to local but failed to upload to official system")
    else:
        # 予期しないステータスコード
        assert False, f"Unexpected status code: {response.status_code}"

    # 実際にファイルが保存されたかを確認
    assert "filePath" in json_data
    saved_path = json_data["filePath"]
    assert os.path.exists(saved_path)
    # テスト終了後、保存ファイルを削除（エラーは無視）
    try:
        os.remove(saved_path)
    except (PermissionError, FileNotFoundError):
        pass
