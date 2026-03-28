# News Agent · 情报简报 — Project Instructions

## 项目概述

这是一个新闻情报 Agent，每日抓取高科技、地缘政治、宏观经济、AI职场四个领域的重要新闻，生成英文为主、中英双语的情报简报，通过邮件推送。

**双轨目标：**
- **个人使用**：`news_agent_v3_5.html` 单文件，浏览器直接打开运行
- **MVP 商业验证**：低成本多用户版本，向 5–20 人推送同一份简报，验证产品需求，收集反馈

---

## 当前版本功能（v3）

### 内容与来源
- **来源分级 T1–T4**，优先级强制执行：
  - T1：政府官方声明、白宫/国务院/议会、央行（美联储/人民银行/欧央行）、监管机构
  - T2：大公司官方 IR 页面、财报、官方新闻稿（Apple Newsroom、NVIDIA IR 等）、交易所公告
  - T3：路透社、彭博、新华社、FT、Nikkei、WSJ
  - T4：其他媒体/博客，confidence 强制不超过 MED，输出中必须注明
- T4 来源的 confidence 不得为 HIGH；同一事件若存在 T1/T2 来源，忽略 T4
- sourceUrl 必须是原始官方 URL，不得是聚合器链接

### 输出格式
- **英文为主语言**：大标题英文（EB Garamond 衬线体），中文作为副标题（Noto Serif SC）
- **每条新闻包含**：
  - 来源层级徽章（T1/T2/T3/T4）+ 官方来源标记
  - 新闻发布日期（YYYY-MM-DD，显示在 WHEN 字段）
  - 5W 双语对照表格（英文左列，中文右列）：WHO/何人、WHAT/何事、WHEN/何时、WHERE/何地、WHY/为何
  - 三维度推理分析（明确标注为 [Analysis]/[分析]，非确认事实）：
    - Investment · 投资信号
    - Geopolitics · 地缘政治
    - Career · 职场/AI转行
  - Confidence 置信度标签：HIGH（绿）/ MED（金）/ LOW（灰）

### 去重机制
- 已推送的新闻存入 localStorage，下次运行自动跳过
- 例外：`isMajorUpdate: true` 的条目（重大新进展）绕过去重，显示 "Major update" 徽章
- 去重历史上限 40 条，可在侧边栏点击 "Clear history & prefs" 重置

### 用户反馈系统
每条新闻底部有反馈栏，所有反馈持久化到 localStorage：
- **Like**：标记喜欢，卡片左边框变绿
- **Dislike**：标记不喜欢，卡片左边框变红，透明度降低
- **Escalate ▾** 下拉菜单，三个选项：
  1. News facts are incorrect（新闻有误）
  2. Analysis is flawed（分析有误）
  3. Duplicate — already sent（重复推送）
- 侧边栏实时显示偏好统计：Liked / Disliked / Escalated / Seen total

### 配置项（侧边栏）
- Topics 话题开关：AI/High-tech、Geopolitics、Macro/Markets、Career/AI pivot、Policy/Regulation
- Schedule 推送时间：Daily 07:00 / 08:00 (Toronto) / Manual
- Email 邮箱
- Stories per run：5 / 7 / 10 条

---

## 技术实现

- **单文件 HTML**，无需后端，浏览器直接打开
- **Claude API**：`claude-sonnet-4-20250514`，带 `web_search_20250305` 工具，max_tokens: 1000
- **输出格式**：纯 JSON 数组，无 markdown 包裹
- **本地持久化**：localStorage 存储三类数据：
  - `di_hist`：去重历史（headlineKey → {date, isMajorUpdate}）
  - `di_fb`：用户反馈（headlineKey → liked/disliked/escalated）
  - `di_esc`：Escalation 记录（数组，含 reason 和 timestamp）
- **Demo 数据**：API 调用失败时自动加载 10 条示例数据（涵盖 Fed、PBOC、NVIDIA、Japan Cabinet 等）

---

## 版本历史

| 版本 | 主要变更 |
|------|----------|
| v1   | 基础原型，手动运行，英文输出 |
| v2   | 加入 T1–T4 来源分级，中英双语输出（中文为主） |
| v3   | 英文为主语言；新闻日期字段；去重+重大更新机制；Like/Dislike/Escalate 反馈系统 |
| v3.1 | 邮件反馈升级：👍 👎 → `thankyou.html` 中转页（静默提交 Google Form + 3秒自动关闭）；⚑ Report issue 和 Unsubscribe 保持 Google Form；所有链接 `target="_blank"` |
| v3.5 | 合并 v3 浏览器端 Like/Dislike/Escalate 反馈 + v3.1 邮件反馈链接；当前主文件 `news_agent_v3_5.html` |
| Phase 2 | `agent.py` 上线：服务端批量发送；邮件改版（背景调亮、字体放大、5W 英文上/中文下）；发件域名 `digest@lensignal.com`；DEMO 模式；dedup 持久化 |

---

## MVP 商业验证方案（低成本多用户版）

### 核心决策

| 决策项 | 选择 | 原因 |
|--------|------|------|
| 订阅者管理 | 手动维护 `subscribers.json` | 5–20人无需自动化 |
| 内容个性化 | 所有人收到同一份简报 | 先验证内容价值，再做个性化 |
| 测试规模 | 5–20人（朋友圈） | 最小验证成本 |
| 用户数据库 | 无 | 不需要注册/登录系统 |

### 发件配置

| 项目 | 配置 |
|------|------|
| 发件地址 | `digest@lensignal.com` |
| 发件域名 | `lensignal.com`（Cloudflare DNS，Resend 已验证 ✅）|
| DNS 记录 | DKIM + SPF (MX + TXT) + DMARC，均已添加 |
| 调试模式 | 在 `daily.yml` 的 env 加 `DEMO: "1"` 可跳过 Claude API |

### 运行成本

| 服务 | 费用 |
|------|------|
| Claude API | ~$0.05/天 |
| Resend 邮件 | 免费（100封/天，3000封/月） |
| GitHub Actions | 免费 |
| **合计** | **< $2/月** |

### 邮件反馈机制

v3 的 Like/Dislike/Escalate 基于 localStorage，多用户场景下你看不到反馈。MVP 改为**邮件内嵌反馈链接**。

**邮件底部四个链接的完整行为（v3.1 已配置）：**

| 按钮 | 点击后 | 用户操作 |
|------|--------|----------|
| 👍 Useful today | 新标签打开 `thankyou.html`，显示感谢，3秒后自动关闭 | 什么都不用做 |
| 👎 Not relevant | 同上，文案改为 "Noted — thanks!" | 什么都不用做 |
| ⚑ Report an issue | 新标签打开 Google Form，日期已预填 | 填写问题描述，提交 |
| Unsubscribe | 新标签打开退订表单 | 填邮箱 + 可选原因 |

**👍 👎 的数据提交方式：**
`thankyou.html` 加载后用 `fetch(..., { mode: 'no-cors' })` 静默向 Google Form 提交数据，用户看不到任何 Google 页面，3秒后窗口自动关闭。如果 `window.close()` 被浏览器拦截（非脚本打开的标签），页面改为显示"You can close this tab."

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

> 退订率和反馈是 MVP 阶段最重要的产品指标。👍 点击率高 = 内容有价值；退订率低 = 用户留存。

### MVP 所需文件（三个）

```
agent.py              ← 核心脚本：调用 Claude + 生成邮件 HTML + 调用 Resend 批量发送
subscribers.json      ← 手动维护的订阅者列表
.github/workflows/
└── daily.yml         ← GitHub Actions 定时任务，每天 07:00 Toronto 自动运行
```

---

## 产品路线图

### Phase 1 ✅ 个人版（已完成）
- 单文件 HTML，浏览器运行
- T1–T4 来源分级
- 英文主语言 + 中文双语
- 5W 事实 + 三维度分析
- localhost 去重 + 反馈系统

### Phase 2 ✅ MVP 多用户验证（已上线）
**目标：让真实用户收到邮件并收集反馈**

- [x] `subscribers.json`：手动维护订阅者列表
- [x] `agent.py`：Claude API + Resend 批量发送脚本
- [x] `.github/workflows/daily.yml`：每天 07:00 Toronto 自动运行
- [x] 邮件模板：👍 👎 一键提交（thankyou.html 中转）+ ⚑ Report + Unsubscribe
- [x] `dedup_history.json`：替代 localStorage 的服务端去重历史
- [x] Google Form + Sheet：反馈表单和退订表单已配置完成

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
本地 news-agent/ 文件夹
├── news_agent_v3_5.html            ← 个人版主文件（当前）
├── news_agent_v2.html              ← 历史版本
├── thankyou.html                   ← 反馈中转页 ✅ 已部署到 GitHub Pages
├── NEWS_AGENT_INSTRUCTIONS.md      ← 本文件
│
├── (Phase 2 新增)
│   ├── agent.py                    ← MVP 核心脚本
│   ├── subscribers.json            ← 订阅者列表（手动维护）
│   ├── dedup_history.json          ← 去重历史（替代 localStorage）
│   └── .github/
│       └── workflows/
│           └── daily.yml           ← 定时任务
│
└── (Phase 3 新增)
    ├── subscribe_page.html         ← 订阅落地页
    └── source_weights.yaml         ← 来源权重配置

GitHub repo：github.com/Mavis1101/News_Agent（Public）
GitHub Pages：https://mavis1101.github.io/News_Agent/
```
