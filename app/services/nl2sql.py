"""
NL2SQL 模块
功能：根据表结构和用户问题，生成 SQL 查询语句
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import re
import dashscope
from app.core.config import get_settings
from app.prompts import NL2SQL, NL2SQL_FEWSHOT_EXAMPLE, MANDATORY_CONDITIONS


def load_fewshot_examples():
    examples_file = os.path.join(
        os.path.dirname(__file__), 
        "..", 
        "data", 
        "fewshot_examples.json"
    )
    
    if os.path.exists(examples_file):
        with open(examples_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def filter_fewshot_examples(table_names: list[str], examples: list[dict]) -> list[dict]:
    if not examples or not table_names:
        return []
    
    table_names_lower = [t.lower() for t in table_names]
    
    related_examples = []
    for ex in examples:
        example_tables = [t.lower() for t in ex.get("tables", [])]
        if set(example_tables) & set(table_names_lower):
            related_examples.append(ex)
    
    return related_examples[:3]


class NL2SQLService:
    def __init__(self):
        settings = get_settings()
        if not settings.dashscope_api_key:
            raise ValueError("DASHSCOPE_API_KEY is not configured")
        dashscope.api_key = settings.dashscope_api_key
        self.model = settings.model_nl2sql
        self.max_rows = settings.max_sql_rows
        self.fewshot_examples = load_fewshot_examples()
    
    async def generate(self, table_descriptions: list[str], question: str) -> str:
        table_names = self._extract_table_names(table_descriptions)
        related_examples = filter_fewshot_examples(table_names, self.fewshot_examples)
        fewshot_section = self._build_fewshot_section(related_examples)
        
        tables_text = "\n\n".join(table_descriptions)
        
        prompt = NL2SQL.format(
            table_descriptions=tables_text,
            fewshot_section=fewshot_section,
            mandatory_conditions=MANDATORY_CONDITIONS,
            question=question
        )
        
        response = await dashscope.Generation.acall(
            model=self.model,
            messages=[{'role': 'user', 'content': prompt}],
            result_format='message',
            temperature=0
        )
        
        if response.status_code == 200:
            sql = self._extract_sql(response.output.choices[0].message.content)
            
            if "LIMIT" not in sql.upper():
                sql = f"{sql.rstrip(';')} LIMIT {self.max_rows}"
            
            return sql
        
        return ""
    
    def _extract_table_names(self, table_descriptions: list[str]) -> list[str]:
        table_names = []
        for desc in table_descriptions:
            match = re.search(r'表名[：:]\s*(\w+)', desc)
            if match:
                table_names.append(match.group(1))
        return table_names
    
    def _build_fewshot_section(self, examples: list[dict]) -> str:
        if not examples:
            return NL2SQL_FEWSHOT_EXAMPLE
        
        section = "参考示例：\n"
        for i, ex in enumerate(examples, 1):
            section += f"\n示例{i}：\n"
            section += f"问题：{ex['question']}\n"
            section += f"SQL：{ex['sql']}\n"
        
        return section
    
    def _extract_sql(self, text: str) -> str:
        sql_match = re.search(r'```sql\s*(.*?)\s*```', text, re.DOTALL)
        if sql_match:
            return sql_match.group(1).strip()
        
        lines = text.strip().split('\n')
        for i, line in enumerate(lines):
            if line.strip().upper().startswith('SELECT'):
                return '\n'.join(lines[i:]).strip()
        
        return text.strip()
