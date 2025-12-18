"""
YOLOv11 硬幣檢測 GUI 應用程式
使用 CustomTkinter 建立現代化介面

作者: AI Course
日期: 2024
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import cv2
from PIL import Image, ImageTk
import threading
import os
import numpy as np

# 設定 CustomTkinter 外觀
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# 硬幣面額對應表
COIN_VALUES = {
    '1h': 1, '1t': 1,
    '5h': 5, '5t': 5,
    '10h': 10, '10t': 10,
    '50h': 50, '50t': 50,
    '0': 0,
    'test': 0,
}


class YOLOApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # 視窗設定
        self.title("YOLOv11 硬幣檢測系統")
        self.geometry("1500x900")
        self.minsize(1300, 800)

        # 變數
        self.model = None
        self.model_path = ctk.StringVar(value="尚未載入模型")
        self.conf_threshold = ctk.DoubleVar(value=0.25)
        self.is_running = False
        self.cap = None
        self.current_source = None

        # 建立 UI
        self.create_widgets()

    def create_widgets(self):
        """建立所有 UI 元件 - 三欄式布局"""

        # ===== 主容器 =====
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # ===== 左側：控制面板 =====
        self.control_frame = ctk.CTkFrame(main_container, width=250)
        self.control_frame.pack(side="left", fill="y", padx=(0, 10))
        self.control_frame.pack_propagate(False)

        self.create_control_panel()

        # ===== 中間：影像顯示區 =====
        self.display_frame = ctk.CTkFrame(main_container)
        self.display_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        self.image_label = ctk.CTkLabel(
            self.display_frame,
            text="請載入模型並選擇來源",
            font=ctk.CTkFont(size=16)
        )
        self.image_label.pack(expand=True, fill="both")

        # ===== 右側：統計 Dashboard =====
        self.dashboard_frame = ctk.CTkFrame(main_container, width=280)
        self.dashboard_frame.pack(side="right", fill="y")
        self.dashboard_frame.pack_propagate(False)

        self.create_dashboard()

    def create_control_panel(self):
        """建立左側控制面板"""

        # 標題
        ctk.CTkLabel(
            self.control_frame,
            text="YOLOv11 硬幣檢測",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(15, 10))

        # ----- 模型設定區 -----
        model_section = ctk.CTkFrame(self.control_frame)
        model_section.pack(fill="x", padx=8, pady=5)

        ctk.CTkLabel(
            model_section,
            text="模型設定",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(pady=(8, 3))

        self.select_model_btn = ctk.CTkButton(
            model_section,
            text="選擇模型檔案 (.pt)",
            command=self.select_model,
            height=32
        )
        self.select_model_btn.pack(fill="x", padx=8, pady=3)

        self.model_label = ctk.CTkLabel(
            model_section,
            textvariable=self.model_path,
            wraplength=200,
            font=ctk.CTkFont(size=10)
        )
        self.model_label.pack(pady=(2, 3))

        self.model_status = ctk.CTkLabel(
            model_section,
            text="● 模型未載入",
            text_color="red",
            font=ctk.CTkFont(size=11)
        )
        self.model_status.pack(pady=(0, 8))

        # ----- 信心閾值設定 -----
        conf_section = ctk.CTkFrame(self.control_frame)
        conf_section.pack(fill="x", padx=8, pady=5)

        conf_header = ctk.CTkFrame(conf_section, fg_color="transparent")
        conf_header.pack(fill="x", padx=8, pady=(8, 3))

        ctk.CTkLabel(
            conf_header,
            text="信心閾值",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left")

        self.conf_label = ctk.CTkLabel(
            conf_header,
            text=f"{self.conf_threshold.get():.2f}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#00BFFF"
        )
        self.conf_label.pack(side="right")

        self.conf_slider = ctk.CTkSlider(
            conf_section,
            from_=0.1,
            to=0.9,
            variable=self.conf_threshold,
            command=self.update_conf_label
        )
        self.conf_slider.pack(fill="x", padx=8, pady=(3, 8))

        # ----- 來源選擇區 -----
        source_section = ctk.CTkFrame(self.control_frame)
        source_section.pack(fill="x", padx=8, pady=5)

        ctk.CTkLabel(
            source_section,
            text="選擇來源",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(pady=(8, 5))

        self.image_btn = ctk.CTkButton(
            source_section,
            text="📷 選擇圖片",
            command=self.select_image,
            height=32,
            state="disabled"
        )
        self.image_btn.pack(fill="x", padx=8, pady=2)

        self.video_btn = ctk.CTkButton(
            source_section,
            text="🎬 選擇影片",
            command=self.select_video,
            height=32,
            state="disabled"
        )
        self.video_btn.pack(fill="x", padx=8, pady=2)

        self.webcam_btn = ctk.CTkButton(
            source_section,
            text="📹 開啟攝影機",
            command=self.toggle_webcam,
            height=32,
            state="disabled"
        )
        self.webcam_btn.pack(fill="x", padx=8, pady=2)

        self.stop_btn = ctk.CTkButton(
            source_section,
            text="⏹ 停止偵測",
            command=self.stop_detection,
            height=32,
            fg_color="#8B0000",
            hover_color="#B22222",
            state="disabled"
        )
        self.stop_btn.pack(fill="x", padx=8, pady=(10, 8))

        # ----- 操作說明 -----
        ctk.CTkLabel(
            self.control_frame,
            text="操作流程:\n1. 載入模型\n2. 選擇來源\n3. 查看結果",
            font=ctk.CTkFont(size=10),
            text_color="gray60",
            justify="left"
        ).pack(pady=(15, 5), padx=10, anchor="w")

    def create_dashboard(self):
        """建立右側統計 Dashboard"""

        # 標題
        ctk.CTkLabel(
            self.dashboard_frame,
            text="📊 統計 Dashboard",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(15, 10))

        # ===== 總金額顯示 (最上方，最醒目) =====
        total_section = ctk.CTkFrame(self.dashboard_frame, fg_color="#1a1a2e", corner_radius=10)
        total_section.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            total_section,
            text="總金額",
            font=ctk.CTkFont(size=12),
            text_color="gray70"
        ).pack(pady=(10, 0))

        self.total_label = ctk.CTkLabel(
            total_section,
            text="$0",
            font=ctk.CTkFont(size=42, weight="bold"),
            text_color="#00FF7F"
        )
        self.total_label.pack(pady=(0, 5))

        self.total_count_label = ctk.CTkLabel(
            total_section,
            text="共 0 枚硬幣",
            font=ctk.CTkFont(size=12),
            text_color="#00BFFF"
        )
        self.total_count_label.pack(pady=(0, 10))

        # ===== 硬幣統計表 =====
        stats_section = ctk.CTkFrame(self.dashboard_frame)
        stats_section.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            stats_section,
            text="硬幣明細",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(pady=(10, 5))

        # 定義硬幣類型和顏色
        self.coin_types = [
            ("50元", ["50h", "50t"], "#FF8C00", 50),
            ("10元", ["10h", "10t"], "#CD853F", 10),
            ("5元", ["5h", "5t"], "#228B22", 5),
            ("1元", ["1h", "1t"], "#4169E1", 1),
        ]

        self.coin_labels = {}

        # 每種硬幣的統計行
        for coin_name, coin_classes, color, value in self.coin_types:
            row_frame = ctk.CTkFrame(stats_section, fg_color="gray20", corner_radius=5)
            row_frame.pack(fill="x", padx=8, pady=2)

            # 左側：顏色標識 + 名稱
            left_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            left_frame.pack(side="left", padx=8, pady=6)

            ctk.CTkLabel(
                left_frame,
                text="●",
                text_color=color,
                font=ctk.CTkFont(size=14)
            ).pack(side="left")

            ctk.CTkLabel(
                left_frame,
                text=f" {coin_name}",
                font=ctk.CTkFont(size=12)
            ).pack(side="left")

            # 右側：數量 x 金額 = 小計
            right_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            right_frame.pack(side="right", padx=8, pady=6)

            count_label = ctk.CTkLabel(
                right_frame,
                text="0",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="gray50",
                width=30
            )
            count_label.pack(side="left")

            ctk.CTkLabel(
                right_frame,
                text=" × ",
                font=ctk.CTkFont(size=10),
                text_color="gray50"
            ).pack(side="left")

            ctk.CTkLabel(
                right_frame,
                text=f"${value}",
                font=ctk.CTkFont(size=10),
                text_color="gray50",
                width=30
            ).pack(side="left")

            ctk.CTkLabel(
                right_frame,
                text=" = ",
                font=ctk.CTkFont(size=10),
                text_color="gray50"
            ).pack(side="left")

            subtotal_label = ctk.CTkLabel(
                right_frame,
                text="$0",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="gray50",
                width=50
            )
            subtotal_label.pack(side="left")

            self.coin_labels[coin_name] = {
                "classes": coin_classes,
                "count": count_label,
                "subtotal": subtotal_label,
                "value": value,
                "row": row_frame
            }

        # ===== 狀態顯示 =====
        status_section = ctk.CTkFrame(self.dashboard_frame, fg_color="transparent")
        status_section.pack(fill="x", padx=10, pady=15)

        self.status_label = ctk.CTkLabel(
            status_section,
            text="● 等待偵測...",
            font=ctk.CTkFont(size=12),
            text_color="gray60"
        )
        self.status_label.pack()

        # ===== FPS 顯示 =====
        self.fps_label = ctk.CTkLabel(
            status_section,
            text="",
            font=ctk.CTkFont(size=10),
            text_color="gray50"
        )
        self.fps_label.pack(pady=(5, 0))

    def update_conf_label(self, value):
        """更新信心閾值標籤"""
        self.conf_label.configure(text=f"{value:.2f}")

    def select_model(self):
        """選擇並載入模型"""
        file_path = filedialog.askopenfilename(
            title="選擇 YOLO 模型檔案",
            filetypes=[("PyTorch 模型", "*.pt"), ("所有檔案", "*.*")]
        )

        if file_path:
            self.load_model(file_path)

    def load_model(self, model_path):
        """載入 YOLO 模型 (在獨立線程中執行)"""
        self.model_status.configure(text="● 載入中...", text_color="yellow")
        self.select_model_btn.configure(state="disabled")
        self._loading_model_path = model_path

        thread = threading.Thread(target=self._load_model_thread, daemon=True)
        thread.start()

    def _load_model_thread(self):
        """在獨立線程中載入模型"""
        try:
            from ultralytics import YOLO
            model_path = self._loading_model_path
            model = YOLO(model_path)
            self.after(0, lambda: self._on_model_loaded(model, model_path))
        except Exception as e:
            self.after(0, lambda: self._on_model_load_error(str(e)))

    def _on_model_loaded(self, model, model_path):
        """模型載入成功的回調"""
        self.model = model
        self.model_path.set(os.path.basename(model_path))
        self.model_status.configure(text="● 模型已載入", text_color="#00FF7F")
        self.select_model_btn.configure(state="normal")

        self.image_btn.configure(state="normal")
        self.video_btn.configure(state="normal")
        self.webcam_btn.configure(state="normal")

        messagebox.showinfo("成功", f"模型載入成功!\n{model_path}")

    def _on_model_load_error(self, error_msg):
        """模型載入失敗的回調"""
        self.model_status.configure(text="● 載入失敗", text_color="red")
        self.select_model_btn.configure(state="normal")
        messagebox.showerror("錯誤", f"模型載入失敗:\n{error_msg}")

    def select_image(self):
        """選擇並處理圖片"""
        file_path = filedialog.askopenfilename(
            title="選擇圖片",
            filetypes=[
                ("圖片檔案", "*.jpg *.jpeg *.png *.bmp *.tiff"),
                ("所有檔案", "*.*")
            ]
        )

        if file_path:
            self.stop_detection()
            self.process_image(file_path)

    def process_image(self, image_path):
        """處理單張圖片"""
        try:
            frame = cv2.imread(image_path)
            if frame is None:
                messagebox.showerror("錯誤", "無法讀取圖片")
                return

            self.status_label.configure(text="● 處理圖片中...", text_color="yellow")

            results = self.model.predict(
                frame,
                conf=self.conf_threshold.get(),
                verbose=False
            )

            annotated_frame, coins = self.process_results(results, frame)
            self.display_frame_on_gui(annotated_frame)
            self.update_detection_results(coins)

            self.status_label.configure(text="● 圖片處理完成", text_color="#00FF7F")

        except Exception as e:
            messagebox.showerror("錯誤", f"處理圖片時發生錯誤:\n{e}")

    def select_video(self):
        """選擇並處理影片"""
        file_path = filedialog.askopenfilename(
            title="選擇影片",
            filetypes=[
                ("影片檔案", "*.mp4 *.avi *.mov *.mkv"),
                ("所有檔案", "*.*")
            ]
        )

        if file_path:
            self.stop_detection()
            self.start_video(file_path)

    def start_video(self, video_path):
        """開始處理影片"""
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            messagebox.showerror("錯誤", "無法開啟影片")
            return

        self.is_running = True
        self.current_source = "video"
        self.stop_btn.configure(state="normal")

        thread = threading.Thread(target=self.video_loop, daemon=True)
        thread.start()

    def toggle_webcam(self):
        """切換攝影機"""
        if self.is_running and self.current_source == "webcam":
            self.stop_detection()
        else:
            self.stop_detection()
            self.start_webcam()

    def start_webcam(self):
        """開啟攝影機"""
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            messagebox.showerror("錯誤", "無法開啟攝影機")
            return

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        self.is_running = True
        self.current_source = "webcam"
        self.webcam_btn.configure(text="📹 關閉攝影機")
        self.stop_btn.configure(state="normal")

        thread = threading.Thread(target=self.video_loop, daemon=True)
        thread.start()

    def video_loop(self):
        """影片/攝影機處理迴圈"""
        import time
        frame_count = 0
        start_time = time.time()

        while self.is_running and self.cap is not None:
            ret, frame = self.cap.read()
            if not ret:
                if self.current_source == "video":
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                else:
                    break

            if self.current_source == "webcam":
                frame = cv2.flip(frame, 1)

            results = self.model.predict(
                frame,
                conf=self.conf_threshold.get(),
                verbose=False
            )

            annotated_frame, coins = self.process_results(results, frame)

            # 計算 FPS
            frame_count += 1
            elapsed = time.time() - start_time
            if elapsed > 0:
                fps = frame_count / elapsed
                fps_text = f"FPS: {fps:.1f}"
            else:
                fps_text = ""

            self.after(0, lambda f=annotated_frame, c=coins, ft=fps_text: self.update_gui(f, c, ft))

        self.after(0, self.on_video_stopped)

    def on_video_stopped(self):
        """影片停止時的處理"""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self.webcam_btn.configure(text="📹 開啟攝影機")
        self.stop_btn.configure(state="disabled")
        self.fps_label.configure(text="")

    def update_gui(self, frame, coins, fps_text=""):
        """更新 GUI"""
        if self.is_running:
            self.display_frame_on_gui(frame)
            self.update_detection_results(coins)
            if fps_text:
                self.fps_label.configure(text=fps_text)

    def process_results(self, results, frame):
        """處理偵測結果"""
        detected_coins = []
        annotated_frame = frame.copy()

        for result in results:
            boxes = result.boxes
            names = result.names

            for box in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                class_name = names[cls_id]

                detected_coins.append(class_name)

                # 根據硬幣類型選擇顏色 (BGR)
                if class_name.startswith('50'):
                    color = (0, 140, 255)       # 深橙色
                    text_color = (255, 255, 255)
                elif class_name.startswith('10'):
                    color = (47, 133, 205)      # 棕色
                    text_color = (255, 255, 255)
                elif class_name.startswith('5'):
                    color = (34, 139, 34)       # 深綠色
                    text_color = (255, 255, 255)
                elif class_name.startswith('1'):
                    color = (225, 105, 65)      # 藍色
                    text_color = (255, 255, 255)
                else:
                    color = (128, 0, 128)       # 紫色
                    text_color = (255, 255, 255)

                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 4)

                value = COIN_VALUES.get(class_name, 0)
                label = f"{class_name} {conf:.2f}"
                if value > 0:
                    label += f" (${value})"

                (label_w, label_h), _ = cv2.getTextSize(
                    label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2
                )
                cv2.rectangle(
                    annotated_frame,
                    (x1, y1 - label_h - 10),
                    (x1 + label_w + 10, y1),
                    color, -1
                )
                cv2.putText(
                    annotated_frame, label,
                    (x1 + 5, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, text_color, 2
                )

        # 顯示總金額
        if detected_coins:
            total = sum(COIN_VALUES.get(c, 0) for c in detected_coins)
            total_text = f"Total: ${total}"
            (tw, th), _ = cv2.getTextSize(total_text, cv2.FONT_HERSHEY_SIMPLEX, 1.5, 3)
            cv2.rectangle(annotated_frame, (5, 10), (tw + 20, th + 25), (0, 0, 139), -1)
            cv2.putText(
                annotated_frame, total_text,
                (10, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3
            )

        return annotated_frame, detected_coins

    def display_frame_on_gui(self, frame):
        """在 GUI 上顯示影像"""
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        display_width = self.display_frame.winfo_width() - 20
        display_height = self.display_frame.winfo_height() - 20

        if display_width > 0 and display_height > 0:
            h, w = frame_rgb.shape[:2]
            scale = min(display_width / w, display_height / h)
            new_w, new_h = int(w * scale), int(h * scale)
            frame_resized = cv2.resize(frame_rgb, (new_w, new_h))
        else:
            frame_resized = frame_rgb

        image = Image.fromarray(frame_resized)
        photo = ctk.CTkImage(
            light_image=image,
            dark_image=image,
            size=(frame_resized.shape[1], frame_resized.shape[0])
        )

        self.image_label.configure(image=photo, text="")
        self.image_label.image = photo

    def update_detection_results(self, coins):
        """更新偵測結果顯示 (Dashboard)"""
        coin_counts = {}
        for coin in coins:
            coin_counts[coin] = coin_counts.get(coin, 0) + 1

        total_coins = 0
        total_amount = 0

        for coin_name, info in self.coin_labels.items():
            count = 0
            for cls in info["classes"]:
                count += coin_counts.get(cls, 0)

            value = info["value"]
            subtotal = count * value

            info["count"].configure(text=str(count))
            info["subtotal"].configure(text=f"${subtotal}")

            # 高亮有偵測到的硬幣
            if count > 0:
                info["count"].configure(text_color="#00FF7F")
                info["subtotal"].configure(text_color="#00FF7F")
                info["row"].configure(fg_color="#2d4a3e")
            else:
                info["count"].configure(text_color="gray50")
                info["subtotal"].configure(text_color="gray50")
                info["row"].configure(fg_color="gray20")

            total_coins += count
            total_amount += subtotal

        # 更新總計
        self.total_count_label.configure(text=f"共 {total_coins} 枚硬幣")
        self.total_label.configure(text=f"${total_amount}")

        # 更新狀態
        if total_coins > 0:
            self.status_label.configure(
                text=f"● 偵測中 - 發現 {total_coins} 枚硬幣",
                text_color="#00FF7F"
            )
        else:
            self.status_label.configure(
                text="● 偵測中 - 未發現硬幣",
                text_color="yellow"
            )

    def stop_detection(self):
        """停止偵測"""
        self.is_running = False
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self.webcam_btn.configure(text="📹 開啟攝影機")
        self.stop_btn.configure(state="disabled")
        self.status_label.configure(text="● 等待偵測...", text_color="gray60")
        self.fps_label.configure(text="")

    def on_closing(self):
        """關閉視窗時的處理"""
        self.stop_detection()
        self.destroy()


def main():
    """主程式"""
    app = YOLOApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()


if __name__ == "__main__":
    main()
