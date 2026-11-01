你在串接 Gemini 或 OpenAI 的 Structured Outputs (Pydantic) 時有沒有遇過什麼坑？

有！在實作動態工具呼叫（Dynamic Tool Calling）或處理未知 JSON 時，如果在 Pydantic 裡面寫 Dict[str, Any]，轉出來的 JSON Schema 會包含 additionalProperties: true。
但無論是 Gemini Developer API 還是 OpenAI 的 Strict Mode，底層在做 Constrained Decoding（受限解碼）時都不支援無固定 Schema 的動態字典。
所以我特地把動態參數欄位設計為 JSON String (action_input_json: str) 並在框架層做 json.loads 與容錯攔截，完美解決跨模型 Schema 限制！