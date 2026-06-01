# core/jaq_brain.py
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os
import json

load_dotenv()

llm = ChatAnthropic(
    model="claude-3-5-sonnet-latest",
    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
    temperature=0.3
)

CEO_PROMPT = """
Sen JAQ'ın CEO'susun. Kullanıcı isteğini analiz et ve hangi ajana yönlendireceğine karar ver.

Mevcut ajanlar: ResearchAgent (araştırma ve fırsat tarama için)

Cevabını SADECE geçerli JSON olarak ver, başka hiçbir şey yazma:
{{
  "next": "ResearchAgent" veya "END",
  "task": "o ajana vereceğin net talimat",
  "reason": "kısaca neden bu ajanı seçtin"
}}

Kullanıcı mesajı: {input}
"""

prompt = ChatPromptTemplate.from_template(CEO_PROMPT)
chain = prompt | llm

def decide_next_agent(user_input: str) -> dict:
    try:
        response = chain.invoke({"input": user_input})
        text = response.content.strip()
        # Claude bazen ```json
        if text.startswith("```json"):
            text = text.split("```json")[1].split("```")[0].strip()
        return json.loads(text)
    except Exception as e:
        import traceback
        print(f"decide_next_agent hatası: {e}\n{traceback.format_exc()}")
        return {"next": "END", "task": "", "reason": "Karar alınamadı"}