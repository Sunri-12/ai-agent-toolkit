# ai-engineering-toolkit
模組化 AI Agent 開發框架

# 🏎️ Enterprise AI Starter Kit (F1 Modular Architecture)

![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)
![Gemini](https://img.shields.io/badge/LLM-Google%20Gemini%20%7C%20OpenAI-orange.svg)
![RAG](https://img.shields.io/badge/RAG-Hybrid%20(BM25%20%2B%20Vector)-green.svg)
![License](https://img.shields.io/badge/Architecture-Production--Ready%20Prototype-purple.svg)

一套專為企業級 AI 應用快速原型開發（Rapid Prototyping）與高壓實戰場景所設計的模組化軍火庫。

本專案採用「F1 賽車模組化組裝」理念，將 LLM 底層呼叫、異質文件解析、混合式檢索（Hybrid RAG）、自主工具調用（ReAct Agent）以及前端展示介面完全解耦，實現 高穩定度、跨模型相容、強型別防幻覺 的工程標準。

---

## 🌟 核心架構亮點 (Key Features)

1. 🔄 雙渦輪無縫切換引擎 (`LLMEngine`)
   - 封裝 `google-genai` 與 `openai` SDK，只需修改 `.env` 一行設定即可在 Gemini、OpenAI、Azure 或地端 vLLM 模型間無痛切換，上層業務邏輯 零修改。
   - 內建 `Tenacity` 指數退避重試（Exponential Backoff）與 `AsyncIO + Semaphore` 併發限流閥，兼顧高吞吐量與 API Rate Limit 安全。
   - 全面整合 `Pydantic` 強型別結構化輸出（Structured Outputs），從根源杜絕 JSON 解析錯誤。

2. 📄 異質資料萬用進氣口 (`UniversalDataLoader`)
   - 支援單檔或整個資料夾批次遞迴讀取（`.pdf`, `.csv`, `.xlsx`, `.json`, `.md`, `.txt`）。
   - PDF 表格結構化保留：自動透過 `pdfplumber` 抽取 PDF 內嵌表格並轉換為 Markdown 語法，解決傳統純文字切塊導致表格數據錯位的痛點。
   - 自動注入檔案名稱、頁碼（Page）與資料列（Row）Metadata，為下游 RAG 提供精確的引用來源（Citation）。

3. ⚡ 氮氣加速混合檢索變速箱 (`SimpleHybridRAG`)
   - Sparse + Dense 雙引擎：結合 `BM25Okapi`（精準命中產品型號、料號、錯誤碼）與 `ChromaDB` 向量語意檢索。
   - RRF（Reciprocal Rank Fusion）演算法：以倒數排名融合異質檢索器的分數，不依賴特定廠牌的 Embedding API，本地端即可秒級建置索引。
   - 防幻覺強制溯源：強制輸出結構化 `RAGResponse`，包含回答內容、引用來源清單（Citations）與信心度評估（Confidence）。

4. 🤖 跨廠牌自癒式 ReAct Agent (`ToolAgent`)
   - 透過 Pydantic Schema 驅動 `Thought -> Action -> Observation` 推理迴圈，擺脫各家模型原生 Function Calling 格式不相容的限制。
   - 錯誤自我修復（Self-Correction）：自動攔截 Python 工具執行時的 Exception 並轉化為 Observation 回傳給模型，讓 Agent 能在下一步自主修正參數重試，確保系統不崩潰。

5. 🖥️ 秒級展示戰情室 (`ui_templates/`)
   - 提供 `Streamlit` 互動式知識庫對話介面與 `FastAPI` 標準 RESTful API 服務模板（自帶 Swagger 文檔）。

---

## 📂 專案目錄結構 (Directory Structure)

```text
Enterprise_f1_kit/
├── .env.example          # 環境變數範本 (API Keys 與模型切換設定)
├── CLAUDE.md             # AI 輔助開發工具 (Claude Code / Copilot) 專用架構導覽
├── README.md             # 專案架構說明與面談設計問答集
├── data/                 # 存放待處理之測試資料 (PDF, CSV, JSON, MD...)
├── core/                 # 核心功能模組
│   ├── llm_engine.py     # [引擎] 統一封裝 LLM 呼叫 (Sync / Async / Retry / Pydantic)
│   ├── data_loader.py    # [進氣] 萬用檔案解析、表格轉 Markdown 與滑動視窗切塊
│   ├── rag_pipeline.py   # [變速箱] BM25 + ChromaDB 向量 RRF 混合檢索與溯源問答
│   └── agent_tools.py    # [導航] 支援自癒機制的 ReAct Tool Calling Agent
└── ui_templates/         # 快速展示與服務外殼
    ├── app_streamlit.py  # [介面 A] 互動式 Web UI 戰情室
    └── app_fastapi.py    # [介面 B] 標準 RESTful API 伺服器
```

---

## 🚀 快速啟動與安裝 (Quick Start)

### 1. 建立環境與安裝依賴
```bash
python -m venv .venv
# Windows 啟動: .venv\Scripts\activate
# Mac/Linux 啟動: source .venv/bin/activate

pip install google-genai openai pydantic python-dotenv tenacity pandas pymupdf pdfplumber chromadb rank-bm25 streamlit fastapi uvicorn tabulate
```

### 2. 配置 `.env` 環境變數
複製 `.env.example` 為 `.env`，並填入現場使用的 API Key：
```env
# 可選 "gemini" 或 "openai" (OpenAI 相容介面亦適用 Azure / LiteLLM / vLLM)
LLM_PROVIDER=gemini

# Gemini 設定
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3.8-flash

# OpenAI 相容介面設定
OPENAI_API_KEY=sk-proj-xxxx
OPENAI_BASE_URL=[https://api.openai.com/v1](https://api.openai.com/v1)
OPENAI_MODEL=gpt-4o-mini
```

### 3. 各模組獨立點火測試
```bash
# 測試 1: 驗證 LLM 引擎、Pydantic 結構化輸出與 Async 批次併發
python -m core.llm_engine

# 測試 2: 驗證 Hybrid RAG (BM25 + Vector RRF) 與 Citation 溯源問答
python -m core.rag_pipeline

# 測試 3: 驗證 ReAct Agent 多步推理與工具調用
python -m core.agent_tools
```

### 4. 啟動視覺化介面或 API 服務
```bash
# 啟動 Streamlit 互動式系統介面 (預設 http://localhost:8501)
streamlit run ui_templates/app_streamlit.py

# 啟動 FastAPI 服務 (預設 http://localhost:8000/docs 查看 Swagger UI)
uvicorn ui_templates.app_fastapi:app --reload --port 8000
```

---

## 💻 核心模組調用範例 (Usage Snippets)

### 1. 結構化資料萃取與非同步高速批處理
```python
import asyncio
from pydantic import BaseModel, Field
from core.llm_engine import LLMEngine

class DefectReport(BaseModel):
    component: str = Field(description="發生異常的硬體零件名稱")
    severity: str = Field(description="嚴重程度: Low, Medium, High")
    root_cause: str = Field(description="推測的根本原因摘要")

engine = LLMEngine()

# 單筆強型別萃取
res = engine.generate_structured("PSU-800W 高溫測試電容爆裂導致斷電", response_schema=DefectReport)
print(res.component, res.severity)

# 多筆非同步併發處理 (內建 Semaphore 防打爆 Rate Limit)
async def main():
    logs = ["風扇異音但轉速正常", "PCIe 插槽焊點脫落無法過電"]
    results = await engine.batch_generate(logs, response_schema=DefectReport, max_concurrency=5)
    print(results)

asyncio.run(main())
```

### 2. 三行程式碼建立企業級 Hybrid RAG
```python
from core.data_loader import UniversalDataLoader
from core.rag_pipeline import SimpleHybridRAG

loader = UniversalDataLoader(chunk_size=800, chunk_overlap=150)
chunks = loader.load_any("./data")  # 自動解析資料夾內所有 PDF(含表格)/CSV/JSON/MD

rag = SimpleHybridRAG()
rag.ingest(chunks)

response = rag.query("請問 PSU-800W 的最高轉換效率是多少？遇到 ERR-092 該如何處理？")
print(f"回答: {response.answer}\n來源: {response.citations}\n信心度: {response.confidence}")
```

### 3. 自定義工具掛載至 ReAct Agent
```python
from core.agent_tools import ToolAgent

agent = ToolAgent(max_steps=5)

@agent.register_tool
def check_stock(part_id: str) -> dict:
    """查詢指定料號的庫存數量與美金單價"""
    db = {"PSU-800W": {"stock": 50, "price": 120.0}}
    return db.get(part_id, {"error": "查無此料號"})

result = agent.run("幫我查 PSU-800W 庫存夠不夠買 30 顆？總共多少錢？")
print(result["answer"])
```

---

## 🧠 架構設計決策與生產環境演進 (Architecture Design & Q&A)

以下記錄本架構在設計時針對可靠性、檢索精準度與擴展性的工程取捨（Trade-offs）與未來規模化（Scaling to Production）演進藍圖：

### Q1：為什麼 RAG 採用 `BM25 + Vector` 搭配 `RRF` 融合，而不是純向量搜尋？公式中的 `60` 代表什麼？
* 設計痛點：在科技製造業場景中，文件包含大量精確型號、料號與錯誤代碼（如 `PSU-800W-B2`、`ERR-092`）。純向量檢索（Dense Retrieval）擅長捕捉語意，但對一字之差的英數型號容易混淆；加入 `BM25`（Sparse Retrieval）能確保精確字詞匹配。
* 為什麼用 RRF（Reciprocal Rank Fusion）：BM25 的分數無上限，而 Cosine Similarity 介於 `-1 ~ 1`，兩者尺度不同無法直接線性相加。RRF 改以「各自的名次（Rank）」進行倒數計分：
  **RRF Score (d)** = Σ 1 / (k + rankᵣ(d))

  其中：
  - r ∈ {BM25, Vector}
  - k：平滑常數（Smoothing Constant），用來抑制單一檢索器將誤判文件排在第一名時所產生的極端權重影響。
  - rankᵣ(d)：文件 d 在檢索方法 r 中的排名

* 10 萬份文件規模化演進（Production Scaling）：
  1. 儲存層：將 In-Memory 的 `ChromaDB` 與 `BM25Okapi` 遷移至原生支援 Hybrid Search 與持久化叢集的 Qdrant / Milvus 或 Elasticsearch / OpenSearch。
  2. 精排層（Reranking）：在 RRF 粗篩出 Top-50 候選區塊後，串接一層 Cross-Encoder Reranker（如 `bge-reranker-large` 或 Cohere Rerank）精選出 Top-5 再送入 LLM，大幅提升 Context 精準度。

---

### Q2：解析 PDF 表格轉成 Markdown 後，若遇到跨頁大表格或被 Chunking 切斷導致遺失表頭（Header），如何解決？
* 現階段取捨：在快速原型階段，透過 `pdfplumber` 轉為 Markdown 表格並搭配 `chunk_overlap=150` 的滑動視窗保留上下文。
* 生產環境進階解法：
  1. 表頭強制注入（Header Injection）：識別出 Markdown 表格區塊後，改以「資料列（Row）」為最小切分單位；每當切出新的表格 Chunk 時，自動在該 Chunk 開頭重複拼接第一列的表頭（Header）與該表格的上下文標題，確保每個切片獨立被檢索時仍具備完整的欄位定義。
  2. 父子文件檢索（Parent-Child Chunking）：以單一資料列或小段落建立細粒度子區塊（Child Chunks）供向量檢索命中，但實際回傳給 LLM 的是其對應的完整表格或完整頁面（Parent Document）。

---

### Q3：為什麼不直接使用各家 SDK 原生的 `tools` / Function Calling 參數，而要用 Pydantic 自建 `ReAct` 迴圈？
* 100% 跨模型可移植性（Portability）：企業內部常需在雲端模型（Gemini / OpenAI）與地端開源模型（vLLM 架設之 Llama / Qwen）間切換。各家對原生 Tool Calling 的支援度與格式差異極大，但透過 `Structured Outputs (JSON Schema)` 驅動自建迴圈，能保證所有模型行為完全一致。
* 強制思考鏈與可觀測性（CoT & Observability）：在 `AgentDecision` Schema 中強制要求模型在決定 `action` 前必須先輸出 `thought` 欄位，不僅顯著降低幻覺與選錯工具的機率，更能將每一步的推理軌跡（Trace History）完整記錄於前端或 Log 供企業稽核。
* 容錯自癒能力（Self-Healing）：當工具調用發生轉型失敗或查無資料等 Exception 時，迴圈能優雅攔截錯誤並將錯誤訊息包裝成 `Observation` 餵回給 LLM，讓模型在下一輪自動修正傳參重試，避免系統直接崩潰。

---

### Q4：在大量批次處理（Batch Processing）時，如何應對嚴格的 API Rate Limit（RPM/TPM）與商業邏輯驗證？
* 流量與併發控制：
  - 目前透過 `asyncio.Semaphore(max_concurrency)` 限制同時飛行請求數（In-flight Requests），並搭配 `Tenacity` 進行指數退避重試（2s -> 4s -> 8s）。
  - 若面對極嚴格的每分鐘請求數（RPM）或 Token 數（TPM）限制，可進一步引入 令牌桶演算法（Token Bucket，如 `aiolimiter`） 控制每秒發送速率。
* 語意與商業邏輯驗證（Semantic Guardrails）：
  - `Pydantic` 保證了資料型別與結構正確；若需防範商業邏輯錯誤（例如：模型算出的折扣率小於 0 或大於 1），可直接於 Pydantic Model 中加入 `@field_validator`。一旦觸發 `ValidationError`，將錯誤訊息連同原輸出退回給 LLM 進行自我修正重试。

---

## 🛡️ 安全性提醒 (Security Note)
請確保專案根目錄下已建立 `.gitignore` 並包含以下內容，切勿將真實 API Key 上傳至公開儲存庫：
```gitignore
.env
.venv/
__pycache__/
*.pyc
chroma_db/
```