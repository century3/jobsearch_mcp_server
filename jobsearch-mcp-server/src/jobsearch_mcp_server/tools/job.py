from typing import Any
from pathlib import Path
import re
from ..llm.llm import LLMClient 
from ..prompt.prompt import Job_Search_Prompt
from ..selenium.listjob import listjob_by_keyword

class JobTools(LLMClient):
    @staticmethod
    def _extract_top_n(resume: str, default_n: int = 8) -> int:
        m = re.search(r"(\d+)\s*个", resume)
        if not m:
            return default_n
        n = int(m.group(1))
        return max(1, min(n, 20))

    @staticmethod
    def _parse_jobs(job_text: str) -> list[dict[str, str]]:
        blocks = re.split(r"\n\s*\d+\.\s*岗位名称:", job_text)
        jobs: list[dict[str, str]] = []
        for block in blocks:
            block = block.strip()
            if not block:
                continue

            lines = [line.strip() for line in block.splitlines() if line.strip()]
            if not lines:
                continue

            # First line is the job title after split.
            record: dict[str, str] = {"岗位名称": lines[0]}
            for line in lines[1:]:
                if "公司名称:" in line:
                    record["公司名称"] = line.split("公司名称:", 1)[1].strip()
                elif "岗位要求:" in line:
                    record["岗位要求"] = line.split("岗位要求:", 1)[1].strip()
                elif "技能要求:" in line:
                    record["技能要求"] = line.split("技能要求:", 1)[1].strip()
                elif "薪资待遇:" in line:
                    record["薪资待遇"] = line.split("薪资待遇:", 1)[1].strip()
            jobs.append(record)
        return jobs

    @staticmethod
    def _extract_resume_features(resume: str) -> dict[str, Any]:
        lower = resume.lower()

        year = None
        m_year = re.search(r"(\d+)\s*年", resume)
        if m_year:
            year = int(m_year.group(1))

        salary_k = None
        m_salary = re.search(r"(\d+)\s*[kK]", resume)
        if m_salary:
            salary_k = int(m_salary.group(1))

        degree = ""
        for d in ["博士", "硕士", "本科", "大专", "学历不限"]:
            if d in resume:
                degree = d
                break

        skill_keywords = [
            "ai agent", "rag", "python", "golang", "java", "prompt", "postgresql",
            "django", "flask", "spark", "redis", "mysql", "大模型", "机器学习",
            "自然语言处理", "深度学习", "多模态",
        ]
        skills = {kw for kw in skill_keywords if kw in lower or kw in resume}

        return {
            "year": year,
            "salary_k": salary_k,
            "degree": degree,
            "skills": skills,
        }

    @staticmethod
    def _degree_ok(job_req: str, resume_degree: str) -> bool:
        if not job_req or not resume_degree:
            return True
        if "学历不限" in job_req:
            return True
        order = {"大专": 1, "本科": 2, "硕士": 3, "博士": 4}
        req = None
        for d in ["博士", "硕士", "本科", "大专"]:
            if d in job_req:
                req = d
                break
        if req is None or resume_degree not in order:
            return True
        return order[resume_degree] >= order[req]

    @staticmethod
    def _exp_score(job_req: str, year: int | None) -> int:
        if year is None or not job_req:
            return 0
        if "经验不限" in job_req:
            return 2
        m = re.search(r"(\d+)\s*-\s*(\d+)\s*年", job_req)
        if m:
            low, high = int(m.group(1)), int(m.group(2))
            if low <= year <= high:
                return 3
            if year > high:
                return 2
            return -2
        return 0

    @staticmethod
    def _salary_score(salary_text: str, expect_k: int | None) -> int:
        if expect_k is None or not salary_text:
            return 0
        m = re.search(r"(\d+)\s*-\s*(\d+)\s*[kK]", salary_text)
        if not m:
            return 0
        low, high = int(m.group(1)), int(m.group(2))
        if low <= expect_k <= high:
            return 4
        if high < expect_k:
            return -3
        return 1

    @staticmethod
    def _skill_score(skill_text: str, skills: set[str]) -> tuple[int, list[str]]:
        if not skill_text:
            return 0, []
        matched: list[str] = []
        lower = skill_text.lower()
        for s in skills:
            if s in lower or s in skill_text:
                matched.append(s)
        return len(matched) * 2, matched

    def register_tools(self, mcp: Any):
        """Register job tools."""
        @mcp.tool(description="根据求职者的期望岗位获取岗位列表数据")
        def get_joblist_by_expect_job(job: str) -> str:
            """根据求职者的期望岗位获取岗位列表数据"""
            # 为了测试方便，可以改成从本地文件获取岗位列表
            job_file = Path(__file__).resolve().parents[1] / "job.txt"
            if not job_file.exists():
                self.logger.error(f"岗位数据文件不存在: {job_file}")
                return "岗位查询工具目前不可用：后台数据文件缺失（job.txt）。"

            with job_file.open('r', encoding='utf-8') as f:
                jobs = f.read()
            
            #使用无头浏览器获取岗位
            #jobs = listjob_by_keyword(job)

            return jobs

        @mcp.tool(description="根据岗位列表以及求职者的简历获取适合该求职者的岗位以及求职建议")
        def get_job_by_resume(jobs: str, resume: str) -> str:
            """根据岗位列表以及求职者的简历获取适合该求职者的岗位以及求职建议"""
            parsed_jobs = self._parse_jobs(jobs)
            if not parsed_jobs:
                return "未解析到岗位数据，请稍后重试。"

            features = self._extract_resume_features(resume)
            ranked: list[tuple[int, dict[str, str], list[str]]] = []

            for job in parsed_jobs:
                job_req = job.get("岗位要求", "")
                if not self._degree_ok(job_req, features["degree"]):
                    continue

                score = 0
                reasons: list[str] = []

                s_exp = self._exp_score(job_req, features["year"])
                score += s_exp
                if s_exp > 0:
                    reasons.append("经验匹配")

                salary_text = job.get("薪资待遇", "")
                s_salary = self._salary_score(salary_text, features["salary_k"])
                score += s_salary
                if s_salary > 0:
                    reasons.append("薪资区间匹配")

                s_skill, matched_skills = self._skill_score(job.get("技能要求", ""), features["skills"])
                score += s_skill
                if matched_skills:
                    reasons.append("技能匹配: " + ",".join(matched_skills[:4]))

                # Boost for AI Agent / RAG related job titles.
                title = job.get("岗位名称", "")
                title_lower = title.lower()
                if "ai agent" in title_lower or "agent" in title_lower or "大模型" in title:
                    score += 2
                    reasons.append("岗位方向匹配")

                ranked.append((score, job, reasons))

            if not ranked:
                return "未找到满足学历/经验约束的岗位，建议放宽条件后重试。"

            ranked.sort(key=lambda x: x[0], reverse=True)
            top_n = self._extract_top_n(resume, default_n=8)
            top = ranked[:top_n]

            lines = [f"为你匹配到最合适的 {len(top)} 个岗位："]
            for idx, (score, job, reasons) in enumerate(top, 1):
                lines.append(f"\n{idx}. 岗位名称: {job.get('岗位名称', '未知')}\n公司名称: {job.get('公司名称', '未知')}\n岗位要求: {job.get('岗位要求', '未知')}\n技能要求: {job.get('技能要求', '未知')}\n薪资待遇: {job.get('薪资待遇', '未知')}\n匹配理由: {'；'.join(reasons) if reasons else '综合条件匹配'}\n匹配得分: {score}")

            lines.append("\n求职建议: 重点突出 AI Agent / RAG 项目中的业务结果（效率提升、成本下降、准确率提升），并在简历中补充 Python 与工程化落地细节。")
            return "\n".join(lines)