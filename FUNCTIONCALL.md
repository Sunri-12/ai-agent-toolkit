## 函數庫導覽

### 1. tenacity
說明: Python 最主流的「自動重試（Retry）」函式庫。
用法: 專案中，它是用來設定指數退避重試（Exponential Backoff），專門抵抗網路瞬斷與 API 的 429 Rate Limit（請求頻率過高限流）報錯。
實務流程: 當程式呼叫 Gemini 或 OpenAI API 失敗拋出 Exception 時，tenacity 會攔截這個錯誤，不會馬上再撞牆一次，而是先等 2 秒重試第 1 次 ➔ 若再失敗就等 4 秒重試第 2 次 ➔ 再失敗等 8 秒重試第 3 次（2s ➔ 4s ➔ 8s）。

### 2. asyncio.Semaphore
說明: Python 內建 asyncio 模組裡的「非同步信號量（計數器鎖）」，用來限制同時處於執行狀態的非同步協程（Coroutine）數量上限。
用法: 專案中，在執行大規模非同步批次處理（Async Batching）時，用來當作「併發限流閥」控制同時在飛行的 API 請求數，避免瞬間打爆 API Rate Limit。
實務流程: 在 core/llm_engine.py 設定 asyncio.Semaphore(max_concurrency=5)。當一次發送多筆非同步任務時，每個任務在發送 await client.aio.models.generate_content() 請求前都必須先通過 async with semaphore: 匣門；系統一次只放行 5 個請求同時出去，第 6 個請求會在門口排隊，直到前面任一請求完成並釋放名額後才能遞補進入，且回傳順序與原始輸入完全一致。

### 3. pydantic
說明: Python 最主流的「強型別資料驗證與 Schema 約束」函式庫。
用法: 專案中，用來解決 LLM 輸出格式不穩定、JSON 解析崩潰（json.loads 報錯）的痛點，保證 100% 輸出合法 JSON；同時用來定義 RAGResponse 溯源格式並驅動跨廠牌的自癒式 ReAct Agent 迴圈。
實務流程: 先定義繼承自 BaseModel 的類別並透過 Field(description=...) 寫明欄位型別與約束（如強制要求輸出 answer、citations、confidence，或 Agent 的 thought 與 action_input_json） ➔ 呼叫 LLM API 時將該類別傳入結構化輸出設定鎖死底層生成格式 ➔ 模型回傳字串後由 Pydantic 自動解析並驗證型別，若工具執行拋出 Exception 則攔截並轉化為 Observation 餵回給模型自我修正重試。

### 4. pdfplumber
說明: 專門用來精準解析 PDF 文字座標與「抽取表格（Table Extraction）」的 Python 函式庫。
用法: 專案中，在 core/data_loader.py 用來解決傳統 PDF 讀取工具將表格文字暴力連成亂碼、導致「PDF 表格結構破碎、行列對不齊」的知識庫痛點。
實務流程: 讀取 PDF 文件時，透過 pdfplumber 偵測頁面線條與座標抽取表格資料 ➔ 自動將第一列設為表頭並補齊 | Header | 與分隔線，將表格完整還原為結構化 Markdown 格式讓 LLM 精準理解行列對應關係 ➔ 最後搭配滑動視窗切塊（Sliding Window Overlap）並自動注入檔名與頁碼（Page）Metadata 供後續溯源引用。

### 5. rank_bm25 / BM25Okapi
說明: 經典資訊檢索演算法 BM25（基於詞頻 TF 與逆向文件頻率 IDF 的字面關鍵字匹配演算法）的輕量級 Python 實作。
用法: 專案中，在 core/rag_pipeline.py 負責 Hybrid Search 的「精準關鍵字檢索」，克服純向量搜尋（Vector Search）只懂模糊語意、找不到一字之差的精確硬體料號或錯誤碼的痛點。
實務流程: 建置索引時，先將所有知識庫切塊（DocChunk）透過中英混合斷詞器切分為詞彙列表並丟入 BM25Okapi 建立索引 ➔ 當使用者提問時，將問題同樣進行斷詞並計算每個區塊的關鍵字匹配分數與排名（Rank），精準鎖定罕見專有名詞與型號代碼，交由後續 RRF 演算法融合。

### 6. chromadb
說明: 開源、輕量級的 AI 原生本地端向量資料庫（Vector Database）。
用法: 專案中，在 core/rag_pipeline.py 負責 Hybrid Search 的「語意模糊檢索（Semantic Search）」，採用純記憶體與本地輕量 Embedding 模型（如 all-MiniLM-L6-v2）建立索引，確保零外部伺服器依賴、秒級啟動且不消耗 API 額度。
實務流程: 匯入文件時，將切好的文字區塊與 Metadata（檔名、頁碼、列號）存入 ChromaDB 轉為向量索引 ➔ 檢索時計算餘弦相似度（Cosine Similarity）抓出語意最相近的區塊排名 ➔ 因 BM25 分數與餘弦相似度分數尺度不同無法直接相加，系統最後透過 RRF（Reciprocal Rank Fusion）倒數排名演算法融合兩邊名次，選出最終 Top-K 區塊送入 LLM 生成帶引用來源的回答。