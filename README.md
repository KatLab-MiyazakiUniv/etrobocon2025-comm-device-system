# etrobocon2025-comm-device-system

宮崎大学片山徹郎研究室チーム KatLab が作成する ET ロボコン 2025 アドバンストクラスの無線通信デバイス内システム用のプログラムです。

走行システムのプログラムは[こちら](https://github.com/KatLab-MiyazakiUniv/etrobocon2025)を参照してください。

## 実行方法

システムを実行する

```
make run
```

Pytest を実行する

```
make test
```

カバレッジレポートの表示

```
make coverage
```

ソースコードをフォーマットする

```
make format
```

ソースコードのスタイルをチェックする

```
make check_style
```

サーバを起動する(詳しくは Notion の開発メモに記載)

```
make server
```

画像ファイルは以下のコマンドで送信できる

```
curl -X POST -F "file=@"画像ファイルのパス"" http://サーバIPアドレス:8000/images
```

## 環境構築

### uv 環境構築手順

1. uv をインストール

   ```
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # pip
   pip install uv
   ```

   pip 環境があれば、pip からもインストールできる。

1. python 3.11.13 を uv 上にインストール

   ```
   uv python install 3.11.13
   ```

   `uv python list` でインストールした python のバージョンを確認できる。

1. 仮想環境を構築およびアクティベート

   ```
   uv venv　# 仮想環境を構築
   source .venv/bin/activate　# 仮想環境をアクティベート
   ```

   ターミナルのユーザの左に (etrobocon2025-comm-device-system) という表記が出ていれば、仮想環境のアクティベート成功

1. 依存関係の同期

   ```
   uv sync
   ```

   `uv pip list` でインストールしているパッケージの確認ができる。

## 作業時に行うこと

1. 仮想環境のアクティベート

   作業を始める際や、シェルを新しくした場合に仮想環境をアクティブ化する必要がある。

   以下のコマンドで、仮想環境をアクティベートする。

   ```
   source .venv/bin/activate
   ```

   VS Code などのエディタを使う場合、エディタさんが仮想環境を自動検出し、勝手にアクティブにしてくれる場合もある。

1. 依存関係の同期

   依存関係に変更があった場合、以下のコマンドで、パッケージの依存関係を最新に同期する。

   ```
   uv sync
   ```

## パッケージの追加・削除

### パッケージの追加

1. 以下のコマンドでパッケージを追加

   ```
   uv add [パッケージ名]
   ```

   これを行うと、`pyproject.toml` と `uv.lock` が変更されるはず。

1. パッケージを追加して問題なければ、変更された`pyproject.toml` と `uv.lock` をプッシュ

1. 他端末は `pyproject.toml` と `uv.lock` の変更をプルして、以下のコマンドでパッケージ環境を同期

   ```
   uv sync
   ```

### パッケージの削除

以下のコマンドでパッケージを削除できる

```
uv remove [パッケージ名]
```

もし、すでに github にプッシュ済みのパッケージを消去したのならば、`pyproject.toml` と `uv.lock` の変更をプッシュする。

他端末での環境の同期はパッケージの追加の時と同じ。

## Authors

KatLab メンバー, 宮崎大学片山徹郎研究室
