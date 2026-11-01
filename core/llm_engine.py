# core/llm_engine.py
import os
import asyncio
from typing import Type, TypeVar, List, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

# 載入環境變數
load_dotenv()

from google import genai
from google.genai import types
from openai import OpenAI, AsyncOpenAI

T = TypeVar("T", bound=BaseModel)


class LLMEngine:
    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None):
        self.provider = (provider or os.getenv("LLM_PROVIDER", "gemini")).lower()
        
        if self.provider == "gemini":
            self.api_key = os.getenv("GEMINI_API_KEY")
            self.model = model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
            self.client = genai.Client(api_key=self.api_key)
        elif self.provider == "openai":
            self.api_key = os.getenv("OPENAI_API_KEY")
            self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
            self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            self.async_client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        else:
            raise ValueError(f"不支援的 Provider: {self.provider}")

    # ==========================================
    # 1. 一般文字生成 (附帶自動 Retry 防護罩)
    # ==========================================
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def generate_text(
        self, 
        prompt: str, 
        system_instruction: str = "You are a helpful AI assistant.",
        temperature: float = 0.2
    ) -> str:
        if self.provider == "gemini":
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=temperature,
                ),
            )
            return response.text
        else:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
            )
            return response.choices[0].message.content

    # ==========================================
    # 2. 結構化輸出 (Pydantic 強制型別驗證 - 必考神器!)
    # ==========================================
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T],
        system_instruction: str = "Extract information accurately according to the schema.",
        temperature: float = 0.0
    ) -> T:
        if self.provider == "gemini":
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=temperature,
                    response_mime_type="application/json",
                    response_schema=response_schema,
                ),
            )
            # 直接轉回驗證過的 Pydantic 物件
            return response_schema.model_validate_json(response.text)
        else:
            response = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt}
                ],
                response_format=response_schema,
                temperature=temperature,
            )
            return response.choices[0].message.parsed

    # ==========================================
    # 3. 異步單筆與批次高速處理 (對付大量資料清理題)
    # ==========================================
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _agenerate_single(
        self, 
        prompt: str, 
        system_instruction: str, 
        response_schema: Optional[Type[T]] = None
    ):
        if self.provider == "gemini":
            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.1,
            )
            if response_schema:
                config.response_mime_type = "application/json"
                config.response_schema = response_schema

            # google-genai 的原生 async 呼叫 (.aio)
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=prompt,
                config=config,
            )
            if response_schema:
                return response_schema.model_validate_json(response.text)
            return response.text
        else:
            if response_schema:
                response = await self.async_client.beta.chat.completions.parse(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": prompt}
                    ],
                    response_format=response_schema,
                    temperature=0.1,
                )
                return response.choices[0].message.parsed
            else:
                response = await self.async_client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                )
                return response.choices[0].message.content

    async def batch_generate(
        self,
        prompts: List[str],
        system_instruction: str = "You are a helpful AI assistant.",
        response_schema: Optional[Type[T]] = None,
        max_concurrency: int = 5  # 控制同時最大請求數，避免觸發 Rate Limit
    ) -> List:
        semaphore = asyncio.Semaphore(max_concurrency)

        async def _worker( idx: int, p: str):
            async with semaphore:
                try:
                    res = await self._agenerate_single(p, system_instruction, response_schema)
                    return idx, res
                except Exception as e:
                    print(f"[Error] 第 {idx} 筆處理失敗: {e}")
                    return idx, None

        tasks = [_worker(i, p) for i, p in enumerate(prompts)]
        results = await asyncio.gather(*tasks)
        # 確保按照原本的順序排好回傳
        results.sort(key=lambda x: x[0])
        return [r[1] for r in results]


# ==========================================
# 🧪 點火測試 (執行 python core/llm_engine.py 即可驗證)
# ==========================================
if __name__ == "__main__":
    # 定義一個測試用的 Pydantic 結構
    class DefectAnalysis(BaseModel):
        component: str = Field(description="發生異常的硬體零件名稱")
        severity: str = Field(description="嚴重程度: Low, Medium, High")
        root_cause: str = Field(description="推測的根本原因摘要")

    engine = LLMEngine()
    print(f"🚀 啟動引擎測試 | Provider: {engine.provider} | Model: {engine.model}\n")

    # 測試 1: 結構化萃取
    test_log = "2026-10-30 產線回報：電源供應器 (PSU-500W) 在高溫燒機測試時出現電容爆裂，導致輸出電壓瞬間歸零，需立即停線檢修。"
    result = engine.generate_structured(
        prompt=f"請分析以下產線異常報告：\n{test_log}",
        response_schema=DefectAnalysis
    )
    print("✅ [結構化輸出測試成功]:")
    print(f"零件: {result.component} | 等級: {result.severity} | 原因: {result.root_cause}\n")

    # 測試 2: Async 批次併發
    async def test_batch():
        logs = [
            "LED 指示燈亮度略微不均，不影響功能。",
            "主機板 PCIe 插槽焊點脫落，無法讀取顯卡。"
        ]
        batch_res = await engine.batch_generate(
            prompts=logs,
            system_instruction="分析產線異常報告",
            response_schema=DefectAnalysis,
            max_concurrency=2
        )
        print("✅ [Async 批次併發測試成功]:")
        for item in batch_res:
            print(item.model_dump())

    asyncio.run(test_batch())