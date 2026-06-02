import requests
import time

print("=" * 60)
print("测试5: 缓存命中逻辑")
print("=" * 60)

jd = """高级Python后端开发工程师
要求：
1. 5年以上Python开发经验，精通FastAPI/Django框架
2. 有大规模分布式系统设计经验，熟悉微服务架构
3. 熟悉Docker、Kubernetes等容器化技术
4. 有AI/LLM项目经验者优先
5. 熟悉PostgreSQL、Redis等数据库"""

print("相同PDF+JD 第2次调用（应命中缓存）...")
t_start = time.time()
with open("test_resume.pdf", "rb") as f:
    resp = requests.post(
        "http://localhost:8080/api/v1/resume/analyze",
        files={"file": ("resume.pdf", f, "application/pdf")},
        data={"job_description": jd},
        timeout=120,
    )
elapsed = time.time() - t_start

result = resp.json()
print(f"耗时: {elapsed:.3f}s")
print(f"HTTP: {resp.status_code}")
print(f"来源缓存: {result['from_cache']}")
print(f"综合得分: {result['match']['overall_score']} 分")

if result["from_cache"]:
    print()
    print("OK: 缓存命中 - 秒级响应，无需消耗Token")
else:
    print()
    print("INFO: 缓存未命中 (服务重启导致内存缓存清空，属于正常行为)")

print()
print("第3次调用（同请求应命中缓存）...")
t_start = time.time()
with open("test_resume.pdf", "rb") as f:
    resp = requests.post(
        "http://localhost:8080/api/v1/resume/analyze",
        files={"file": ("resume.pdf", f, "application/pdf")},
        data={"job_description": jd},
        timeout=120,
    )
elapsed = time.time() - t_start

result = resp.json()
print(f"耗时: {elapsed:.3f}s")
print(f"来源缓存: {result['from_cache']}")

if result["from_cache"]:
    print("OK: 缓存命中测试 通过")
else:
    print("FAIL: 缓存命中测试 失败")
