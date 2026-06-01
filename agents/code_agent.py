# agents/code_agent.py
from __future__ import annotations

import logging

from langchain_core.messages import HumanMessage

from agents.base_agent import BaseAgent
from config.prompts import CODE_PROMPT

logger = logging.getLogger(__name__)

_LANG_PATTERNS: dict[str, list[str]] = {
    "python":     ["python", "fastapi", "django", "flask", "pandas", ".py"],
    "typescript": ["typescript", "ts", "react", "nextjs", "node"],
    "javascript": ["javascript", "js", "express", "vue"],
    "sql":        ["sql", "query", "select", "database", "postgres", "mysql"],
    "bash":       ["bash", "shell", "script", "linux", "terminal"],
}

_MODE_PATTERNS: dict[str, list[str]] = {
    "debug":    ["hata", "bug", "error", "çalışmıyor", "fix", "düzelt"],
    "review":   ["review", "incele", "kontrol", "analiz et", "değerlendir"],
    "refactor": ["refactor", "temizle", "düzenle", "iyileştir", "optimize"],
    "generate": ["yaz", "oluştur", "create", "implement", "ekle", "write"],
}

_MODE_INSTRUCTIONS: dict[str, str] = {
    "debug":    "Kodu analiz et, hatanın kök nedenini bul, düzeltilmiş versiyonu göster. Açıklama ekle.",
    "review":   "Kodu review et: güvenlik açıkları, performans sorunları, kod kalitesi. Madde madde raporla.",
    "refactor": "Kodu refactor et: okunabilirlik, DRY prensibi, tip güvenliği. Önce/sonra karşılaştırması yap.",
    "generate": "Temiz, production-ready kod yaz. Docstring, tip anotasyonu ve örnek kullanım ekle.",
}


def _detect_language(task: str) -> str:
    task_lower = task.lower()
    for lang, keywords in _LANG_PATTERNS.items():
        if any(kw in task_lower for kw in keywords):
            return lang
    return "python"


def _detect_mode(task: str) -> str:
    task_lower = task.lower()
    for mode, keywords in _MODE_PATTERNS.items():
        if any(kw in task_lower for kw in keywords):
            return mode
    return "generate"


class CodeAgent(BaseAgent):
    name = "CodeAgent"
    _base_system_prompt = CODE_PROMPT
    tools = []

    async def _execute(self, task: str, context: str) -> str:
        lang = _detect_language(task)
        mode = _detect_mode(task)
        instruction = _MODE_INSTRUCTIONS[mode]

        prompt = self._build_prompt(task=task, context=context)
        full_prompt = (
            f"{prompt}\n\n"
            f"**Tespit Edilen Dil:** {lang}\n"
            f"**Mod:** {mode}\n"
            f"**Talimat:** {instruction}"
        )

        logger.info(f"CodeAgent: lang={lang}, mode={mode}")
        response = await self.llm.ainvoke([HumanMessage(content=full_prompt)])
        return response.content
