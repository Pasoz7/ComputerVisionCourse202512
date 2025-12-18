"""
MediaPipe 手部追蹤範例
最簡單的手部偵測與關鍵點繪製

使用方式:
    python hand_tracking.py

安裝套件:
    pip install mediapipe opencv-python
"""

import cv2
import mediapipe as mp


def main():
    # 初始化 MediaPipe Hands
    mp_hands = mp.solutions.hands
    mp_draw = mp.solutions.drawing_utils

    # 建立手部偵測器
    hands = mp_hands.Hands(
        static_image_mode=False,      # False = 影片模式 (更快)
        max_num_hands=2,              # 最多偵測 2 隻手
        min_detection_confidence=0.5, # 偵測信心閾值
        min_tracking_confidence=0.5   # 追蹤信心閾值
    )

    # 開啟攝影機
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    print("手部追蹤已啟動，按 'q' 退出")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # 水平翻轉 (鏡像)
        frame = cv2.flip(frame, 1)

        # BGR 轉 RGB (MediaPipe 需要 RGB)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # 執行手部偵測
        results = hands.process(rgb_frame)

        # 繪製結果
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # 繪製手部關鍵點與連接線
                mp_draw.draw_landmarks(
                    frame,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS
                )

                # 取得手腕座標 (示範如何取得特定關鍵點)
                h, w, _ = frame.shape
                wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]
                cx, cy = int(wrist.x * w), int(wrist.y * h)

                # 在手腕位置畫圓
                cv2.circle(frame, (cx, cy), 10, (0, 255, 0), -1)

        # 顯示畫面
        cv2.imshow("Hand Tracking", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # 釋放資源
    cap.release()
    cv2.destroyAllWindows()
    hands.close()


if __name__ == "__main__":
    main()
