import json
import logging

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL
from app.models import ResumeSchema

logger = logging.getLogger(__name__)

RESUME_SCHEMA_JSON = """{
  "basic_info": {"name": "姓名或null", "phone": "电话或null", "email": "邮箱或null"},
  "job_intention": "求职意向或null",
  "education": [{"school": "学校", "degree": "学历", "major": "专业", "graduate_year": "毕业年份或null"}],
  "work_experience": [{"company": "公司", "position": "职位", "start_date": "开始时间或null", "end_date": "结束时间或null", "description": "描述或null", "highlights": ["亮点"]}],
  "skills": ["技能列表"],
  "projects": [{"name": "项目名", "role": "角色或null", "description": "描述或null", "tech_stack": ["技术栈"]}],
  "self_evaluation": "自我评价或null"
}"""

_llm = None


def _get_llm():
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL,
            model=DEEPSEEK_MODEL,
            temperature=0.1,
            model_kwargs={"response_format": {"type": "json_object"}},
        )
    return _llm


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


_EXTRACTION_SYSTEM = """你是一位资深的人力资源专家和简历解析专家。请仔细阅读以下简历文本，并从中提取所有关键信息。

要求：
1. 必须准确识别姓名、电话、邮箱等基本信息
2. 识别教育经历，包含学校、学历、专业、毕业年份
3. 提取工作经历，包含公司、职位、起止时间、工作描述和亮点
4. 提取项目经历，包含项目名称、角色、描述和技术栈
5. 识别技能列表和求职意向
6. 如果有自我评价，也一并提取
7. 如果简历中没有某个字段的信息，请使用 null，不要编造内容

你必须严格按照以下 JSON 格式输出，不要输出任何其他内容：
{format_schema}"""

_EXTRACTION_SYSTEM_WITH_JD = """你是一位资深的人力资源专家和简历解析专家。请仔细阅读以下简历文本，并结合岗位描述进行分析。

要求：
1. 必须准确识别姓名、电话、邮箱等基本信息
2. 识别教育经历，包含学校、学历、专业、毕业年份
3. 提取工作经历，包含公司、职位、起止时间、工作描述和亮点
4. 提取项目经历，包含项目名称、角色、描述和技术栈
5. 识别技能列表和求职意向
6. 如果有自我评价，也一并提取
7. 如果简历中没有某个字段的信息，请使用 null，不要编造内容

你必须严格按照以下 JSON 格式输出，不要输出任何其他内容：
{format_schema}"""


def parse_resume(resume_text: str, job_description: str | None = None) -> ResumeSchema:
    llm = _get_llm()

    if job_description:
        system_content = _EXTRACTION_SYSTEM_WITH_JD.format(format_schema=RESUME_SCHEMA_JSON)
        user_content = f"岗位描述：\n{job_description}\n\n简历文本：\n{resume_text}\n\n请解析以上简历文本。"
    else:
        system_content = _EXTRACTION_SYSTEM.format(format_schema=RESUME_SCHEMA_JSON)
        user_content = f"请解析以下简历文本，提取所有关键信息：\n\n{resume_text}"

    messages = [
        SystemMessage(content=system_content),
        HumanMessage(content=user_content),
    ]
    response = llm.invoke(messages)
    data = _parse_llm_response(response)
    return ResumeSchema(**data)
