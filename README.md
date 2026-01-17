# 產品真偽驗證系統

這是一個讓客戶驗證產品真偽的查詢系統，同時提供後台管理介面讓你新增、編輯、刪除產品資料。

## 系統特色

- **前台**：簡潔的查詢介面，客戶輸入產品編碼即可驗證真偽
- **後台**：完整的資料管理功能，支援單筆新增、批次上傳、編輯、刪除
- **擴充性**：使用 SQLite 資料庫，輕鬆支援數萬筆資料，未來可升級至 PostgreSQL

## 安裝步驟

### 1. 安裝 Python（如尚未安裝）

前往 https://www.python.org/downloads/ 下載並安裝 Python 3.8 以上版本

安裝時記得勾選「Add Python to PATH」

### 2. 安裝所需套件

打開終端機/命令提示字元，切換到專案資料夾：

```bash
cd product-verification-system
```

安裝套件：

```bash
pip install -r requirements.txt
```

### 3. 啟動伺服器

```bash
python app.py
```

看到以下訊息表示啟動成功：

```
資料庫初始化完成
伺服器啟動中...
前台查詢頁面: http://localhost:5000
後台管理頁面: http://localhost:5000/admin
```

### 4. 開始使用

- 前台查詢：打開瀏覽器，前往 http://localhost:5000
- 後台管理：打開瀏覽器，前往 http://localhost:5000/admin

## 使用說明

### 後台管理

1. **新增單筆產品**
   - 點擊「新增產品」按鈕
   - 填入產品編碼（如 T501603）、商品名稱、購買醫院、出貨日期
   - 點擊「儲存」

2. **批次上傳**
   - 點擊「批次上傳」按鈕
   - 下載範例 CSV 檔案，依格式填入資料
   - 上傳 CSV 檔案

   CSV 格式範例：
   ```csv
   product_code,product_name,hospital_name,purchase_date
   T501603,心臟超音波儀,台北動物醫院,2024-01-15
   T501604,血壓計,高雄動物醫院,2024-01-16
   ```

3. **編輯/刪除**
   - 在產品列表中點擊對應的按鈕

### 前台查詢

客戶只需輸入產品編碼，系統會顯示：
- 驗證成功：顯示產品名稱、購買醫院、出貨日期
- 驗證失敗：提示查無此編碼

## 部署到網路

### 方法一：使用 Railway（推薦新手）

1. 註冊 https://railway.app
2. 連結你的 GitHub，上傳專案
3. Railway 會自動部署，給你一個公開網址

### 方法二：使用 Render

1. 註冊 https://render.com
2. 建立新的 Web Service
3. 連結 GitHub 專案
4. 設定啟動指令：`python app.py`

### 方法三：使用 VPS（進階）

如果你有自己的伺服器：

1. 安裝 Python 和 pip
2. 使用 gunicorn 作為生產環境伺服器：
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```
3. 設定 nginx 反向代理
4. 設定 SSL 憑證（Let's Encrypt）

## 資料庫備份

資料存放在 `products.db` 檔案中，定期備份這個檔案即可。

```bash
# 備份
cp products.db products_backup_$(date +%Y%m%d).db
```

## API 文件

### 前台 API

- `GET /api/verify/{product_code}` - 驗證產品編碼

### 後台 API

- `GET /api/products` - 取得產品列表（支援分頁和搜尋）
- `POST /api/products` - 新增產品
- `PUT /api/products/{id}` - 更新產品
- `DELETE /api/products/{id}` - 刪除產品
- `POST /api/products/batch` - 批次新增
- `GET /api/stats` - 取得統計資料

## 未來擴充建議

1. **加入後台登入驗證**：防止未授權存取管理頁面
2. **支援多種產品類型**：加入分類欄位
3. **匯出功能**：匯出 Excel 報表
4. **查詢紀錄**：記錄客戶的查詢行為
5. **升級資料庫**：資料量大時可遷移至 PostgreSQL

## 遇到問題？

常見問題：

1. **啟動失敗：Port 5000 被佔用**
   修改 app.py 最後一行的 port 數字，例如改成 5001

2. **中文顯示亂碼**
   確保 CSV 檔案以 UTF-8 編碼儲存

3. **無法連線**
   確認防火牆允許該 port，雲端部署要設定正確的 host（0.0.0.0）
