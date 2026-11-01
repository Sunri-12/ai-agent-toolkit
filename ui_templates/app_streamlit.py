# ui_templates/app_streamlit.py
import sys
from pathlib import Path

# 確保能 import 根目錄的 core 模組
sys.path.append(str(Path(__file__).resolve().parent.parent))

import streamlit as st
from core.llm_engine import LLMEngine
from core.data_loader import UniversalDataLoader
from core.rag_pipeline import SimpleHybridRAG

st.set_page_config(page_title="AI 實作系統原型", layout="wide")
st.title("⚡ 企業級 AI 智能分析與知識庫系統")

# 初始化 Session State (避免每次點擊重新載入模型)
if "llm" not in st.session_state:
    st.session_state.llm = LLMEngine()
if "rag" not in st.session_state:
    st.session_state.rag = SimpleHybridRAG(st.session_state.llm)
if "messages" not in st.session_state:
    st.session_state.messages = []

# 側邊欄：知識庫資料載入區
with st.sidebar:
    st.header("📂 資料載入與設定")
    data_path = st.text_input("輸入資料夾或檔案路徑", value="./data")
    if st.button("🚀 建立 / 更新 Hybrid 索引"):
        with st.spinner("解析文件與建立向量+BM25索引中..."):
            try:
                loader = UniversalDataLoader()
                chunks = loader.load_any(data_path)
                st.session_state.rag.ingest(chunks)
                st.success(f"成功匯入 {len(chunks)} 個知識區塊！")
            except Exception as e:
                st.error(f"匯入失敗: {e}")

# 主畫面：對話與來源追蹤
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("請輸入您的問題..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("檢索與推理中..."):
            if st.session_state.rag.chunks:
                res = st.session_state.rag.query(prompt, top_k=4, structured=True)
                reply = f"{res.answer}\n\n---\n**🎯 信心度:** `{res.confidence}` | **📚 參考來源:** `{', '.join(res.citations)}`"
            else:
                reply = st.session_state.llm.generate_text(prompt)
            st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})