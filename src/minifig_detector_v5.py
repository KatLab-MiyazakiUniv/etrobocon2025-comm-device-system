"""minifig向き検出クラス.

@file minifig_detector.py
@author Hara1274
"""
import cv2
import numpy as np
import onnxruntime as ort
import os
import json


class MinifigDetector:
    """minifigの向きを検出するクラス."""

    def __init__(self):
        """検出器を初期化."""
        self.session = None
        self.input_name = None
        self.labels = ["front", "back", "right", "left"]
        self.conf_threshold = 0.25
        self.nms_threshold = 0.45
        self.input_size = 640

        # YOLOv5 ONNXモデルのパス
        project_root = os.path.dirname(os.path.dirname(__file__))
        model_path = os.path.join(
            project_root, "models", "yolo_optimized.onnx")

        # モデルファイルが存在する場合のみonnxモデルの設定
        if os.path.exists(model_path):
            # 推論セッションを作成
            self.session = ort.InferenceSession(model_path)
            #  ONNXモデルの入力層の名前を取得
            self.input_name = self.session.get_inputs()[0].name

    def preprocess_image(self, img):
        """推論用に画像を前処理.

        Args:
            img: 入力画像

        Returns:
            tuple: (処理後画像, スケール比, パディング情報)
        """
        # シャープネス強化
        kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
        img = cv2.filter2D(img, -1, kernel)
        
        cv2.imwrite("output.png", img)

        # アスペクト比を保持するスケール計算
        shape = img.shape[:2]  # 元画像サイズ (H, W)
        # アスペクト比維持のスケール
        r = min(self.input_size / shape[0], self.input_size / shape[1])
        # スケール後サイズ (W, H)
        new_unpad = (int(round(shape[1] * r)), int(round(shape[0] * r)))
        img_resized = cv2.resize(
            img, new_unpad, interpolation=cv2.INTER_LINEAR)

        # 640x640にするための余白計算
        dw = self.input_size - new_unpad[0]  # 水平余白
        dh = self.input_size - new_unpad[1]  # 垂直余白
        top, bottom = dh // 2, dh - dh // 2  # 上下分割
        left, right = dw // 2, dw - dw // 2  # 左右分割

        # 灰色（114）でパディングして640x640に調整
        img_padded = cv2.copyMakeBorder(
            img_resized, top, bottom, left, right, cv2.BORDER_CONSTANT,
            value=(114, 114, 114))

        # YOLO入力形式に変換: HWC→CHW, [0,1]正規化, バッチ次元追加
        img_input = img_padded.transpose(2, 0, 1).astype(
            np.float32) / 255.0  # (3,640,640)
        img_input = np.expand_dims(img_input, axis=0)  # (1,3,640,640)

        return img_input, r, (left, top)

    def postprocess(self, pred, scale, pad):
        """推論結果を後処理.

        Args:
            pred: 推論出力 [1, N, 5+classes]
            scale: レターボックスのスケール比
            pad: パディング情報 (left, top)

        Returns:
            dict: 検出結果 {"wasDetected": bool, "direction": str,
                   "confidence": float}
        """
        if pred.size == 0:
            return {"wasDetected": False, "direction": "NONE",
                    "confidence": 0.0}

        # YOLOv5出力解析: [1,N,5+classes] -> [N,5+classes]（バッチ次元除去）
        data = pred[0]
        num_classes = data.shape[1] - 5
        num_boxes = data.shape[0]

        boxes = []
        confidences = []
        class_ids = []

        # 各検出候補を処理
        for i in range(num_boxes):
            # オブジェクト信頼度を取得
            obj_conf = data[i, 4]
            if obj_conf < self.conf_threshold:
                continue

            max_score = -1.0
            best_class = -1

            # クラススコアの最大値とクラスIDを取得
            for j in range(num_classes):
                score = data[i, 5 + j]
                if score > max_score:
                    max_score = score
                    best_class = j

            # 信頼度閾値による候補フィルタリング
            if obj_conf * max_score < self.conf_threshold:
                continue

            # バウンディングボックス座標抽出（YOLO形式：中心座標＋幅高さ）
            cx = data[i, 0]
            cy = data[i, 1]
            w = data[i, 2]
            h = data[i, 3]

            # レターボックス座標系から元画像座標系に逆変換
            center_x = int((cx - pad[0]) / scale)  # パディング補正＋スケール逆変換
            center_y = int((cy - pad[1]) / scale)
            width = int(w / scale)
            height = int(h / scale)

            # 中心座標形式から左上座標形式（OpenCV形式）に変換
            left = center_x - width // 2
            top = center_y - height // 2

            # NMS用データに追加
            boxes.append([left, top, width, height])  # [x,y,w,h]形式
            confidences.append(obj_conf * max_score)  # 最高クラススコア
            class_ids.append(best_class)  # 最高スコアのクラスID

        # 信頼度閾値を満たす検出がない場合
        if not boxes:
            return {"wasDetected": False,
                    "direction": "NONE", "confidence": 0.0}

        # Non-Maximum Suppression で重複検出を除去
        indices = cv2.dnn.NMSBoxes(
            boxes, confidences, self.conf_threshold, self.nms_threshold)

        # NMS後に有効な検出が残っている場合
        if len(indices) > 0:
            best_idx = indices.flatten()[0]  # 最も信頼度の高い検出を選択
            best_class_id = class_ids[best_idx]  # 対応するクラスID
            best_confidence = confidences[best_idx]  # 対応する信頼度
            direction = self.labels[best_class_id]  # ミニフィグの向き

            return {
                "wasDetected": True,
                "direction": direction,  # "front", "back", "right", "left"
                "confidence": float(best_confidence)  # 0.0-1.0の信頼度
            }

        return {"wasDetected": False, "direction": "NONE", "confidence": 0.0}

    def detect(self, image_path: str) -> dict:
        """minifigの向きを判定.

        Args:
            image_path (str): 画像ファイルのパス

        Returns:
            dict: 検出結果 {"wasDetected": bool, "direction": str,
                         "confidence": float}
        """
        # 共通エラーレスポンス
        error_result = {"wasDetected": False,
                        "direction": "NONE", "confidence": 0.0}

        # 入力ファイル存在チェック
        if not os.path.exists(image_path):
            print("入力ファイルが存在しません")
            return error_result
        # モデル読み込み状態チェック
        if self.session is None:
            print("モデル読み込みエラー")
            return error_result
        # 画像読み込み（BGR形式）
        img = cv2.imread(image_path)
        if img is None:  # 読み込み失敗（不正ファイル等）
            print("画像読み込みエラー")
            return error_result

        # 前処理：レターボックス＋正規化
        img_input, scale, pad = self.preprocess_image(img)

        # YOLOv5推論実行
        outputs = self.session.run(None, {self.input_name: img_input})
        pred = outputs[0]  # メイン出力 [1,N,5+classes]

        # 後処理：NMS＋結果構築
        result = self.postprocess(pred, scale, pad)

        return result
