"""サンプルです.

pytest の参考用です.

@author: takahashitom
"""


class Sample:
    """サンプルクラス."""

    def __init__(self, name):
        """コンストラクタ."""
        self.name = name

    def say(self):
        """名前を呼ぶよ."""
        print("Hello " + self.name + ".")
