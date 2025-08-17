# 🍽️ 餐廳搜尋助手 API

> AI 驅動的智能餐廳搜尋服務，支援多種位置格式和自然語言對話

## ✨ 特色功能

### 🤖 智能 AI 對話
- **Gemini AI 整合** - 理解自然語言查詢
- **多語言支援** - 中文、英文、日文、韓文等
- **智能追問檢測** - 自動識別需要更多資訊的情況
- **對話歷史管理** - 保持上下文連貫性

### 📍 彈性位置處理
```python
# 支援多種位置格式
location_formats = {
    "地址字串": "台北市信義區",
    "座標物件": {"latitude": 25.0330, "longitude": 121.5654},
    "座標字串": "25.0330,121.5654"
}
```

### 🔍 智能搜尋引擎
- **地理位置搜尋** - 基於座標和半徑的精確搜尋
- **模糊地址搜尋** - 支援不完整地址查詢
- **關鍵字搜尋** - 餐廳名稱、菜系類型搜尋
- **智能排序** - 按距離、評分自動排序

### 💬 會話狀態管理
- **用戶會話持久化** - 記住用戶偏好和搜尋歷史
- **自動過期清理** - 防止記憶體洩漏
- **回滾機制** - 錯誤恢復功能

## 🏗️ 系統架構

```
├── 🌐 API Layer          # FastAPI 路由和請求處理
├── 🧠 Service Layer      # 業務邏輯和 AI 服務
├── 💾 Repository Layer   # 數據存取和持久化
├── 🗂️ Model Layer        # 數據模型和驗證
└── 🛠️ Utils Layer        # 工具函數和輔助功能
```

### 核心組件

| 組件 | 描述 | 檔案 |
|------|------|------|
| **API Gateway** | RESTful API 端點 | `api/routes.py` |
| **AI Service** | Gemini AI 整合 | `services/ai_service.py` |
| **Location Handler** | 位置處理引擎 | `api/location_handler.py` |
| **Search Engine** | 餐廳搜尋引擎 | `services/restaurant_service.py` |
| **Session Manager** | 會話狀態管理 | `services/session_service.py` |

## 🚀 快速開始

### 環境需求
- Python 3.8+
- FastAPI 0.116.1+
- Google Gemini API Key

### 安裝步驟

1. **克隆專案**
   ```bash
   git clone <repository-url>
   cd restaurant-search-api
   ```

2. **安裝依賴**
   ```bash
   pip install -r requirements.txt
   ```

3. **環境配置**
   ```bash
   # 設定環境變數
   export GEMINI_API_KEY="your_gemini_api_key"
   export DEBUG="true"
   export LOG_LEVEL="INFO"
   ```

4. **啟動服務**
   ```bash
   python main.py
   ```

5. **API 文檔**
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

## 📖 API 使用範例

### 基本搜尋
```python
import requests

# 使用地址搜尋
response = requests.post("http://localhost:8000/search", json={
    "user_id": "user123",
    "user_input": "我想要找一家義大利餐廳",
    "location": "台北市信義區",
    "time": "2024-01-15 18:00"
})

# 使用座標搜尋
response = requests.post("http://localhost:8000/search", json={
    "user_id": "user123",
    "user_input": "附近有什麼好吃的日式料理？",
    "location": {"latitude": 25.0330, "longitude": 121.5654},
    "time": "2024-01-15 18:00"
})
```

### 回應格式
```json
{
    "type": "success",
    "message": "為您找到 3 家符合條件的餐廳",
    "recommendations": [
        {
            "id": "rest001",
            "name": "義式風情餐廳",
            "cuisine": "義大利菜",
            "distance_km": 1.2,
            "rating": 4.5,
            "price_level": 3,
            "tags": ["浪漫", "約會", "正宗"],
            "address": "台北市信義區信義路五段7號",
            "phone": "02-2345-6789"
        }
    ],
    "criteria": {
        "cuisine": "義大利菜",
        "location": "台北市信義區"
    },
    "metadata": {
        "search_time": "2024-01-15T18:00:00",
        "total_found": 3
    }
}
```

## 🛠️ 技術棧

### 後端框架
- **FastAPI** - 現代高效能 Web 框架
- **Pydantic** - 數據驗證和序列化
- **Uvicorn** - ASGI 伺服器

### AI 與機器學習
- **Google Gemini AI** - 自然語言處理
- **多語言 NLP** - 支援多語言問題檢測

### 地理計算
- **Haversine 公式** - 精確距離計算
- **邊界框計算** - 地理搜尋優化

### 開發工具
- **Type Hints** - 完整類型註解
- **Dataclasses** - 現代 Python 數據類別
- **依賴注入** - 可測試的架構設計

## 📁 專案結構

```
餐廳搜尋助手 API/
├── api/                    # API 層
│   ├── routes.py          # 主要路由
│   ├── routes_alternative.py  # 替代實現
│   └── location_handler.py    # 位置處理
├── config/                # 配置管理
│   ├── setting.py         # AI 和應用配置
│   └── constants.py       # 系統常數
├── core/                  # 核心功能
│   ├── config.py          # 配置實例
│   ├── dependencies.py    # 依賴注入
│   └── logging.py         # 日誌配置
├── models/                # 數據模型
│   ├── requests.py        # 請求模型
│   ├── responses.py       # 回應模型
│   ├── definitions.py     # 餐廳定義
│   └── user_session.py    # 會話模型
├── services/              # 業務邏輯
│   ├── ai_service.py      # AI 服務
│   ├── restaurant_service.py  # 餐廳服務
│   └── session_service.py     # 會話服務
├── repositories/          # 數據存取
│   ├── in_memory_repo.py  # 記憶體倉庫
│   └── session_repo_interface.py  # 倉庫介面
├── utils/                 # 工具函數
│   ├── geo.py            # 地理計算
│   ├── ai_response_utils.py   # AI 回應分析
│   └── validators.py     # 數據驗證
└── main.py               # 應用程式入口
```

## 🔧 進階配置

### 環境變數
```bash
# AI 配置
GEMINI_API_KEY=your_api_key
GEMINI_MODEL=gemini-2.0-flash-exp
GEMINI_MAX_TOKENS=1000
GEMINI_TEMPERATURE=0.7

# 應用配置
DEBUG=false
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000
```

### 自定義搜尋半徑
```python
# 在 location_handler.py 中調整
def get_search_radius_km(location_data: Dict[str, Any]) -> float:
    if location_data.get("type") == "coordinates":
        return 5.0   # 座標搜尋: 5 公里
    elif location_data.get("type") == "address":
        return 10.0  # 地址搜尋: 10 公里
    else:
        return 15.0  # 預設: 15 公里
```

## 🧪 測試

### 健康檢查
```bash
curl http://localhost:8000/health
```

### 清除用戶會話
```bash
curl -X DELETE http://localhost:8000/sessions/user123
```

## 📊 效能特色

- ⚡ **異步處理** - 非阻塞 I/O 操作
- 🔄 **會話管理** - 智能會話過期清理
- 📏 **精確計算** - 毫秒級地理距離計算
- 🧠 **智能快取** - 減少重複 AI 請求

## 🤝 貢獻指南

1. Fork 專案
2. 創建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交變更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟 Pull Request

## 📄 許可證

此專案使用 MIT 許可證 - 詳見 [LICENSE](LICENSE) 文件

## 👥 作者

- **開發者** - 餐廳搜尋助手 API 團隊

## 🙏 致謝

- Google Gemini AI 團隊
- FastAPI 社群
- Python 開源社群

---

<p align="center">
  <strong>🍽️ 讓 AI 幫您找到最完美的用餐體驗！</strong>
</p>