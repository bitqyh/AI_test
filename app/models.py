from typing import Optional, List
from pydantic import BaseModel, Field


class GeneralInfo(BaseModel):
    name: Optional[str] = Field(None, description="候选人姓名")
    phone: Optional[str] = Field(None, description="电话号码")
    email: Optional[str] = Field(None, description="电子邮箱")


class Education(BaseModel):
    school: str = Field(description="毕业院校")
    degree: str = Field(description="学历层次，如本科/硕士/博士")
    major: str = Field(description="专业名称")
    graduate_year: Optional[str] = Field(None, description="毕业年份")


class WorkExperience(BaseModel):
    company: str = Field(description="公司名称")
    position: str = Field(description="职位名称")
    start_date: Optional[str] = Field(None, description="开始时间")
    end_date: Optional[str] = Field(None, description="结束时间")
    description: Optional[str] = Field(None, description="工作描述")
    highlights: Optional[List[str]] = Field(None, description="工作亮点")


class Project(BaseModel):
    name: str = Field(description="项目名称")
    role: Optional[str] = Field(None, description="项目角色")
    description: Optional[str] = Field(None, description="项目描述")
    tech_stack: Optional[List[str]] = Field(None, description="使用的技术栈")


class ResumeSchema(BaseModel):
    basic_info: Optional[GeneralInfo] = Field(None, description="基本信息")
    job_intention: Optional[str] = Field(None, description="求职意向")
    education: Optional[List[Education]] = Field(None, description="教育经历")
    work_experience: Optional[List[WorkExperience]] = Field(None, description="工作经历")
    skills: Optional[List[str]] = Field(None, description="技能列表")
    projects: Optional[List[Project]] = Field(None, description="项目经历")
    self_evaluation: Optional[str] = Field(None, description="自我评价")


class MatchScore(BaseModel):
    overall_score: float = Field(description="综合匹配度百分制分数")
    skill_score: float = Field(description="技能匹配得分")
    experience_score: float = Field(description="经验匹配得分")
    highlights: str = Field(description="匹配亮点，50字以内")
    gaps: str = Field(description="缺失项，50字以内")
    recommendation: str = Field(description="综合评价与建议，100字以内")


class AnalysisResult(BaseModel):
    resume: ResumeSchema = Field(description="简历解析结果")
    match: Optional[MatchScore] = Field(None, description="岗位匹配分析结果")
    from_cache: bool = Field(False, description="是否来自缓存")
