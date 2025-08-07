"""競技システムインタフェース.

競技システムとの通信を行うクラス.
@author: nishijima515
"""
import requests
import os
from PIL import Image


class ResponseError(Exception):
    """レスポンスエラー用の例外."""

    def __init__(self, message: str):
        """コンストラクタ.

        Args:
            message (string): エラーメッセージ
        """
        super().__init__(message)


class OfficialInterface:
    """競技システムとの通信を行うクラス."""

    SERVER_IP = "192.168.100.1"    # 競技システムのIPアドレス
    TEAM_ID = 117                   # チームID

    @classmethod
    def upload_snap(cls, img_path: str) -> bool:
        """指定された画像をアップロードする.

        Args:
            img_path (str): アップロードする画像のパス

        Returns:
            success (bool): 通信が成功したか(成功:true/失敗:false)
        """
        url = f"http://{cls.SERVER_IP}/snap"
        # リクエストヘッダー
        headers = {
            "Content-Type": "image/jpeg"
        }
        # リクエストパラメータ
        params = {
            "id": cls.TEAM_ID
        }
        try:
            if not os.path.exists(img_path):
                print(f"画像ファイルが存在しません: {img_path}")
                return False
            # サイズが正しくない場合はリサイズする
            img = Image.open(img_path)
            width, height = img.size
            if not (width == 800 and height == 600):
                img = img.resize((800, 600))
                img.save(img_path, format="JPEG")
            # bytes型で読み込み
            with open(img_path, "rb") as image_file:
                image_data = image_file.read()
            # APIにリクエストを送信
            response = requests.post(url, headers=headers,
                                     data=image_data, params=params)
            # レスポンスのステータスコードが201の場合、通信成功
            print("Response status code:", response.status_code)
            print("Response text:", response.text)  # 追加
            if response.status_code != 201:
                raise ResponseError("Failed to send upload image.")
            success = True
            print("Image uploaded successfully.")
        except Exception as e:
            print(e)
            success = False
        return success


if __name__ == "__main__":
    print("test-start")
    print("Current working directory:", os.getcwd())
    OfficialInterface.upload_snap("tests/test_data/img/Fig/Fig1-1.JPEG")
    print("test-end")
