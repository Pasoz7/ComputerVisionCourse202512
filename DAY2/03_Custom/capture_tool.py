"""
硬幣資料蒐集工具 - WebCam 擷取 GUI
使用攝影機拍攝硬幣圖片，自動儲存到對應類別資料夾

操作說明:
1. 選擇要儲存的類別 (正面/反面)
2. 將硬幣對準畫面
3. 按「擷取」按鈕或按空白鍵拍照
4. 圖片會自動儲存到對應資料夾
"""

import tkinter as tk
from tkinter import ttk, messagebox
import cv2
from PIL import Image, ImageTk
import os
from datetime import datetime
import threading

# ============== 取得腳本所在目錄 ==============
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ============== 設定區 ==============
DATASET_DIR = os.path.join(SCRIPT_DIR, "dataset")
HEADS_DIR = os.path.join(DATASET_DIR, "heads")
TAILS_DIR = os.path.join(DATASET_DIR, "tails")

# 攝影機設定
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
PREVIEW_WIDTH = 640
PREVIEW_HEIGHT = 480


class CaptureToolGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("硬幣資料蒐集工具")
        self.root.geometry("900x600")
        self.root.resizable(False, False)

        # 攝影機相關
        self.cap = None
        self.is_running = False
        self.current_frame = None

        # 計數器
        self.heads_count = 0
        self.tails_count = 0

        # 確保資料夾存在
        self._setup_directories()

        # 建立 UI
        self._setup_ui()

        # 更新計數
        self._update_counts()

        # 綁定鍵盤事件
        self.root.bind('<space>', self._on_space_press)
        self.root.bind('<Escape>', lambda e: self._on_closing())

        # 視窗關閉事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _setup_directories(self):
        """建立資料夾結構"""
        os.makedirs(HEADS_DIR, exist_ok=True)
        os.makedirs(TAILS_DIR, exist_ok=True)

    def _setup_ui(self):
        """建立使用者介面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ========== 左側：攝影機畫面 ==========
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 攝影機標題
        ttk.Label(left_frame, text="攝影機畫面", font=("Arial", 12, "bold")).pack(pady=5)

        # 攝影機畫面
        self.canvas = tk.Canvas(left_frame, width=PREVIEW_WIDTH, height=PREVIEW_HEIGHT, bg="black")
        self.canvas.pack(padx=5, pady=5)

        # 攝影機控制按鈕
        cam_btn_frame = ttk.Frame(left_frame)
        cam_btn_frame.pack(pady=5)

        self.btn_start = ttk.Button(cam_btn_frame, text="開啟攝影機", command=self._start_camera)
        self.btn_start.pack(side=tk.LEFT, padx=5)

        self.btn_stop = ttk.Button(cam_btn_frame, text="關閉攝影機", command=self._stop_camera, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT, padx=5)

        # ========== 右側：控制面板 ==========
        right_frame = ttk.Frame(main_frame, padding="10")
        right_frame.pack(side=tk.RIGHT, fill=tk.Y)

        # 類別選擇
        ttk.Label(right_frame, text="選擇類別", font=("Arial", 12, "bold")).pack(pady=(0, 10))

        self.selected_class = tk.StringVar(value="heads")

        # 正面選項
        self.radio_heads = ttk.Radiobutton(
            right_frame,
            text="正面 (Heads)",
            variable=self.selected_class,
            value="heads",
            command=self._on_class_change
        )
        self.radio_heads.pack(anchor=tk.W, pady=5)

        # 反面選項
        self.radio_tails = ttk.Radiobutton(
            right_frame,
            text="反面 (Tails)",
            variable=self.selected_class,
            value="tails",
            command=self._on_class_change
        )
        self.radio_tails.pack(anchor=tk.W, pady=5)

        # 分隔線
        ttk.Separator(right_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)

        # 目前選擇顯示
        self.lbl_current = ttk.Label(
            right_frame,
            text="目前: 正面",
            font=("Arial", 14, "bold"),
            foreground="green"
        )
        self.lbl_current.pack(pady=10)

        # 擷取按鈕
        self.btn_capture = ttk.Button(
            right_frame,
            text="擷取照片\n(空白鍵)",
            command=self._capture_image,
            state=tk.DISABLED
        )
        self.btn_capture.pack(pady=10, ipadx=20, ipady=10)

        # 分隔線
        ttk.Separator(right_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)

        # 統計資訊
        ttk.Label(right_frame, text="已蒐集數量", font=("Arial", 12, "bold")).pack(pady=(0, 10))

        stats_frame = ttk.Frame(right_frame)
        stats_frame.pack()

        ttk.Label(stats_frame, text="正面:").grid(row=0, column=0, sticky=tk.E, padx=5)
        self.lbl_heads_count = ttk.Label(stats_frame, text="0", font=("Arial", 12))
        self.lbl_heads_count.grid(row=0, column=1, sticky=tk.W)

        ttk.Label(stats_frame, text="反面:").grid(row=1, column=0, sticky=tk.E, padx=5)
        self.lbl_tails_count = ttk.Label(stats_frame, text="0", font=("Arial", 12))
        self.lbl_tails_count.grid(row=1, column=1, sticky=tk.W)

        ttk.Label(stats_frame, text="總計:").grid(row=2, column=0, sticky=tk.E, padx=5)
        self.lbl_total_count = ttk.Label(stats_frame, text="0", font=("Arial", 12, "bold"))
        self.lbl_total_count.grid(row=2, column=1, sticky=tk.W)

        # 分隔線
        ttk.Separator(right_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)

        # 操作說明
        ttk.Label(right_frame, text="操作說明", font=("Arial", 10, "bold")).pack()
        instructions = [
            "1. 點擊「開啟攝影機」",
            "2. 選擇正面或反面",
            "3. 對準硬幣後按空白鍵",
            "   或點擊「擷取照片」",
            "4. 圖片自動儲存",
        ]
        for inst in instructions:
            ttk.Label(right_frame, text=inst, font=("Arial", 9)).pack(anchor=tk.W)

        # 狀態列
        self.status_var = tk.StringVar(value="請開啟攝影機")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _on_class_change(self):
        """當類別選擇改變時"""
        selected = self.selected_class.get()
        if selected == "heads":
            self.lbl_current.config(text="目前: 正面", foreground="green")
        else:
            self.lbl_current.config(text="目前: 反面", foreground="blue")

    def _update_counts(self):
        """更新計數顯示"""
        # 計算各資料夾的圖片數量
        self.heads_count = len([f for f in os.listdir(HEADS_DIR)
                                if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))])
        self.tails_count = len([f for f in os.listdir(TAILS_DIR)
                                if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))])

        self.lbl_heads_count.config(text=str(self.heads_count))
        self.lbl_tails_count.config(text=str(self.tails_count))
        self.lbl_total_count.config(text=str(self.heads_count + self.tails_count))

    def _start_camera(self):
        """開啟攝影機"""
        self.cap = cv2.VideoCapture(0)

        if not self.cap.isOpened():
            messagebox.showerror("錯誤", "無法開啟攝影機\n請確認攝影機已連接")
            return

        # 設定攝影機解析度
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)

        self.is_running = True
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self.btn_capture.config(state=tk.NORMAL)

        self.status_var.set("攝影機已開啟 - 選擇類別後按空白鍵擷取")

        # 開始更新畫面
        self._update_frame()

    def _stop_camera(self):
        """關閉攝影機"""
        self.is_running = False

        if self.cap is not None:
            self.cap.release()
            self.cap = None

        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)
        self.btn_capture.config(state=tk.DISABLED)

        # 清空畫面
        self.canvas.delete("all")
        self.canvas.create_text(
            PREVIEW_WIDTH // 2, PREVIEW_HEIGHT // 2,
            text="攝影機已關閉", fill="white", font=("Arial", 16)
        )

        self.status_var.set("攝影機已關閉")

    def _update_frame(self):
        """更新攝影機畫面"""
        if not self.is_running:
            return

        ret, frame = self.cap.read()

        if ret:
            # 儲存原始畫面用於擷取
            self.current_frame = frame.copy()

            # 水平翻轉 (鏡像)
            frame = cv2.flip(frame, 1)

            # 繪製類別提示
            selected = self.selected_class.get()
            color = (0, 255, 0) if selected == "heads" else (255, 0, 0)
            text = "HEADS" if selected == "heads" else "TAILS"

            cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

            # 繪製中心十字線
            h, w = frame.shape[:2]
            cv2.line(frame, (w//2 - 30, h//2), (w//2 + 30, h//2), (0, 255, 255), 1)
            cv2.line(frame, (w//2, h//2 - 30), (w//2, h//2 + 30), (0, 255, 255), 1)

            # 轉換為 Tkinter 格式
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)

            # 調整大小
            img = img.resize((PREVIEW_WIDTH, PREVIEW_HEIGHT), Image.Resampling.LANCZOS)

            self.photo = ImageTk.PhotoImage(image=img)
            self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)

        # 繼續更新
        if self.is_running:
            self.root.after(30, self._update_frame)

    def _capture_image(self):
        """擷取並儲存圖片"""
        if self.current_frame is None:
            messagebox.showwarning("警告", "沒有可用的畫面")
            return

        # 決定儲存路徑
        selected = self.selected_class.get()
        if selected == "heads":
            save_dir = HEADS_DIR
            class_name = "正面"
        else:
            save_dir = TAILS_DIR
            class_name = "反面"

        # 產生檔名 (時間戳記)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"coin_{timestamp}.jpg"
        filepath = os.path.join(save_dir, filename)

        # 儲存圖片
        cv2.imwrite(filepath, self.current_frame)

        # 更新計數
        self._update_counts()

        # 更新狀態
        self.status_var.set(f"已儲存: {class_name} - {filename}")

        # 視覺回饋 (閃爍效果)
        self._flash_feedback()

    def _flash_feedback(self):
        """擷取時的視覺回饋"""
        original_bg = self.canvas.cget("bg")
        self.canvas.config(bg="white")
        self.root.after(100, lambda: self.canvas.config(bg=original_bg))

    def _on_space_press(self, event):
        """空白鍵按下事件"""
        if self.is_running and self.btn_capture.cget("state") != tk.DISABLED:
            self._capture_image()

    def _on_closing(self):
        """視窗關閉事件"""
        self.is_running = False

        if self.cap is not None:
            self.cap.release()

        self.root.destroy()


def main():
    root = tk.Tk()
    app = CaptureToolGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
