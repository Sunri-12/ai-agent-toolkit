# Project Context & Architecture Guide (F1 Starter Kit)

你正在協助我進行一場限時的 AI 工程師實作測驗。本專案已經預先建立並測試好 `core/` 核心模組與 `ui_templates/` 介面模板。

## ⚠️ 核心開發原則 (Core Directives)
1. 絕對不要重新造輪子：當需要呼叫 LLM、解析 PDF/CSV/JSON、建立 RAG 檢索、或實作 Tool Calling Agent 時，**必須直接 `import` `core/` 底下的現有模組**。
2. 環境變數已配置：API Key 與模型設定統一由 `.env` 與 `core.llm_engine.LLMEngine` 管理，請勿在程式碼中寫死 API Key。
3. 優先使用結構化輸出与併發：遇到資料萃取或分類任務，優先定義 `pydantic.BaseModel` 並使用 `engine.generate_structured()` 或 `await engine.batch_generate()`。

## 📦 現有模組快速調用指南 (API Reference)

### 1. `core.llm_engine.LLMEngine` (萬用 LLM 引擎，內建 Retry 與雙廠牌支援)
- `engine = LLMEngine()`
- `text = engine.generate_text(prompt, system_instruction="...", temperature=0.2)`
- `obj = engine.generate_structured(prompt, response_schema=MyPydanticModel, system_instruction="...")` -> 直接回傳驗證過的 Pydantic 實例。
- `results = await engine.batch_generate(prompts_list, system_instruction="...", response_schema=MyPydanticModel, max_concurrency=5)` -> 高速非同步批次處理。

### 2. `core.data_loader.UniversalDataLoader` (萬用檔案讀取與切塊器)
- `loader = UniversalDataLoader(chunk_size=800, chunk_overlap=150)`
- `chunks = loader.load_any("./data")` -> 支援單一檔案或整個資料夾 (自動解析 `.pdf` 含表格轉 Markdown、`.csv`、`.xlsx`、`.json`、`.md`、`.txt`)，回傳 `List[DocChunk]` (包含 `chunk_id`, `content`, `source`, `metadata`)。
- `summary_str = UniversalDataLoader.get_dataframe_summary("file.csv")` -> 產生給 LLM 看的 DataFrame 結構與範例摘要。

### 3. `core.rag_pipeline.SimpleHybridRAG` (BM25 + ChromaDB 向量 RRF 混合檢索)
- `rag = SimpleHybridRAG(llm_engine=engine)`
- `rag.ingest(chunks)` -> 傳入 `List[DocChunk]` 建立混合索引。
- `top_chunks = rag.search(query, top_k=4)` -> 回傳最相關的 `List[DocChunk]`。
- `res = rag.query(question, top_k=4, structured=True)` -> 回傳 `RAGResponse` (含 `res.answer`, `res.citations`, `res.confidence`)。

### 4. `core.agent_tools.ToolAgent` (跨廠牌 ReAct Function Calling Agent)
- `agent = ToolAgent(llm_engine=engine, max_steps=5)`
- 使用 `@agent.register_tool` 裝飾任何具有 Type Hints 與 Docstring 的 Python function。
- `result_dict = agent.run(user_query, verbose=True)` -> 回傳 `{"answer": str, "trace": list, "steps": int}`。

### 5. `ui_templates/` (快速展示介面)
- 若題目需要前端互動介面，基於 `ui_templates/app_streamlit.py` 修改。
- 若題目需要 REST API 服務，基於 `ui_templates/app_fastapi.py` 修改。