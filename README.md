# 📊 公開資訊觀測站 開放資料瀏覽器

使用 **Gradio** 打造的 MOPS（公開資訊觀測站）開放資料瀏覽工具。輸入 CSV 網址即可下載資料，並進行關鍵字搜尋、欄位篩選、圖表分析與 CSV 匯出。

## ✨ 功能

- 🔗 可自訂資料網址（預設：`t187ap46_L_1.csv`），換成其他 MOPS 開放資料也能用
- 🧹 可選擇是否移除缺漏值（`dropna`）
- 📈 統計卡片：筆數、欄位數、數值欄位數、缺漏值
- 🔎 全欄位關鍵字搜尋、自選顯示欄位
- 📊 圖表分析：數值欄位畫分布直方圖、文字欄位畫 Top N 長條圖
- 🧮 欄位摘要（`describe`）
- ⬇️ 下載目前篩選結果（CSV，`utf-8-sig`，Excel 開啟不亂碼）

## 📁 專案結構

```
.
├── app.py             # Gradio 主程式
├── requirements.txt   # 相依套件
├── render.yaml        # (選用) Render Blueprint 設定
├── .gitignore
└── README.md
```

## 💻 本機執行

```bash
python -m venv .venv
source .venv/bin/activate      # Windows：.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

開啟瀏覽器前往 http://localhost:7860 。

## 🚀 部署到 Render

### 1. 上傳到 GitHub

```bash
git init
git add .
git commit -m "Initial commit: MOPS Gradio app"
git branch -M main
git remote add origin https://github.com/<你的帳號>/<repo 名稱>.git
git push -u origin main
```

### 2. 在 Render 建立 Web Service

1. 登入 [Render](https://render.com)，點 **New + → Web Service**。
2. 連結 GitHub 並選擇這個 repo。
3. 設定如下：

| 欄位 | 值 |
| --- | --- |
| Language / Runtime | `Python 3` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `python app.py` |
| Instance Type | `Free`（測試用） |

4. 在 **Environment** 新增變數：

| Key | Value | 說明 |
| --- | --- | --- |
| `PYTHON_VERSION` | `3.11.9` | 指定 Python 版本 |
| `DEFAULT_URL` | （選填）CSV 網址 | 覆蓋預設資料網址 |

5. 點 **Create Web Service**，等待建置完成後，即可使用 Render 提供的 `https://xxx.onrender.com` 網址。

> 也可以改用 **Blueprint**：Render 選 **New + → Blueprint**，選擇此 repo，會自動讀取 `render.yaml`。

## ⚠️ 注意事項

- **免費方案會休眠**：閒置一段時間後服務會關閉，下次開啟需等待約 30～60 秒冷啟動。
- **下載失敗**：程式會顯示錯誤原因。若在本機可下載、但 Render 上失敗，可能是來源網站限制了雲端主機的 IP，請改用其他部署環境或確認網址是否正確。
- **資料為 0 筆**：若勾選「移除缺漏值」後每列都有空值，會變成空資料，請取消勾選。
- **憑證驗證**：沿用原腳本的 `verify=False` 下載資料，僅用於公開資料；若來源憑證正常，建議在 `app.py` 改為 `verify=True`。
- 暫存的下載檔案存於伺服器暫存目錄，重新部署或重啟後會清空。

## 🛠️ 技術

Python · Gradio · pandas · Plotly · requests

## 📄 資料來源

[公開資訊觀測站 開放資料](https://mopsfin.twse.com.tw/)
