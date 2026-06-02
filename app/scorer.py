import json
import logging

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL
from app.models import MatchScore

logger = logging.getLogger(__name__)

SCORE_SCHEMA_JSON = """{
  "overall_score": 85.0,
  "skill_score": 90.0,
  "experience_score": 77.5,
  "highlights": "匹配亮点，50字以内",
  "gaps": "缺失项，50字以内",
  "recommendation": "综合评价与建议，100字以内"
}"""

_scoring_llm = None

_SCORING_SYSTEM = """你是一位资深的技术HR和招聘专家，擅长评估候选人与岗位的匹配度。

评分规则：
1. 从「技能匹配度」和「经验匹配度」两个维度进行打分
2. 技能匹配度（S_skill）：0-100分，考察候选人的技术栈与岗位要求是否契合
3. 经验匹配度（S_exp）：0-100分，考察工作年限、项目经验、行业背景是否匹配
4. 综合得分公式：S_total = 0.6 * S_skill + 0.4 * S_exp（保留一位小数）
5. 突出点（highlights）：候选人简历中最匹配岗位的亮点，50字以内
6. 缺失项（gaps）：候选人相对于岗位要求的明显不足，50字以内
7. 综合评价（recommendation）：整体评价与建议，100字以内

请以专业、客观的态度进行评分，不要刻意拔高或压低分数。

你必须严格按照以下 JSON 格式输出，不要输出任何其他内容：
{format_schema}"""


def _get_scoring_llm():
    global _scoring_llm
    if _scoring_llm is None:
        _scoring_llm = ChatOpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL,
            model=DEEPSEEK_MODEL,
            temperature=0.3,
            model_kwargs={"response_format": {"type": "json_object"}},
        )
    return _scoring_llm


def _parse_llm_response(response) -> dict:
    content = response.content if hasattr(response, 'content') else str(response)
    content = content.strip()
    if content.startswith("```"):
        lines = content.split("\n")
        content = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        raise ValueError(f"无法解析 AI 返回的 JSON: {content[:300]}")


def score_resume(resume_json: str, job_description: str) -> MatchScore:
    llm = _get_scoring_llm()
    system_content = _SCORING_SYSTEM.format(format_schema=SCORE_SCHEMA_JSON)
    user_content = f"岗位描述：\n{job_description}\n\n候选人简历解析结果：\n{resume_json}\n\n请对该候选人进行岗位匹配度评分。"

    messages = [
        SystemMessage(content=system_content),
        HumanMessage(content=user_content),
    ]
    response = llm.invoke(messages)
    data = _parse_llm_response(response)
    return MatchScore(**data)
