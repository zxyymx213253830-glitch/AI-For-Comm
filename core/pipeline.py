# -*- coding: utf-8 -*-
"""
科研任务流水线 —— 多智能体协作完成一次完整调研

双模式架构中的"科研任务"模式（快问快答见 main.py 关键词路由）。流程：
  1. plan       问题拆解     —— 规划者 Agent 把课题拆成若干带专家归属的子问题(JSON)
  2. literature 文献调研     —— lit_review_agent 公网检索 + 平台KB 综述
  3. experts    并行领域专家 —— 子问题按 expert 字段分发给 math/comm/hw/sim（线程池并发）
  4. verify     综合校验     —— verify_agent 核对交叉一致性，给出【通过】/【需修正】
  5. compile    报告统稿     —— report_agent 分段统稿：每位专家各 1 次分节统稿（保留其完整论证）
                                + 1 次全局统稿（摘要/背景/交叉/结论），本地合并；失败降级为机械拼装
  6. report     HTML 报告    —— core/report.generate_research_report() 高审美模板渲染

星型拓扑：各步产物全部经本类内存聚合，Agent 两两之间不直接对话，天然避免消息环；
主干 LLM 调用固定 ≤ 6 次（每对节点 ≤3 轮）；各 Agent 的回答若申请工具，
由 core.tool_driver 额外最多 2 轮本地回环（不新增 Agent 间消息，不破防循环约束）。
"""
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from core.logger import log
from core.report import generate_research_report, restore_latex_ctrl
from core.tool_driver import ask_with_tools
from tools import label as tool_label

# 通用兜底后缀：防网关通道"终答只剩收尾语"（2026-08-27 sim_agent 教训，对所有 LLM 调用生效）
FULL_ANSWER_SUFFIX = (
    "\n\n注意：请把完整回答内容直接写在你本次最终答复的正文中一次性输出，"
    "不要只给摘要，也不要说\"见上方输出\"。"
)

# 子问题 expert 字段 → Agent 注册表键名
EXPERT_AGENTS = {
    "math": "math_agent",
    "comm": "comm_agent",
    "hw":   "hw_agent",
    "sim":  "sim_agent",
}

# 规划者候选顺序（comm 是通信通才，优先做拆解；不可用则逐个回退）
PLANNER_CANDIDATES = ["comm_agent", "math_agent"]

MAX_ANGLES = 5  # 子问题上限，防止 token 爆炸
MIN_ANGLES = 3          # 子问题下限：少于这个数就重新拆解/本地回填
MIN_EXPERT_TYPES = 3    # 至少覆盖几类专家，避免报告只有一两位专家在论证
MAX_CORRECTION_ROUNDS = 2  # 闭环修正最大轮次（验证不通过→修正→重新校验）

# 专家覆盖不足时的本地回填子问题（与各专家职责严格对应，不引入课题外信息）
_EXPERT_BACKFILL = {
    "math": "给出本课题涉及的关键公式推导、适用条件与量级估算（含单位换算）。",
    "comm": "相关 3GPP 规范对本课题涉及的特性是如何规定的？写明规范编号、版本与关键条款。",
    "hw": "本方案的硬件实现（FPGA/ASIC）复杂度、资源开销与时序瓶颈在哪里？",
    "sim": "用蒙特卡洛仿真对上述理论结论做数值验证，并给出与理论曲线的偏差分析。",
}

# ── 统稿预算（2026-09-02 内容量恢复：单次大输入统稿改为"分段统稿"）──
# 旧方案把全部材料塞进一次调用并压到 1200 字/专家 + 输出 ≤1900 字，代价是
# math/comm 的推导与条款论证在报告正文里几乎不剩东西；现改为每次调用只装
# 一位专家的完整论证，单次输入输出都很小，既不再撞平台 180 秒硬超时，
# 又能把字段字数恢复到 prompts/report_system.md 的规定量级。
DIGEST_ANSWER_LIMIT = 6000    # 单专家原文送入分节统稿的字符上限
DIGEST_CONTENT_BUDGET = "600~800 字"  # 分节统稿正文的目标字数
GLOBAL_LIT_LIMIT = 1800       # 全局统稿里文献综述的字符上限
GLOBAL_VERDICT_LIMIT = 900    # 全局统稿里校验意见的字符上限
GLOBAL_PREVIEW_LIMIT = 260    # 全局统稿里每位专家论证摘要的预览字符数
COMPILE_ATTEMPTS = 2          # 每个统稿子任务（分节/全局）的尝试次数
COMPILE_DIGEST_MAX = 5        # 核心发现条目上限

_PLANNER_PROMPT = (
    "你是科研规划专家。请把下面的研究课题拆解成 3~{max_n} 个关键子问题，"
    "并要求：子问题总数不得少于 3 个，且必须覆盖至少 3 类不同的领域专家，"
    "同一类专家最多负责 1 个子问题。\n"
    "每个子问题标注最适合解答的领域专家，expert 只能取: math(信息论/数学推导), "
    "comm(3GPP 协议/标准化/组网), hw(FPGA/硬件实现), sim(蒙特卡洛仿真/数值验证)。\n"
    "拆解时请优先保证四类视角齐备：原理推导、规范依据、硬件落地、数值验证。\n\n"
    "课题：{topic}\n\n"
    "严格按以下 JSON 格式输出，不要有任何其他文字：\n"
    '{{"topic": "<课题名>",\n'
    ' "angles": [{{"question": "<子问题1>", "expert": "comm"}}, '
    '{{"question": "<子问题2>", "expert": "sim"}}, '
    '{{"question": "<子问题3>", "expert": "hw"}}]}}'
)

# 拆解不合格时的补正指令（同一次会话内重问一遍，比直接本地造题质量好）
_PLANNER_RETRY_HINT = (
    "你上一次的拆解不合格：子问题少于 3 个，或全部集中在同一类专家身上。\n"
    "请重新拆解，硬要求：3~{max_n} 个子问题、至少 3 个不同的 expert 取值、"
    "每个 expert 最多出现一次，且必须覆盖原理推导/规范依据/硬件落地/数值验证"
    "中的至少三类。仍按原 JSON 格式输出，不要任何其他文字。"
)


def _report_full_answer_suffix() -> str:
    """report_agent 的"一次性交付完整 JSON"指令：优先用 config.json 里的
    个性化措辞（已针对统稿场景写明"唯一交付物是 JSON"），缺省回退通用后缀。"""
    from core.config import AGENTS
    return AGENTS.get("report_agent", {}).get("requireFullAnswer", FULL_ANSWER_SUFFIX)


class ResearchPipeline:
    """科研任务流水线编排器（星型拓扑中枢）"""

    def __init__(self, orch, agents: dict):
        """
        orch:   core.orchestrator.Orchestrator 实例（复用其消息路由能力）
        agents: 全量 Agent 字典 {"name": AgentNode}
        """
        self.orch = orch
        self.agents = agents
        self.lit = agents.get("lit_review_agent")
        self.steps = []  # 消息协议轨迹：(step, sender, receiver, type, chars)

    # ═══════════════════════════════════════════════════
    #  主入口
    # ═══════════════════════════════════════════════════

    def run(self, topic: str, use_web: bool = True, make_report: bool = True,
            on_progress=None) -> dict:
        """执行完整流水线，返回含各环节产物与报告路径的结果字典。

        Args:
            on_progress: 可选回调 (step_id, step_name, status, detail)
                         step_id: 1-6, status: "start"|"done"|"error"
        """
        t0 = time.time()
        log.info("pipeline.start", topic=topic[:80])

        def _notify(sid, name, status, detail=""):
            if on_progress:
                try:
                    on_progress(sid, name, status, detail)
                except Exception:
                    pass

        # 1. 问题拆解
        _notify(1, "问题拆解", "start")
        plan = self._plan(topic)
        questions = [a["question"] for a in plan["angles"]]
        print(f"\n[1/6] 问题拆解 → {len(questions)} 个子问题（规划者: {plan['planner']}）")
        _notify(1, "问题拆解", "done", f"{len(questions)} 个子问题")

        # 2. 文献调研（lit_agent 缺席时降级为无综述继续）
        _notify(2, "文献调研", "start")
        if self.lit:
            print("[2/6] 文献调研中…（lit_review_agent，公网+平台KB，约 1~2 分钟）")
            try:
                literature = self.lit.survey_with_angles(
                    plan["topic"], questions, use_web=use_web)
                self._record("literature", "lit_review_agent", "orchestrator", "summary", literature)
            except Exception as e:
                log.error("pipeline.literature.failed", error=str(e))
                literature = f"(文献调研失败，已降级继续: {e})"
                print(f"      [WARN] 文献调研失败，降级继续: {e}")
        else:
            literature = "(lit_review_agent 未配置，跳过文献调研)"
            print("[2/6] 跳过文献调研（lit_review_agent 未配置）")
        _notify(2, "文献调研", "done")

        # 3. 并行领域专家
        _notify(3, "并行专家", "start")
        n_experts = sum(1 for a in plan["angles"] if self._resolve_expert(a["expert"]))
        print(f"[3/6] 并行领域专家中…（{n_experts} 个专家并行）")
        experts = self._experts(plan, literature)

        # 3.5 仿真代码自动执行（sim_agent 产出的 Python 代码本地运行，生成图表嵌入报告）
        for e in experts:
            if e.get("expert") == "sim":
                imgs = self._execute_sim_code(e["answer"])
                if imgs:
                    e["images"] = imgs
                    print(f"      仿真执行完成，生成 {len(imgs)} 张图表")

        # 4. 综合校验（含闭环修正）
        _notify(3, "并行专家", "done", f"{len(experts)} 位专家完成")
        _notify(4, "综合校验", "start")
        if "verify_agent" in self.agents and experts:
            print("[4/6] verify_agent 综合校验中…")
            verdict = None
            for attempt in (1, 2):
                try:
                    verdict, experts = self._verify_with_correction(topic, literature, experts)
                    break
                except Exception as e:
                    log.error("pipeline.verify.failed", attempt=attempt, error=str(e))
                    if attempt == 1:
                        print(f"      [WARN] 校验首次失败，3 秒后重试: {str(e)[:60]}")
                        time.sleep(3)
            if verdict is None:
                # 平台侧异常（如 verify_agent 离线）不应中断整条流水线，降级继续出报告
                print("      [WARN] 综合校验失败，降级继续")
                verdict = "(综合校验被跳过：平台侧校验环节暂时不可用)"
        else:
            verdict = "(verify_agent 未配置或无专家产出，跳过校验)"
            print("[4/6] 跳过综合校验")
        _notify(4, "综合校验", "done")

        elapsed = time.time() - t0

        # 5. 报告统稿（report_agent 缺席/失败时静默降级，报告必出；网络异常重试一次）
        _notify(5, "报告统稿", "start")
        draft = None
        if "report_agent" in self.agents:
            print("[5/6] report_agent 分段统稿中…（每位专家 1 次分节 + 1 次全局）")
            last_err = ""
            for attempt in (1, 2, 3):
                try:
                    draft = self._compile_report(plan, literature, experts, verdict)
                    if draft:
                        break
                    last_err = "统稿返回空结果"
                    log.warning("pipeline.compile.empty", attempt=attempt)
                except Exception as e:
                    last_err = str(e)
                    log.error("pipeline.compile.failed", attempt=attempt, error=last_err)
                if attempt < 3:
                    print(f"      [WARN] 统稿第 {attempt} 次未成功，3 秒后重试: {last_err[:60]}")
                    time.sleep(3)
            if draft:
                findings = draft.get("findings") or []
                avg = sum(len(f.get("content", "")) for f in findings) // len(findings) if findings else 0
                print(f"      统稿完成：核心发现 {len(findings)} 节（平均 {avg} 字/节）、"
                      f"摘要 {len(draft.get('summary', ''))} 字")
                _notify(5, "报告统稿", "done", f"{len(findings)} 节")
            else:
                draft = self._fallback_draft(plan, literature, experts, verdict)
                print("      [WARN] 报告统稿降级为本地机械拼装")
                _notify(5, "报告统稿", "done", "降级")
        else:
            print("[5/6] 跳过报告统稿（report_agent 未配置），本地机械拼装")
            draft = self._fallback_draft(plan, literature, experts, verdict)
            _notify(5, "报告统稿", "done", "降级")

        # 6. HTML 报告（高审美模板渲染）
        _notify(6, "报告渲染", "start")
        report_path = ""
        if make_report:
            try:
                report_path = generate_research_report(
                    topic=plan["topic"],
                    plan=plan,
                    literature=literature,
                    experts=experts,
                    verdict=verdict,
                    total_time=f"{elapsed:.0f}",
                    draft=draft,
                    steps=list(self.steps),
                )
                print(f"[6/6] 报告已生成: {report_path}")
                _notify(6, "报告渲染", "done", report_path)
            except Exception as e:
                log.error("pipeline.report.failed", error=str(e))
                print(f"[6/6] [WARN] 报告生成失败: {e}")
                _notify(6, "报告渲染", "error", str(e))
        else:
            _notify(6, "报告渲染", "done", "跳过")

        result = {
            "topic": plan["topic"],
            "plan": plan,
            "literature": literature,
            "experts": experts,
            "verdict": verdict,
            "draft": draft,
            "report_path": report_path,
            "elapsed": round(elapsed, 1),
            "steps": list(self.steps),
        }
        log.info("pipeline.done", topic=topic[:80], elapsed=result["elapsed"],
                 experts=len(experts), passed=("通过" in verdict))
        return result

    # ═══════════════════════════════════════════════════
    #  各阶段实现
    # ═══════════════════════════════════════════════════

    def _plan(self, topic: str) -> dict:
        """步骤1：规划者 Agent 拆解课题。

        两道质量门：① 拆解结果必须 ≥MIN_ANGLES 题且覆盖 ≥MIN_EXPERT_TYPES 类专家，
        不合规则带补正指令重问一次（并换下一个候选规划者）；② 仍不合规则按缺失
        视角本地回填模板子问题，保证报告至少有三类专家在论证。
        （2026-09-02 实测教训：旧提示词只写“≤5 个”，规划者常常只拆 2 题且全给
        math/sim，导致七智能体系统实际只有两个人在论证。）
        """
        candidates = [n for n in PLANNER_CANDIDATES if n in self.agents]
        prompt_base = _PLANNER_PROMPT.format(max_n=MAX_ANGLES, topic=topic) \
                      + FULL_ANSWER_SUFFIX
        retry_prompt = (prompt_base + "\n\n" + _PLANNER_RETRY_HINT.format(max_n=MAX_ANGLES))

        angles: list = []
        planner_name = candidates[0] if candidates else "(none)"
        for cand in candidates:
            for attempt, prompt in ((1, prompt_base), (2, retry_prompt)):
                try:
                    raw = self.agents[cand].think(prompt)
                except Exception as e:
                    log.error("pipeline.plan.failed", planner=cand, error=str(e))
                    raw = ""
                parsed = self._parse_angles(raw, topic)
                if len(parsed) > len(angles):
                    angles = parsed
                if self._coverage_ok(angles):
                    planner_name = cand
                    break
                log.warning("pipeline.plan.weak_coverage", planner=cand, attempt=attempt,
                            angles=len(parsed), types=len({a["expert"] for a in parsed}))
            if self._coverage_ok(angles):
                break

        angles = self._diversify(angles)
        if not angles:
            angles = self._diversify([{"question": topic, "expert": "comm"}])
        for a in angles:
            self._record("plan", planner_name, "orchestrator", f"angle@{a['expert']}", a["question"])
        types = sorted({a["expert"] for a in angles})
        print(f"      拆解得到 {len(angles)} 个子问题，覆盖专家：{'、'.join(types)}"
              + ("" if planner_name != "(none)" else "（规划者不可用，本地回填）"))
        return {"topic": topic, "angles": angles, "planner": planner_name}

    @staticmethod
    def _coverage_ok(angles: list) -> bool:
        """拆解质量门：题数与专家类型数都达标记为合格。"""
        return (len(angles) >= MIN_ANGLES
                and len({a["expert"] for a in angles}) >= MIN_EXPERT_TYPES)

    @staticmethod
    def _diversify(angles: list) -> list:
        """按缺失视角本地回填子问题：题数未满则追加，已满则顶掉一个重复专家的多余题。"""
        out = list(angles)[:MAX_ANGLES]
        have = {a["expert"] for a in out}
        for key in ("math", "comm", "hw", "sim"):
            if key in have:
                continue
            if len(out) < MAX_ANGLES and (len(out) < MIN_ANGLES
                                          or len(have) < MIN_EXPERT_TYPES):
                out.append({"question": _EXPERT_BACKFILL[key], "expert": key})
                have.add(key)
                log.info("pipeline.plan.backfill", expert=key)
                continue
            if len(have) >= MIN_EXPERT_TYPES:
                break
            seen = set()          # 题数已满：找一位领了两题的专家，把第二题换成本次缺失视角
            for i in range(len(out) - 1, -1, -1):
                e = out[i]["expert"]
                if e in seen and e != key:
                    out[i] = {"question": _EXPERT_BACKFILL[key], "expert": key}
                    have.add(key)
                    log.info("pipeline.plan.replace", expert=key, dropped=e)
                    break
                seen.add(e)
        return out

    @staticmethod
    def _parse_angles(text: str, topic: str) -> list:
        """从容错解析规划者输出的 JSON（容忍 ```json 围栏与前后杂文）。"""
        data = None
        fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text or "", re.S)
        for candidate in ([fence.group(1)] if fence else []) + (
                [re.search(r"\{.*\}", text or "", re.S).group(0)]
                if re.search(r"\{.*\}", text or "", re.S) else []):
            try:
                data = json.loads(candidate)
                break
            except (json.JSONDecodeError, ValueError):
                continue
        data = ResearchPipeline._undo_json_escapes(data)

        clean = []
        if isinstance(data, dict):
            for a in (data.get("angles") or [])[:MAX_ANGLES]:
                if not (isinstance(a, dict) and str(a.get("question", "")).strip()):
                    continue
                exp = str(a.get("expert", "comm")).strip().lower()
                clean.append({"question": str(a["question"]).strip(),
                              "expert": exp if exp in EXPERT_AGENTS else "comm"})
        if not clean:  # 兜底：整题交给 comm
            clean = [{"question": topic, "expert": "comm"}]
        return clean

    def _resolve_expert(self, expert_key: str) -> str | None:
        """expert 标签 → 可用 Agent 名；目标缺席时回退到任意可用专家。"""
        name = EXPERT_AGENTS.get(expert_key, "comm_agent")
        if name in self.agents:
            return name
        return next((n for n in ("comm_agent", "math_agent", "sim_agent", "hw_agent")
                     if n in self.agents), None)

    def _experts(self, plan: dict, literature: str) -> list:
        """步骤3：并行咨询领域专家。同一 Agent 至多领 1 题（避免并发 session 竞态），
        多余子问题合并进该 Agent 的提问文本。"""
        assignments = {}   # agent_name -> {"main": question, "extra": [...]}
        seen_questions = set()
        for a in plan["angles"]:
            name = self._resolve_expert(a["expert"])
            if not name:
                continue
            q = a["question"]
            if q in seen_questions:
                continue
            seen_questions.add(q)
            slot = assignments.setdefault(name, {"main": q, "extra": []})
            if slot["main"] != q:
                slot["extra"].append(q)

        def work(agent_name: str, main_q: str, extra_qs: list) -> dict:
            extra_txt = ("\n补充子问题（一并简要回答）：\n  - "
                         + "\n  - ".join(extra_qs)) if extra_qs else ""
            tools_used = []      # 本地工具轨迹（预跑 + Agent 自主申请），报告里作为证据展示
            # 预跑上下文：课题 + 子问题，驱动器据此本地真跑 comm_lib / protocol_lookup，
            # 把真实数值压进提示词（仅靠模型自愿申请工具实测为 0 次，回答会退化成纯文本）
            pre_ctx = f"{plan['topic']} {main_q} {' '.join(extra_qs)}"

            def _ask(p):
                return ask_with_tools(
                    self.agents[agent_name], p,
                    on_event=lambda r, c, b: tools_used.extend(x["name"] for x in c),
                    preflight_ctx=pre_ctx)

            # sim_agent 任务规划器无法处理含文献综述的复合提示词（已知 pitfall），
            # 改用精简提示词：仅给课题+子问题，不注入完整文献综述
            if agent_name == "sim_agent":
                from core.config import AGENTS as _AGENTS
                sim_suffix = _AGENTS.get("sim_agent", {}).get(
                    "requireFullAnswer", FULL_ANSWER_SUFFIX)
                prompt = (
                    f"研究课题：{plan['topic']}\n"
                    f"你负责的子问题：{main_q}{extra_txt}\n\n"
                    f"要求：给出完整的仿真方案、可运行 Python 代码、理论对照与运行说明。"
                ) + sim_suffix
                log.info("pipeline.expert.start", agent=agent_name, question=main_q[:60])
                # 三级候选提示词：完整版 → 去补充子问题 → 极简（只有子问题本身）
                attempts = [prompt]
                if extra_qs:
                    attempts.append((
                        f"研究课题：{plan['topic']}\n"
                        f"你负责的子问题：{main_q}\n\n"
                        f"要求：给出完整的仿真方案、可运行 Python 代码、理论对照与运行说明。"
                    ) + sim_suffix)
                attempts.append(
                    f"{main_q}。请给出完整的仿真方案、可运行 Python 代码、理论对照与运行说明。"
                )
                answer, last_err = None, None
                for lvl, p in enumerate(attempts):
                    try:
                        answer = _ask(p)
                        break
                    except Exception as err:
                        last_err = err
                        log.warning("pipeline.expert.sim_fallback",
                                    agent=agent_name, level=lvl + 1,
                                    error=str(err)[:120])
                        if lvl + 1 < len(attempts):
                            print(f"      [INFO] sim_agent 降级重试（第 {lvl + 1} 轮，精简提示词）")
                if answer is None:
                    raise last_err
            else:
                prompt = (
                    f"你作为领域专家，请结合以下调研资料回答子问题，给出有依据的专业结论。\n\n"
                    f"{literature}\n\n"
                    f"研究课题：{plan['topic']}\n"
                    f"你负责的子问题：{main_q}{extra_txt}\n\n"
                    f"要求：结论先行、论据标注来源；如资料不足请明确指出缺口。"
                ) + FULL_ANSWER_SUFFIX
                log.info("pipeline.expert.start", agent=agent_name, question=main_q[:60])
                answer = _ask(prompt)
            self._record("experts", "orchestrator", agent_name, "sub_question", main_q)
            self._record("experts", agent_name, "orchestrator", "answer", answer)
            return {"question": main_q, "extra": extra_qs,
                    "expert": agent_name.replace("_agent", ""), "agent": agent_name,
                    "answer": answer,
                    "tools_used": [tool_label(n) for n in dict.fromkeys(tools_used)]}

        results, failed = [], []
        # 并发度 2：降低同时打开的网关 SSE 连接，避免触发网关限流（WinError 10054/10051）
        with ThreadPoolExecutor(max_workers=min(len(assignments), 2) or 1) as pool:
            futures = {pool.submit(work, n, s["main"], s["extra"]): n
                       for n, s in assignments.items()}
            for fut in as_completed(futures):
                try:
                    results.append(fut.result())
                except Exception as e:
                    failed.append((futures[fut], str(e)))
                    log.error("pipeline.expert.failed", agent=futures[fut], error=str(e))

        for name, err in failed:
            print(f"      [WARN] 专家 {name} 失败: {err[:120]}")
        print(f"      完成 {len(results)}/{len(assignments)} 位专家"
              + (f"，失败 {len(failed)} 位" if failed else ""))
        return results

    def _verify(self, topic: str, literature: str, experts: list) -> str:
        """步骤4：verify_agent 汇总交叉校验，输出【通过】/【有条件通过】/【不通过】开头的意见。
        输入截断防 token 超量（2026-09-02 校验环节同统稿一样撞平台规划超时）。"""
        blocks = []
        if literature and not literature.startswith("("):
            blocks.append(f"【文献综述】\n{literature[:1000]}")
        for i, e in enumerate(experts, 1):
            extra = "".join(f"\n补充问题：{q}" for q in e.get("extra") or [])
            blocks.append(f"【专家回答{i} · {e['expert']}】\n问：{e['question']}{extra}\n答：{(e.get('answer') or '')[:1500]}")

        prompt = (
            f"以下是一份关于「{topic}」的多智能体协作产出材料，请你做综合交叉校验：\n"
            "1) 各结论之间是否矛盾；\n"
            "2) 是否有明显的事实、公式或标准条款错误；\n"
            "3) 引用来源是否可信、编号是否一致；\n"
            "4) 指出尚存的缺口与建议的后续验证手段。\n"
            "最终校验意见必须以【通过】【有条件通过】或【不通过】开头。\n"
            "请严格按三级评级判断：\n"
            "- 【通过】：核心结论正确，无原理性错误（轻微瑕疵可附带提示）\n"
            "- 【有条件通过】：存在中等问题，不影响核心结论但应修正\n"
            "- 【不通过】：存在原理性错误或严重事实错误\n\n"
            + "\n\n".join(blocks)
        ) + FULL_ANSWER_SUFFIX

        # 预跑上下文：课题 + 各子问题，让校验者手里先拿到标准算法库的真实数值，
        # 不至于只能“读着专家的文本对文本”
        pre_ctx = topic + " " + " ".join(e.get("question", "") for e in experts)
        verdict = ask_with_tools(self.agents["verify_agent"], prompt,
                                 preflight_ctx=pre_ctx)
        self._record("verify", "verify_agent", "orchestrator", "verdict", verdict)
        return verdict

    def _verify_with_correction(self, topic: str, literature: str, experts: list) -> tuple:
        """综合校验 + 闭环修正：验证不通过时自动修正，最多 MAX_CORRECTION_ROUNDS 轮。

        Returns:
            (verdict, experts)  最终校验意见与（可能已修正的）专家产出
        """
        verdict = self._verify(topic, literature, experts)

        for round_num in range(1, MAX_CORRECTION_ROUNDS + 1):
            # 判断是否需要修正：只有【不通过】才触发修正，【有条件通过】视为通过
            if "【不通过】" not in verdict:
                if round_num == 1:
                    print(f"      校验结论：{'通过' if '【通过】' in verdict else '有条件通过'}")
                break

            print(f"      [修正轮次 {round_num}/{MAX_CORRECTION_ROUNDS}] 验证不通过，自动修正中…")
            log.info("pipeline.correction.start", round=round_num)

            # 逐个专家修正：将验证反馈发回给对应专家
            for idx, expert in enumerate(experts):
                agent_name = expert.get("agent", f"{expert['expert']}_agent")
                if agent_name not in self.agents:
                    continue

                correction_tools = []

                def _ask_fix(p):
                    return ask_with_tools(
                        self.agents[agent_name], p,
                        on_event=lambda r, c, b: correction_tools.extend(
                            x["name"] for x in c),
                        preflight_ctx=f"{topic} {expert['question']}")

                correction_prompt = (
                    f"你之前回答的子问题存在以下校验意见，请根据反馈修正后重新给出完整回答。\n\n"
                    f"研究课题：{topic}\n"
                    f"你的子问题：{expert['question']}\n\n"
                    f"你的原回答：\n{expert['answer']}\n\n"
                    f"verify_agent 的校验意见：\n{verdict}\n\n"
                    f"请修正上述问题后重新给出完整回答，不需要重复未出错的部分。"
                ) + FULL_ANSWER_SUFFIX

                try:
                    corrected_answer = _ask_fix(correction_prompt)
                    if corrected_answer and corrected_answer.strip():
                        experts[idx]["answer"] = corrected_answer
                        if correction_tools:
                            experts[idx]["tools_used"] = list(dict.fromkeys(
                                (experts[idx].get("tools_used") or [])
                                + [tool_label(n) for n in correction_tools]))
                        self._record(
                            "correction", agent_name, "orchestrator",
                            f"corrected_r{round_num}", corrected_answer
                        )
                        log.info("pipeline.correction.done",
                                 agent=agent_name, round=round_num)
                except Exception as e:
                    log.error("pipeline.correction.failed",
                              agent=agent_name, round=round_num, error=str(e))
                    print(f"      [WARN] {agent_name} 修正失败: {e}")

            # 重新校验
            print(f"      重新校验中…")
            verdict = self._verify(topic, literature, experts)
            log.info("pipeline.correction.reverify", round=round_num,
                     passed="不通过" not in verdict)

            if "【不通过】" not in verdict:
                conclusion = "通过" if "【通过】" in verdict else "有条件通过"
                print(f"      修正轮次 {round_num} 完成，校验结论：{conclusion}")
                break

        return verdict, experts

    @staticmethod
    def _execute_sim_code(answer: str) -> list:
        """从 sim_agent 回答中提取 Python 代码，本地执行并收集生成的 PNG 图片。

        提取与执行逻辑已收敛到工具层（tools/sim_tools），与 run_python 工具
        共用同一套安全执行实现。Returns: base64 图片列表，失败返回空列表。
        """
        from tools.sim_tools import extract_python_code, execute_python_code

        code_blocks = extract_python_code(answer)
        if not code_blocks:
            log.warning("pipeline.sim.no_code", msg="未从 sim_agent 回答中找到 Python 代码")
            return []

        out = execute_python_code("\n\n".join(code_blocks), timeout=120)
        if not out["ok"]:
            log.error("pipeline.sim.exec_failed", stderr=out["stderr"][:500])
            print(f"      [WARN] 仿真代码执行失败: {out['stderr'][:200]}")
            return []
        if out["stdout"]:
            log.info("pipeline.sim.stdout", output=out["stdout"][:300])
        return out["images"]

    def _record(self, step: str, sender: str, receiver: str, msg_type: str, content: str):
        """星型拓扑消息轨迹（内存聚合 + 总线留档），替代点对点直接对话。"""
        self.steps.append({
            "task_id": id(self),
            "step": step, "from": sender, "to": receiver,
            "type": msg_type, "chars": len(content),
            "reply_ref": f"{sender}->{receiver}",
        })

    # ══════════════════════════════════════════════════
    #  报告统稿（步骤5：report_agent）
    # ══════════════════════════════════════════════════

    def _compile_report(self, plan: dict, literature: str,
                        experts: list, verdict: str) -> dict | None:
        """分段统稿：每位专家各 1 次分节统稿（输入为其完整论证原文）+ 1 次全局统稿，
        本地合并为结构化 draft。平台完全不可用时返回 None，由调用方机械拼装兜底。"""
        digests = self._compile_digests(plan, experts)
        glob = self._compile_global(plan, literature, experts, verdict, digests)
        if glob is None and all(d.get("degraded") for d in digests):
            return None      # 分节与全局都没走通平台 → 整篇交给本地兜底
        return self._merge_draft(glob, digests, plan, literature, experts, verdict)

    # ── 分节统稿：一位专家一次调用 ────────────────────

    def _compile_digests(self, plan: dict, experts: list) -> list:
        """对每位专家并发做一次分节统稿（结果与 experts 同序对齐）。
        单节失败退化为原文直录，绝不为平台限制而丢掉专家论证内容。"""
        results: list = [None] * len(experts)

        def work(idx: int) -> dict:
            e = experts[idx]
            for attempt in range(1, COMPILE_ATTEMPTS + 1):
                content = ""
                try:
                    raw = ask_with_tools(self.agents["report_agent"],
                                         self._build_digest_prompt(plan, e))
                    self._record("compile", "report_agent", "orchestrator",
                                 f"digest@{e['expert']}", raw or "")
                    parsed = self._parse_draft(raw, require_field="findings")
                    if parsed and parsed.get("findings"):
                        f = parsed["findings"][0]
                        content = str(f.get("content", "")).strip()
                        if len(content) >= 150:
                            return {
                                "title": str(f.get("title", "")).strip()
                                         or self._short_title(e["question"]),
                                "expert": e["expert"], "content": content,
                            }
                    log.warning("pipeline.compile.digest_weak",
                                agent=e["agent"], attempt=attempt, chars=len(content))
                except Exception as err:
                    log.warning("pipeline.compile.digest_failed", agent=e["agent"],
                                attempt=attempt, error=str(err)[:120])
            return self._digest_fallback(e)

        with ThreadPoolExecutor(max_workers=min(len(experts), 2) or 1) as pool:
            futures = {pool.submit(work, i): i for i in range(len(experts))}
            for fut in as_completed(futures):
                i = futures[fut]
                try:
                    results[i] = fut.result()
                except Exception as err:      # work() 内部已兜底，此处仅为保险
                    log.error("pipeline.compile.digest_crash", index=i, error=str(err)[:120])
                    results[i] = self._digest_fallback(experts[i])
        n_fb = sum(1 for d in results if d and d.get("degraded"))
        if n_fb:
            print(f"      [INFO] {n_fb} 节统稿未走通平台，已按专家原文直录保留")
        return results

    @staticmethod
    def _short_title(question: str, n: int = 18) -> str:
        """从子问题提短标题（分节统稿未给 title 时的回填）。"""
        s = re.sub(r"\s+", "", str(question or "")).strip("？?。；，")
        return (s[:n] + "……") if len(s) > n else (s or "专家论证")

    @classmethod
    def _digest_fallback(cls, expert: dict) -> dict:
        """分节统稿失败时的保内容兜底：直接录专家原文（去空行、上限 2500 字）。"""
        raw = re.sub(r"\n{3,}", "\n\n", (expert.get("answer") or "").strip())
        content = raw[:2500] + ("\n\n……（原文较长，完整论证见本章末尾展开区）"
                                if len(raw) > 2500 else "")
        return {"title": cls._short_title(expert.get("question", "")),
                "expert": expert.get("expert", ""),
                "content": content or "（该专家未产出有效论证）",
                "degraded": True}

    @staticmethod
    def _build_digest_prompt(plan: dict, expert: dict) -> str:
        """分节统稿提示词：只送一位专家的完整论证，只回填 findings 一个字段
        （沿用 report_agent 的输出协议，避免自定义格式被在线角色手册拒收）。"""
        answer = (expert.get("answer") or "").strip()
        extra = "".join(f"\n补充子问题：{q}" for q in expert.get("extra") or [])
        return (
            "【分节统稿子任务】本次只统稿下面这一位专家的材料，不要总览全文。\n"
            f"研究课题：{plan.get('topic', '')}\n"
            f"来源专家：{expert['expert']}_agent\n"
            f"该专家的子问题：{expert['question']}{extra}\n"
            f"该专家论证原文（共 {len(answer)} 字，超长已截断）：\n"
            + answer[:DIGEST_ANSWER_LIMIT]
            + "\n\n输出要求：仍按你的输出协议给出单个 JSON 对象，但本次只填 findings——"
              "findings 输出且仅输出 1 条：title 为该发现短标题（15 字以内），"
              f"expert 固定填 {expert['expert']}，content 由该专家论证整理成报告正文段"
              f"（{DIGEST_CONTENT_BUDGET}）：必须保留原文里全部关键公式（LaTeX 记法）、"
              "关键数值、规范与文献编号、分步推导要点与结论，删去口语与重复表述，"
              "禁止引入材料以外的信息，禁止写“见上文”“如上”这类指代。"
              "summary、background、cross_analysis、conclusion、outlook 一律输出空字符串，"
              "keywords 输出空数组。"
        ) + _report_full_answer_suffix()

    # ── 全局统稿：只出摘要/背景/交叉/结论/展望/关键词 ────

    def _compile_global(self, plan: dict, literature: str, experts: list,
                        verdict: str, digests: list) -> dict | None:
        """全局章节统稿（输入为各专家的分节摘要而非原文，单次体量很小）。"""
        prompt = self._build_global_prompt(plan, literature, experts, verdict, digests)
        for attempt in range(1, COMPILE_ATTEMPTS + 1):
            try:
                raw = ask_with_tools(self.agents["report_agent"], prompt)
                self._record("compile", "report_agent", "orchestrator",
                             "global", raw or "")
                parsed = self._parse_draft(raw)
                if parsed and parsed.get("summary"):
                    return parsed
                log.warning("pipeline.compile.global_weak", attempt=attempt)
            except Exception as err:
                log.warning("pipeline.compile.global_failed",
                            attempt=attempt, error=str(err)[:120])
        return None

    @staticmethod
    def _build_global_prompt(plan: dict, literature: str, experts: list,
                             verdict: str, digests: list) -> str:
        """全局统稿输入：任务拆解表 + 综述节选 + 各专家论证要点预览 + 校验意见。"""
        parts = [f"研究课题：{plan.get('topic', '')}", "\n【任务拆解表】"]
        for i, a in enumerate(plan.get("angles", []), 1):
            parts.append(f"{i}. {a['question']}（负责专家：{a['expert']}）")
        parts.append("\n【文献综述】\n"
                     + (literature[:GLOBAL_LIT_LIMIT] if literature and not literature.startswith("(")
                        else "(文献调研未产出有效材料)"))
        parts.append("\n【各专家论证要点（完整正文已由分节统稿写入核心发现，此处仅供写交叉分析参照）】")
        for i, e in enumerate(experts, 1):
            dg = digests[i - 1] if i - 1 < len(digests) and digests[i - 1] else {}
            preview = (dg.get("content") or e.get("answer") or "")[:GLOBAL_PREVIEW_LIMIT]
            parts.append(f"- 专家{i} {e['expert']}_agent｜问：{e['question']}\n  论证要点：{preview}")
        parts.append("\n【综合校验意见（verify_agent）】\n" + (verdict or "(无)")[:GLOBAL_VERDICT_LIMIT])
        return (
            "【全局统稿子任务】本次只统稿报告的总体章节，findings 输出空数组"
            "（各专家的分节正文已由前序分节统稿完成，不要在此重复）。\n"
            "请按你的输出协议给出单个 JSON 对象，各字段一律按手册规定的满额字数写："
            "summary 300 字、background 400 字（保留关键文献标注与规范编号）、"
            "cross_analysis 400 字（逐条指出各专家结论是否互相印证、理论值与仿真值是否一致、"
            "存在哪些张力与缺口）、conclusion 300 字（必须以 verify_agent 的三级评级开头、"
            "忠实转述评级与理由）、outlook 200 字、keywords 3~6 个。\n\n" + "\n".join(parts)
        ) + _report_full_answer_suffix()

    def _merge_draft(self, glob: dict | None, digests: list, plan: dict,
                     literature: str, experts: list, verdict: str) -> dict | None:
        """合并分节与全局两部分：全局字段缺失时仅对该字段走本地拼装补齐。"""
        glob = dict(glob or {})
        if not (glob.get("summary") and glob.get("conclusion")):
            local = self._fallback_draft(plan, literature, experts, verdict)
            for k in ("summary", "background", "cross_analysis",
                      "conclusion", "outlook", "keywords"):
                if not str(glob.get(k, "")).strip():
                    glob[k] = local[k]
        findings = [d for d in digests if d and d.get("content")][:COMPILE_DIGEST_MAX]
        draft = {
            "summary": str(glob.get("summary", "")).strip(),
            "background": str(glob.get("background", "")).strip(),
            "findings": findings,
            "cross_analysis": str(glob.get("cross_analysis", "")).strip(),
            "conclusion": str(glob.get("conclusion", "")).strip(),
            "outlook": str(glob.get("outlook", "")).strip(),
            "keywords": [str(k).strip() for k in (glob.get("keywords") or [])
                         if str(k).strip()][:8],
        }
        if not (draft["summary"] or draft["findings"]):
            return None
        log.info("pipeline.compile.done", summary_len=len(draft["summary"]),
                 findings=len(draft["findings"]),
                 digest_chars=sum(len(d["content"]) for d in draft["findings"]))
        return draft

    @staticmethod
    def _parse_draft(raw: str, require_field: str = "summary") -> dict | None:
        """容错解析 report_agent 的结构化输出：容忍围栏、前后杂文与单引号。
        require_field 指定本次必须非空的字段（分节统稿传 findings，全局统稿传 summary）。"""
        if not raw or not raw.strip():
            return None
        text = raw.strip()
        fence = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.S)
        candidates = ([fence.group(1)] if fence else []) + [
            m.group(0) for m in [re.search(r"\{.*\}", text, re.S)] if m]
        data = None
        for c in candidates:
            for variant in (c, ResearchPipeline._fix_escapes(c), c.replace("'", '"')):
                try:
                    data = json.loads(variant)
                    break
                except (json.JSONDecodeError, ValueError):
                    continue
            if data:
                break
        if data is None and "{" in text:
            # 截断修复：网关流被平台超时掐断时，从尾部补齐闭合符号抢救已生成字段
            data = ResearchPipeline._repair_truncated(text[text.index("{"):])
            if data:
                log.warning("pipeline.compile.truncated_repaired",
                            fields=len(data))
        if not isinstance(data, dict):
            return None
        data = ResearchPipeline._undo_json_escapes(data)
        need = data.get(require_field)
        if not ((need if isinstance(need, list) else str(need or "").strip())):
            return None
        findings = [f for f in (data.get("findings") or [])
                    if isinstance(f, dict) and str(f.get("content", "")).strip()][:5]
        return {
            "summary": str(data.get("summary", "")).strip(),
            "background": str(data.get("background", "")).strip(),
            "findings": findings,
            "cross_analysis": str(data.get("cross_analysis", "")).strip(),
            "conclusion": str(data.get("conclusion", "")).strip(),
            "outlook": str(data.get("outlook", "")).strip(),
            "keywords": [str(k).strip() for k in (data.get("keywords") or [])
                         if str(k).strip()][:6],
        }

    @staticmethod
    def _undo_json_escapes(obj):
        r"""递归还原 json.loads 之后的“被吃转义”：LaTeX 命令首字母（b/f/n/r/t）
        撞上 JSON 合法转义集，\text 会变成 制表符+ext，公式在页面上露出源码。
        统稿正文、子问题文本全部走一道，下游的字数统计与渲染看到的才是真文本。"""
        if isinstance(obj, str):
            return restore_latex_ctrl(obj)
        if isinstance(obj, list):
            return [ResearchPipeline._undo_json_escapes(x) for x in obj]
        if isinstance(obj, dict):
            return {k: ResearchPipeline._undo_json_escapes(v) for k, v in obj.items()}
        return obj

    @staticmethod
    def _fix_escapes(t: str) -> str:
        """修复模型在 JSON 字符串内直写的非法转义（典型：LaTeX 的 \\sqrt/\\frac），
        把不在 JSON 合法转义集内的反斜杠双写。\\u 后面不是四位十六进制时
        （如 \\underline）也必须双写，否则整个 JSON 直接解析失败。"""
        t = re.sub(r'\\u(?![0-9a-fA-F]{4})', r'\\\\u', t)
        return re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', t)

    @staticmethod
    def _repair_truncated(t: str):
        """对尾部被截断的 JSON 文本，逐个回退到最后一个完整字符串边界，
        尝试补齐常见闭合符，能解析则返回。全部失败返回 None。"""
        tails = ("}", "}]", "}}", "]}}", "}}]", "\"]}")
        i = t.rfind('",')
        while i > 0:
            head = t[:i + 1]
            for tail in tails:
                try:
                    d = json.loads(head + tail)
                    if isinstance(d, dict):
                        return d
                except (json.JSONDecodeError, ValueError):
                    continue
            i = t.rfind('",', 0, i)
        return None

    @staticmethod
    def _fallback_draft(plan: dict, literature: str,
                        experts: list, verdict: str) -> dict:
        """平台统稿不可用时的本地机械拼装：直接由各环节材料
        提炼出结构化报告字段，保证靛蓝瓷报告必有统稿章节。
        不压缩专家正文（clip 保留换行），降级也不丢内容。"""
        topic = str(plan.get("topic", "")).strip()
        n_q = len(plan.get("angles", []))
        names = "、".join(sorted({e["expert"] for e in experts})) or "各"

        def head(s: str, n: int) -> str:
            """单行提炼（用于摘要类字段）。"""
            s = re.sub(r"\s+", " ", (s or "").strip())
            return s[:n] + ("……" if len(s) > n else "")

        def clip(s: str, n: int) -> str:
            """保留换行与 Markdown 结构的截断（用于正文类字段）。"""
            s = re.sub(r"\n{3,}", "\n\n", (s or "").strip())
            return s[:n] + ("\n\n……（完文见附录）" if len(s) > n else "")

        findings = [{
            "title": ResearchPipeline._short_title(e.get("question", "")),
            "expert": e.get("expert", ""),
            "content": clip(e.get("answer", ""), 1200),
            "degraded": True,
        } for e in experts[:COMPILE_DIGEST_MAX]]
        return {
            "summary": (f"本报告围绕「{topic}」拆解出 {n_q} 个子问题，"
                        f"由 {names} 等领域专家并行论证"
                        + (f"，综合校验意见：{head(verdict, 120)}" if verdict else "。")
                        + "核心结论详见各章节。"),
            "background": clip(literature, 500) or f"围绕「{topic}」的研究背景材料暂缺。",
            "findings": findings,
            "cross_analysis": (clip(verdict, 500)
                               if verdict else "平台校验环节未产出意见，交叉印证暂缺。"),
            "conclusion": head(verdict, 350) or "各环节材料已齐备，结论以专家论证为准。",
            "outlook": "后续可在更复杂信道模型、更大样本量与真实测量数据上扩展验证。",
            "keywords": [w for w in re.split(r"[\s，,、与在下的及]+", topic) if w][:6],
            "degraded": True,
        }
