# 🧠 BMad 專案模板（文件版）

## 專案名稱

台幣硬幣影像辨識與金額統計系統（Coin Vision Project）

---

## 一、專案背景（Problem Context）

在實際生活與產業場景中，對於散落硬幣的自動化清點與金額統計具有高度實用價值，例如：

- 零錢盤點
- 自助結帳系統
- 金融教育與影像辨識教學

本專案目標是：

> **給定一張包含多枚新台幣硬幣的影像，自動辨識硬幣面額、正反面，並計算總金額與數量。**

---

## 二、專案目標（Project Objectives）

### 核心目標

- 辨識圖中所有硬幣
- 判斷每一枚硬幣的：
  - 面額（1 / 5 / 10 元）
  - 正面 / 反面
- 輸出：
  - 總金額
  - 正面硬幣數量
  - 反面硬幣數量

### 成功判準（Success Criteria）

- 硬幣偵測召回率 ≥ 95%
- 正反面分類準確率 ≥ 70%（使用既有模型）
- 金額計算錯誤率 ≤ 5%

---

## 三、已知資源與限制（Constraints & Assets）

### 已有資源

- 已訓練模型：`coin_classifier.pth`
  - 功能：硬幣正反面辨識
  - 準確率：約 70%

### 技術限制

- 僅使用單張靜態影像（JPG / PNG）
- 硬幣可能互相距離不一、角度不同
- 光線與背景可能存在變化

---

## 四、整體解決策略（High-Level Strategy）

本專案採用 **「傳統影像處理 + AI 模型」的混合式架構**：

- 傳統 CV：
  - 提供穩定、可解釋的幾何與位置資訊
- AI 模型：
  - 負責處理人眼難以用規則判斷的外觀差異（正反面）

---

## 五、辨識流程設計（Pipeline Design）

### Step 1：影像前處理（Preprocessing）

**目的：** 提升硬幣輪廓可辨識度

可能方法：

- 灰階轉換
- Gaussian Blur
- Adaptive Threshold / Canny Edge

---

### Step 2：硬幣偵測（Coin Detection）

**目的：** 找出所有硬幣位置（ROI）

建議方法：

- 霍夫圓變換（Hough Circle Transform）
- 輪廓分析（Contour + Circularity）

輸出：

- 每枚硬幣的 bounding box / center / radius

---

### Step 3：ROI 擷取（Region of Interest Extraction）

**目的：** 為每枚硬幣建立獨立分析單元

處理方式：

- 依據圓心與半徑裁切影像
- 尺寸標準化（Resize）

---

### Step 4：正反面分類（Front / Back Classification）

**目的：** 使用既有 AI 模型判斷硬幣朝向

方法：

- 載入 `coin_classifier.pth`
- 對 ROI 進行推論

輸出：

- label: front / back
- confidence score（可選）

---

### Step 5：面額判斷（Denomination Estimation）

**目的：** 判斷 1 / 5 / 10 元

建議策略（非深度學習）：

- 使用半徑（pixel size）相對比例
- 設定分群門檻（Clustering / Rule-based）

優點：

- 可解釋
- 不依賴額外訓練資料

---

### Step 6：結果彙整（Aggregation）

輸出計算：

- 總金額
- 正面硬幣數量
- 反面硬幣數量
- 各面額數量 (加分項)

---

## 六、BMad 方法論對應（BMad Alignment）

### Workflow Track：

**Execution / Engineering Track**

### BMad 在本專案的角色：

- 協助專案模組化
- 定義清楚輸入 / 輸出
- 管理實驗與里程碑

---

## 七、里程碑規劃（Milestones）

| Milestone | 說明               |
| --------- | ------------------ |
| M1        | 成功偵測所有硬幣   |
| M2        | 正反面分類可運作   |
| M3        | 面額判斷穩定       |
| M4        | 金額與數量輸出正確 |

---

## 八、評估與驗證（Evaluation Plan）

- 人工標註對照
- 單張 / 多張影像測試
- 邊界案例（重疊、暗光）測試

---

## 九、未來擴充方向（Future Work）

- 提升正反面模型準確率
- 加入硬幣重疊處理
- 擴充至其他幣別
- 即時攝影機辨識

---

## 十、專案總結（Summary）

本專案透過 **工程化影像處理流程 + AI 模型 + BMad 專案治理**，
建立一套具備可重用性、可說明性與實務價值的影像辨識系統。

> 這不只是一次作業，而是一個可複製的 Computer Vision 專案模板。
