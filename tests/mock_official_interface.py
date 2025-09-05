"""テスト用の競技システムモック.

@author: Hara1274
"""
import os


class MockOfficialInterface:
    """テスト用の競技システムモック."""

    @classmethod
    def upload_snap(cls, img_path: str, maxAttempts: int = 3) -> bool:
        """テスト用のアップロード関数（常に成功を返す）.

        Args:
            img_path (str): アップロードする画像のパス
            maxAttempts (int): 最大試行回数

        Returns:
            success (bool): 常にTrue
        """
        if not os.path.exists(img_path):
            print(f"画像ファイルが存在しません: {img_path}")
            return False

        print(f"Mock: Image uploaded successfully from {img_path}")
        return True
