import sys, json
import requests

print("=" * 60)
print("测试4: 端到端 API 集成测试")
print("=" * 60)

jd = """高级Python后端开发工程师
要求：
1. 5年以上Python开发经验，精通FastAPI/Django框架
2. 有大规模分布式系统设计经验，熟悉微服务架构
3. 熟悉Docker、Kubernetes等容器化技术
4. 有AI/LLM项目经验者优先
5. 熟悉PostgreSQL、Redis等数据库"""

with open("test_resume.pdf", "rb") as f:
    files = {"file": ("resume.pdf", f, "application/pdf")}
    data = {"job_description": jd}

    print("发送 POST /api/v1/resume/analyze ...")
    resp = requests.post(
        "http://localhost:8080/api/v1/resume/analyze",
        files=files,
        data=data,
        timeout=120,
    )

if resp.status_code == 200:
    result = resp.json()
    print(f"HTTP {resp.status_code} OK")
    print(f"来源缓存: {result.get('from_cache')}")

    match = result.get("match", {})
    if match:
        print()
        print("--- 评分结果 ---")
        print(f"综合得分:   {match['overall_score']} 分")
        print(f"技能匹配:   {match['skill_score']} 分")
        print(f"经验匹配:   {match['experience_score']} 分")
        print(f"匹配亮点:   {match['highlights']}")
        print(f"缺失项:     {match['gaps']}")
        print(f"综合评价:   {match['recommendation']}")

    resume = result.get("resume", {})
    if resume.get("basic_info"):
        bi = resume["basic_info"]
        print()
        print("--- 简历解析 ---")
        print(f"姓名: {bi['name']} | 电话: {bi['phone']} | 邮箱: {bi['email']}")
        print(f"求职意向: {resume.get('job_intention', 'N/A')}")
        print(f"技能: {', '.join(resume.get('skills', []))}")
        print(f"教育经历: {len(resume.get('education', []))} 条")
        print(f"工作经历: {len(resume.get('work_experience', []))} 条")
        print(f"项目经历: {len(resume.get('projects', []))} 条")

    print()
    print("OK: 端到端 API 集成测试 通过")
else:
    print(f"FAIL: HTTP {resp.status_code}")
    print(resp.text)
    sys.exit(1)
