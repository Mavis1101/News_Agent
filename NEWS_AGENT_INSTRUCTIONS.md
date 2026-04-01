# News Agent · 情报简报 — Project Instructions

## 项目概述

这是一个新闻情报 Agent，每日抓取高科技、地缘政治、宏观经济三个领域的重要新闻，生成英文为主、中英双语的情报简报，通过邮件推送。

**双轨目标：**
- **个人使用**：`news_agent_v3_5.html` 单文件，浏览器直接打开运行
- **MVP 商业验证**：低成本多用户版本，向少量用户推送同一份简报，验证产品需求，收集反馈

---

## 当前版本功能（v3 / Phase 2）

### 内容与来源
- **来源分级 T1/T2/T3a/T3b/T4**，优先级强制执行：
  - T1：政府官方声明、白宫/国务院/议会、央行（美联储/人民银行/欧央行/加拿大央行）、监管机构、军方官方声明
  - T2：大公司官方 IR 页面、财报、官方新闻稿（Apple Newsroom、NVIDIA IR、华为官网等）、交易所公告（SEC/HKEX/SSE）
  - T3a（可信电讯）：Reuters、Bloomberg、Xinhua（新华社）、Nikkei（日经）— 数字和事实可进 5W，confidence 可为 HIGH
  - T3b（谨慎）：WSJ、FT、SCMP — 数字必须移至 analysis，文字进 5W 前须剔除编辑性判断，confidence 上限 MED
  - T4：其他媒体/博客/观点类/智库报告（The Economist、Brookings、RAND、TechCrunch、Axios 等）— confidence 上限 MED；例外：研究机构的原创调查/测量数据可进 5W，其预测/结论属于分析
- 同一事件若存在 T1/T2 来源，忽略 T3b/T4
- sourceUrl 必须是原始官方 URL，不得是聚合器链接

### 输出格式
- **英文为主语言**：大标题英文（EB Garamond 衬线体），中文作为副标题（Noto Serif SC）
- **每条新闻包含**：
  - 来源层级徽章（T1/T2/T3a/T3b/T4）+ 官方来源标记
  - 新闻发布日期（YYYY-MM-DD），估算日期附 `est.` 标记
  - 5W 堆叠布局（**英文块在上，中文块在下**，中间分隔线）：WHO/何人、WHAT/何事、WHEN/何时、WHERE/何地、CONTEXT/背景（原 WHY）
  - 三维度推理分析（明确标注为 [Analysis]/[分析]，非确认事实）：
    - Investment · 投资信号
    - Geopolitics · 地缘政治
    - Career · 职场/AI转行
  - Confidence 置信度标签：HIGH（绿）/ MED（金）/ LOW（灰）

### 去重机制
- 已推送的新闻存入 `dedup_history.json`（Phase 2 服务端）或 localStorage（个人版）
- **去重窗口：7 天滚动**（仅保留最近 7 天内发送的条目，按日期过滤，非计数）
- 例外：`isMajorUpdate: true` 的条目（重大新进展）绕过去重，显示 "Major update" 徽章
- 个人版侧边栏可点击 "Clear history & prefs" 重置 localStorage 去重记录

### 用户反馈系统
**个人版（浏览器）**每条新闻底部有反馈栏，持久化到 localStorage：
- **Like**：标记喜欢，卡片左边框变绿
- **Dislike**：标记不喜欢，卡片左边框变红，透明度降低
- **Escalate ▾** 下拉菜单，三个选项：
  1. News facts are incorrect（新闻有误）
  2. Analysis is flawed（分析有误）
  3. Duplicate — already sent（重复推送）
- 侧边栏实时显示偏好统计：Liked / Disliked / Escalated / Seen total

**邮件版（Phase 2）** 每封邮件底部四个链接：

| 按钮 | 点击后 | 用户操作 |
|------|--------|----------|
| 👍 Useful today | 新标签打开 `thankyou.html`，显示感谢，3秒后自动关闭 | 什么都不用做 |
| 👎 Not relevant | 同上，文案改为 "Noted — thanks!" | 什么都不用做 |
| ⚑ Report an issue | 新标签打开 Google Form，日期已预填 | 填写问题描述，提交 |
| Unsubscribe | 新标签打开退订表单 | 填邮箱 + 可选原因 |

### 配置项（个人版侧边栏）
- Topics 话题开关：AI/High-tech、Geopolitics、Macro/Markets、Career/AI pivot、Policy/Regulation
- Schedule 推送时间：Daily 07:00 / 08:00 (Toronto) / Manual
- Email 邮箱
- Stories per run：5 / 7 / 10 条

---

## 技术实现

### 架构概述

- **个人版**：单文件 HTML，无需后端，浏览器直接打开
- **Phase 2 服务端**：`agent.py` Python 脚本，GitHub Actions 每日定时运行

### Claude API

- **模型**：`claude-sonnet-4-20250514`
- **工具**：`web_search_20250305`（`betas: ["web-search-2025-03-05"]`）
- **max_tokens**：16 000

### Skill 外部化（Phase 2）

`agent.py` 的 system prompt 不再内联，而是从 `skills/` 目录中的 `.md` 文件载入，通过 `render_skill()` 函数处理：
- 自动剥离 YAML frontmatter（`---` 块）
- 支持 `%%PLACEHOLDER%%` 变量替换（避免与 JSON 大括号冲突）

当前 skill 文件：

| 文件 | 用途 |
|------|------|
| `skills/news_extractor.md` | **单次调用**（当前 `agent.py` 使用）：web search + 事实提取 + 分析三合一 |
| `skills/news_extractor_staged.md` | 双阶段第一阶段：web search + 事实提取，分析字段留空 |
| `skills/news_analyst.md` | 双阶段第二阶段：无 web search，纯分析填充（用于 `agent_staged.py`） |

### 双阶段架构（`agent_staged.py`，备用）

`agent_staged.py` 将一次大 Claude 调用拆分为两个专注调用：
- **Stage 1**：web_search + 事实提取（`news_extractor_staged.md`）
- **Stage 2**：无搜索，纯分析填充（`news_analyst.md`）；若 Stage 2 失败，降级为发送无分析版本

> **注意**：当前 `daily.yml` 仍运行 `agent.py`（单次调用），`agent_staged.py` 尚未切换为生产主路径。

### 5W 可信度规则（v2.0 新增）

**5W 是高可信度区域**，用户默认这里的内容是经过核实的事实。规则违反的后果比 analysis 部分的错误更严重。

**数字来源管控：**

| 来源层级 | 数字能否进 5W | Confidence 上限 |
|---|---|---|
| T1 | ✓ | HIGH |
| T2 | ✓ | HIGH |
| T3a（Reuters/Bloomberg/Xinhua/Nikkei） | ✓ | HIGH |
| T3b（WSJ/FT/SCMP） | ✗ → 移至 analysis | MED |
| T4 | ✗ → 移至 analysis | MED |

**文字内容规则：**
- T3b（WSJ/FT/SCMP）文字进 5W 前必须剔除编辑性判断（"amid growing concerns"、"analysts say"、"widely seen as" 等），只保留可独立核实的事实
- T4 智库/研究机构：原创调查/测量数据可进 5W；预测/模型结论移至 analysis

**CONTEXT 字段（JSON 字段名保持 `whyEn/whyCn`，显示标签改为 CONTEXT）：**
- 只写可核实的事实背景（前置事件、已陈述条件）
- 禁止因果措辞：`because / due to / as a result of / driven by / prompted by`
- 允许（仅描述事实序列时）：`following / after / amid`（条件须来自原文）、`citing`（须直接引用官方声明）
- 无法核实则写 `Not confirmed`
- 因果解释移至 analysis

**已宣布计划的写法：** 官方公告的未来行动属于事实，使用 `announced plan to…` / `stated intention to…` 措辞，不写成已确认的结果

**字段留空规则：** 无法用可核实信息填充某字段时，写 `Not confirmed`，禁止推断或捏造

### JSON 字段规范

每条新闻的 JSON 对象包含以下字段（含新增的 `dateConfidence`）：

```json
{
  "rank": number,
  "sourceTier": "T1"|"T2"|"T3"|"T4",
  "source": "Source name (English)",
  "sourceCn": "来源名称（中文）",
  "sourceUrl": "URL",
  "topic": "tech"|"geo"|"macro",
  "confidence": "HIGH"|"MED"|"LOW",
  "newsDate": "YYYY-MM-DD",
  "dateConfidence": "confirmed"|"estimated",
  "isMajorUpdate": false,
  "updateNote": "",
  "headlineEn": "...", "headlineCn": "...",
  "whoEn": "...",  "whoCn": "...",
  "whatEn": "...", "whatCn": "...",
  "whenEn": "...", "whenCn": "...",
  "whereEn": "...", "whereCn": "...",
  "whyEn": "...",  "whyCn": "...",
  "investEn": "[Analysis] ...", "investCn": "[分析] ...",
  "geoEn": "[Analysis] ...",   "geoCn": "[分析] ...",
  "careerEn": "[Analysis] ...", "careerCn": "[分析] ..."
}
```

`dateConfidence` 说明：
- `"confirmed"`：新闻日期在来源中明确标注
- `"estimated"`：日期从相对时间（"3 hours ago"、"yesterday"）推算
- 邮件中估算日期会在日期旁附 `est.` 标记

### JSON 修复机制

Claude 返回的 JSON 字符串可能含未转义引号（常见于中文文本），`agent.py` 提供三层修复：
1. **原始解析**：直接 `json.loads()`
2. **字符级修复**：`_repair_json_quotes()` 逐字符扫描，转义字符串内部的 ASCII `"`
3. **Claude 修复调用**：发送损坏 JSON 给 Claude（无 web_search），要求返回修正版本

### 本地持久化

**个人版（localStorage）**存储三类数据：
- `di_hist`：去重历史（headlineKey → {date, isMajorUpdate}）
- `di_fb`：用户反馈（headlineKey → liked/disliked/escalated）
- `di_esc`：Escalation 记录（数组，含 reason 和 timestamp）

**Phase 2（服务端文件）**：
- `dedup_history.json`：去重历史，GitHub Actions 每次运行后 commit 回 repo

### Demo 数据

API 调用失败（个人版）或设置 `DEMO=1` 环境变量（Phase 2）时，自动加载 2 条示例数据（Fed + NVIDIA），跳过 Claude API 调用。

---

## MVP 发件配置

| 项目 | 配置 |
|------|------|
| 发件地址 | `digest@lensignal.com` |
| 发件域名 | `lensignal.com`（Cloudflare DNS，Resend 已验证 ✅）|
| DNS 记录 | DKIM + SPF (MX + TXT) + DMARC，均已添加 |
| 调试模式 | 在 `daily.yml` 的 env 加 `DEMO: "1"` 可跳过 Claude API |
| 定时任务 | `cron: '30 10 * * *'`（10:30 UTC = 05:30 EST / 06:30 EDT，目标送达 ~07:00-07:10 Toronto）|

### 当前订阅者（3人）

| 姓名 | 邮箱 |
|------|------|
| Mavis | loiswufe@gmail.com |
| Chengli | chengli.wu@hotmail.com |
| Chunyang | zcysunny@outlook.com |

### 运行成本

| 服务 | 费用 |
|------|------|
| Claude API | ~$0.05/天 |
| Resend 邮件 | 免费（100封/天，3000封/月） |
| GitHub Actions | 免费 |
| **合计** | **< $2/月** |

---

## 邮件反馈配置

**已配置的 Google Form ID（勿修改）：**
```js
FORM_ID      = '1FAIpQLScN3lYHkYmg0tdXkPi9ofkhUKcIqdf2HTa5J6N2j9t-0Ov8zQ'
ENTRY_DATE   = 'entry.763436474'
ENTRY_RATING = 'entry.771339392'
UNSUB_ID     = '1FAIpQLSc5y-sjQt7f3w18bqQT2rUVRQ8Ef5mJ9fCmufKlmiKqYcEFHw'
```

**`thankyou.html` 已部署到 GitHub Pages ✅**

- Repo：`github.com/Mavis1101/News_Agent`（Public）
- 线上地址：`https://mavis1101.github.io/News_Agent/thankyou.html`
- `news_agent_v3_5.html` 和 `agent.py` 中 `THANKYOU_BASE` 已指向该地址，无需再修改

**退订流程：**
用户点 Unsubscribe → 填表单（邮箱 + 原因）→ 你在 Google Sheet 收到通知 → 手动从 `subscribers.json` 删除

---

## 版本历史

| 版本 | 主要变更 |
|------|----------|
| v1   | 基础原型，手动运行，英文输出 |
| v2   | 加入 T1–T4 来源分级，中英双语输出（中文为主） |
| v3   | 英文为主语言；新闻日期字段；去重+重大更新机制；Like/Dislike/Escalate 反馈系统 |
| v3.1 | 邮件反馈升级：👍 👎 → `thankyou.html` 中转页（静默提交 Google Form + 3秒自动关闭）；⚑ Report issue 和 Unsubscribe 保持 Google Form；所有链接 `target="_blank"` |
| v3.5 | 合并 v3 浏览器端 Like/Dislike/Escalate 反馈 + v3.1 邮件反馈链接；当前个人版主文件 `news_agent_v3_5.html` |
| Phase 2 | `agent.py` 上线：服务端批量发送；邮件改版（背景调亮、字体放大、5W 英文上/中文下堆叠布局）；发件域名 `digest@lensignal.com`；DEMO 模式；dedup 持久化至 `dedup_history.json` |
| Phase 2.1 | Skill 外部化：system prompt 从 `skills/news_extractor.md` 载入（`render_skill()` + `%%PLACEHOLDER%%` 变量替换）；新增 `dateConfidence` 字段（confirmed/estimated，估算日期标注 est.）；三层 JSON 修复机制（原始 → 字符修复 → Claude 修复调用）；去重窗口改为 7 天滚动（原为计数上限 40）；新增 `agent_staged.py`（双阶段架构，备用） |
| Phase 2.2 | **5W 可信度规则**：T3 拆分为 T3a（可信：Reuters/Bloomberg/Xinhua/Nikkei）和 T3b（谨慎：WSJ/FT/SCMP）；T3b/T4 数字禁止进 5W；WHY 改为 CONTEXT（禁止因果措辞，only 事实背景）；Confidence 上限按来源层级强制执行（T3b/T4 上限 MED）；已宣布计划用 "announced plan to…" 措辞；无法核实字段写 "Not confirmed"；`news_extractor.md` 升至 v2.0；Analysis 主定位恢复为"为读者投资/地缘/职场决策服务"；数字规则提取到独立 `number_integrity.md`（staged 架构 Stage 2 不加载，节省 token）|

---

## 产品路线图

### Phase 1 ✅ 个人版（已完成）
- 单文件 HTML，浏览器运行
- T1–T4 来源分级
- 英文主语言 + 中文双语
- 5W 事实 + 三维度分析
- localStorage 去重 + 反馈系统

### Phase 2 ✅ MVP 多用户验证（已上线）
**目标：让真实用户收到邮件并收集反馈**

- [x] `subscribers.json`：手动维护订阅者列表（当前 3 人）
- [x] `agent.py`：Claude API + Resend 批量发送脚本
- [x] `.github/workflows/daily.yml`：每天 ~07:00 Toronto 自动运行
- [x] 邮件模板：👍 👎 一键提交（thankyou.html 中转）+ ⚑ Report + Unsubscribe
- [x] `dedup_history.json`：替代 localStorage 的服务端去重历史（7 天滚动窗口）
- [x] Google Form + Sheet：反馈表单和退订表单已配置完成
- [x] `skills/news_extractor.md`：system prompt 外部化，支持独立迭代
- [x] `dateConfidence` 字段 + 三层 JSON 修复机制
- [x] `agent_staged.py`：双阶段架构（备用，尚未切换为生产主路径）

**成功指标：** 20人中2周后仍有15+人订阅，且收到至少5条反馈

### Phase 3 — 个性化订阅（付费前提）
触发条件：MVP 验证成功，有用户主动询问"能不能只看某些话题"

- 订阅页面（静态 HTML 表单，Netlify 部署）
- 用户选择话题偏好（AI/地缘/宏观/职场）
- 按偏好生成不同版本的邮件内容
- 来源可信度权重 `source_weights.yaml`

### Phase 4 — 商业化
触发条件：50+ 活跃订阅者，退订率 < 10%

- 付费订阅（Stripe）
- 用户账户系统
- Web Dashboard（历史简报存档，趋势分析）
- 真正的一键退订（token-based，全自动）

---

## 迭代规范

- 每次迭代**基于当前最新版本文件**修改，保存为新版本号（如 `news_agent_v4.html`）
- 旧版本文件保留，不覆盖
- 修改前先明确说明：基于哪个文件 + 具体改动内容
- 每次改动后更新本文件的版本历史表格和 Phase checklist

---

## 文件结构

```
本地 Claude-News-Agent/ 文件夹
├── news_agent_v3_5.html            ← 个人版主文件（当前）
├── news_agent_v2.html              ← 历史版本
├── thankyou.html                   ← 反馈中转页 ✅ 已部署到 GitHub Pages
├── NEWS_AGENT_INSTRUCTIONS.md      ← 本文件
│
├── phase2-mvp/                     ← Phase 2 服务端
│   ├── agent.py                    ← MVP 核心脚本（当前生产主路径）
│   ├── agent_staged.py             ← 双阶段架构脚本（备用，未切换）
│   ├── subscribers.json            ← 订阅者列表（手动维护，当前 3 人）
│   ├── dedup_history.json          ← 去重历史（7 天滚动，GitHub Actions 自动 commit）
│   └── skills/                     ← System prompt 外部化目录
│       ├── news_extractor.md       ← 单次调用：搜索 + 提取 + 分析（agent.py 使用）
│       ├── news_extractor_staged.md← 双阶段第一阶段：搜索 + 提取（agent_staged.py 使用）
│       ├── news_analyst.md         ← 双阶段第二阶段：纯分析（agent_staged.py 使用）
│       └── number_integrity.md     ← 数字来源规则（供 Stage 1 加载，Stage 2 不需要）
│
├── .github/
│   └── workflows/
│       └── daily.yml               ← 定时任务（cron: 10:30 UTC，目标 ~07:00 Toronto）
│
└── (Phase 3 新增)
    ├── subscribe_page.html         ← 订阅落地页
    └── source_weights.yaml         ← 来源权重配置

GitHub repo：github.com/Mavis1101/News_Agent（Public）
GitHub Pages：https://mavis1101.github.io/News_Agent/
```
