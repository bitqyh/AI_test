import sys, json
sys.path.insert(0, '.')

from app.pdf_loader import load_pdf_text
from app.ai_parser import parse_resume
from app.scorer import score_resume

print('=' * 60)
print('测试3: 简历评分与匹配 (DeepSeek)')
print('=' * 60)

text = load_pdf_text('test_resume.pdf')
parsed = parse_resume(text)
resume_json = json.dumps(parsed.model_dump(), ensure_ascii=False)

job_description = """高级Python后端开发工程师
要求：
1. 5年以上Python开发经验，精通FastAPI/Django框架
2. 有大规模分布式系统设计经验，熟悉微服务架构
3. 熟悉Docker、Kubernetes等容器化技术
4. 有AI/LLM项目经验者优先
5. 熟悉PostgreSQL、Redis等数据库"""

print(f"岗位描述: {job_description.strip()[:80]}...")

result = score_resume(resume_json, job_description)
data = result.model_dump()

print()
print('--- 评分结果 ---')
print(f"综合得分:   {data['overall_score']} 分")
print(f"技能匹配:   {data['skill_score']} 分")
print(f"经验匹配:   {data['experience_score']} 分")
print(f"匹配亮点:   {data['highlights']}")
print(f"缺失项:     {data['gaps']}")
print(f"综合评价:   {data['recommendation']}")
print()
print('OK: 简历评分与匹配 通过')
