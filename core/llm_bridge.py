"""
Agent 2: Custom LLM Connector & Strict Data-Grounded RAG Engine.
Allows the user to plug in their own LLM API (OpenAI, Gemini, Ollama, Groq, vLLM, etc.)
and ensures the model answers EXCLUSIVELY and STRICTLY from the ingested data/documents.
"""

import json
import sqlite3
import os
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional

DB_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "space_fire_system.db")

DEFAULT_SYSTEM_PROMPT = """أنت مساعد الذكاء الاصطناعي لطوارئ وأعطال حرائق المركبات الفضائية (NASA Spacecraft Fire Safety Officer).
تعليمات صارمة (STRICT DATA GROUNDING):
1. أجب على استفسار رائد الفضاء بناءً على البيانات والوثائق الفنية المرفقة أدناه حصراً وفقط.
2. لا تقم بالهلوسة أو تخمين أي معلومات غير موجودة في البيانات المدخلة.
3. إذا لم تجد الإجابة في البيانات، اذكر بوضوح أن الوثائق المتوفرة لم تتضمن هذا العطل.
4. حدد دائماً: سبب العطل المرجح، النظام المتأثر، والخطوات الإجرائية الفورية للسلامة.
"""

class Agent2LLMBridge:
    """Manages LLM API keys, endpoints, and data-grounded retrieval execution."""

    def __init__(self, db_path: str = DB_FILE, data_engine = None):
        self.db_path = db_path
        self.data_engine = data_engine
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent2_llm_config (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    api_key TEXT,
                    base_url TEXT DEFAULT 'https://api.openai.com/v1',
                    model_name TEXT DEFAULT 'gpt-4o-mini',
                    system_prompt TEXT,
                    is_enabled INTEGER DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                INSERT OR IGNORE INTO agent2_llm_config (id, api_key, base_url, model_name, system_prompt, is_enabled)
                VALUES (1, '', 'https://api.openai.com/v1', 'gpt-4o-mini', ?, 0)
            """, (DEFAULT_SYSTEM_PROMPT,))
            conn.commit()

    def get_config(self) -> Dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM agent2_llm_config WHERE id = 1")
            row = cursor.fetchone()
            if row:
                d = dict(row)
                # Mask API key for security in UI
                raw_key = d.get("api_key") or ""
                d["has_key"] = bool(raw_key.strip())
                d["masked_key"] = (raw_key[:4] + "..." + raw_key[-4:]) if len(raw_key) > 8 else ("***" if raw_key else "")
                return d
            return {"api_key": "", "base_url": "https://api.openai.com/v1", "model_name": "gpt-4o-mini", "is_enabled": 0}

    def save_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        api_key = config_data.get("api_key", "").strip()
        base_url = config_data.get("base_url", "https://api.openai.com/v1").strip().rstrip('/')
        model_name = config_data.get("model_name", "gpt-4o-mini").strip()
        is_enabled = 1 if config_data.get("is_enabled") else 0
        sys_prompt = config_data.get("system_prompt", DEFAULT_SYSTEM_PROMPT)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # If empty api_key submitted and we already have one, keep existing key
            if not api_key:
                cursor.execute("SELECT api_key FROM agent2_llm_config WHERE id = 1")
                row = cursor.fetchone()
                if row and row[0]:
                    api_key = row[0]

            cursor.execute("""
                UPDATE agent2_llm_config
                SET api_key = ?, base_url = ?, model_name = ?, system_prompt = ?, is_enabled = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = 1
            """, (api_key, base_url, model_name, sys_prompt, is_enabled))
            conn.commit()

        return self.get_config()

    def query_grounded_agent2(self, user_message: str, fallback_safety_bot) -> Dict[str, Any]:
        """
        Executes strict data-grounded RAG query:
        1. Searches ingested documents for relevant context.
        2. If LLM API is configured: Calls the model with strict grounding prompt.
        3. If no LLM API: Uses our local safety knowledge base + retrieved dataset chunks.
        """
        cfg = self.get_config()
        api_key = cfg.get("api_key", "").strip()
        base_url = cfg.get("base_url", "https://api.openai.com/v1").rstrip('/')
        model_name = cfg.get("model_name", "gpt-4o-mini")
        is_enabled = bool(cfg.get("is_enabled", 0))

        # Retrieve relevant context chunks from uploaded datasets/manuals
        retrieved_chunks = []
        if self.data_engine:
            retrieved_chunks = self.data_engine.search_rag_context("agent2", user_message, limit=4)

        context_block = "\n---\n".join(retrieved_chunks) if retrieved_chunks else "لا توجد وثائق إضافية مرفوعة؛ اعتمد على بروتوكولات ناسا الأساسية."

        # If LLM API is active and key is provided -> Call LLM
        if is_enabled and api_key:
            system_content = f"{cfg.get('system_prompt', DEFAULT_SYSTEM_PROMPT)}\n\n[البيانات والوثائق الفنية المعتمدة المسترجعة]:\n{context_block}"
            
            payload = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": user_message}
                ],
                "temperature": 0.1
            }

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }

            url = f"{base_url}/chat/completions"
            try:
                req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
                with urllib.request.urlopen(req, timeout=15) as resp:
                    resp_data = json.loads(resp.read().decode('utf-8'))
                    llm_text = resp_data["choices"][0]["message"]["content"]

                    return {
                        "mode": "CUSTOM_LLM_RAG",
                        "model": model_name,
                        "reply": llm_text,
                        "retrieved_sources_count": len(retrieved_chunks),
                        "retrieved_context_snippets": retrieved_chunks[:2],
                        "chat_response_markdown": llm_text
                    }
            except Exception as e:
                print(f"[Agent 2 LLM Call Error]: {e}. Falling back to internal engine.")

        # Fallback to internal grounded safety engine
        base_diagnosis = fallback_safety_bot.analyze_incident(user_message)
        response_md = base_diagnosis["chat_response_markdown"]

        if retrieved_chunks:
            extra_info = "\n\n📄 **بيانات إضافية مستخرجة من الوثائق المدربة:**\n" + "\n".join([f"• {c[:180]}..." for c in retrieved_chunks[:2]])
            response_md += extra_info

        return {
            "mode": "INTERNAL_GROUNDED_ENGINE",
            "model": "NASA Space Safety Expert System",
            "category": base_diagnosis.get("category"),
            "root_cause_diagnosis": base_diagnosis.get("root_cause_diagnosis"),
            "affected_subsystem": base_diagnosis.get("affected_subsystem"),
            "hazard_level": base_diagnosis.get("hazard_level"),
            "recommended_actions": base_diagnosis.get("recommended_actions"),
            "retrieved_sources_count": len(retrieved_chunks),
            "chat_response_markdown": response_md
        }

    def generate_agent2_bridge_spec(self, base_url: str = "http://localhost:8500") -> Dict[str, Any]:
        """Provides frontend developers with exact request/response schemas for Agent 2."""
        endpoint = f"{base_url}/api/chat/agent2"
        return {
            "agent_id": "agent2",
            "endpoint_url": endpoint,
            "method": "POST",
            "input_schema": {
                "message": "نص استفسار المستخدم أو وصف الحريق الصغير"
            },
            "output_schema": {
                "mode": "CUSTOM_LLM_RAG | INTERNAL_GROUNDED_ENGINE",
                "model": "اسم الموديل المستخدم",
                "chat_response_markdown": "الرد الكامل المعتمد على البيانات الفنية",
                "root_cause_diagnosis": "سبب المشكلة",
                "affected_subsystem": "النظام المتأثر",
                "recommended_actions": ["خطوة 1", "خطوة 2"]
            },
            "fetch_snippet": f"""// كود ربط شات Agent 2 بالفرونت إند:
const res = await fetch('{endpoint}', {{
  method: 'POST',
  headers: {{ 'Content-Type': 'application/json' }},
  body: JSON.stringify({{
    message: 'دخان ورائحة احتراق بلاستيك في لوحة القواطع'
  }})
}});
const data = await res.json();
console.log('رد الشات المعتمد على البيانات:', data.chat_response_markdown);"""
        }
