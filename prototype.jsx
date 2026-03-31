import { useState } from "react";

const TODAY = "2026-03-28";

const TIER_COLOR = {
  T1: "#c8a96e",
  T2: "#4db8a0",
  T3: "#6090d8",
  T4: "#8a8880",
};

const TOPIC_LABEL = {
  tech: "AI/Tech",
  geo: "Geopolitics",
  macro: "Macro",
  career: "Career",
  policy: "Policy",
};

const STORIES = [
  {
    rank: 1,
    sourceTier: "T1",
    source: "Federal Reserve",
    sourceCn: "美联储",
    sourceUrl: "https://www.federalreserve.gov/newsevents/pressreleases.htm",
    topic: "macro",
    confidence: "HIGH",
    newsDate: "2026-03-28",
    isMajorUpdate: false,
    updateNote: "",
    headlineEn: "Fed holds rates steady at 4.25–4.50%; signals two cuts possible in H2 2026",
    headlineCn: "美联储维持利率4.25–4.50%不变，暗示2026年下半年或降息两次",
    whoEn: "Federal Reserve FOMC, Chair Jerome Powell",
    whoCn: "美联储联邦公开市场委员会，主席鲍威尔",
    whatEn: "Post-meeting statement holds federal funds rate unchanged; dot plot shows two 25bp cuts in H2",
    whatCn: "会后声明维持基准利率不变；点阵图显示下半年两次25基点降息",
    whenEn: "March 28, 2026 — FOMC meeting decision",
    whenCn: "2026年3月28日 FOMC会议决议",
    whereEn: "Washington D.C.",
    whereCn: "华盛顿特区",
    whyEn: "Services inflation remains sticky at 3.8%; labor market resilient with 180K jobs added in Feb",
    whyCn: "服务业通胀韧性较强（3.8%），2月新增就业18万人，劳动市场稳健",
    investEn: "[Analysis] Dollar weakened slightly post-statement. Rate-sensitive sectors (REITs, utilities) rallied 1.2%. Watch for 10Y yield compression toward 4.0% if cuts materialize.",
    investCn: "[分析] 声明后美元小幅走弱，利率敏感板块（REITs、公用事业）上涨1.2%。若降息落地，10年期美债收益率或压缩至4.0%附近。",
    geoEn: "[Analysis] Sustained high US rates continue to pressure EM capital flows and USD-denominated debt in developing economies.",
    geoCn: "[分析] 美国高利率持续，新兴市场资本外流压力加大，发展中国家美元计价债务风险上升。",
    careerEn: "[Analysis] FinTech and crypto hiring remains subdued. Traditional finance adds headcount in fixed income desks anticipating rate cycle turn.",
    careerCn: "[分析] 金融科技与加密货币招聘依然疲软；传统金融机构固定收益部门提前布局，增加招聘。",
  },
  {
    rank: 2,
    sourceTier: "T1",
    source: "White House",
    sourceCn: "白宫",
    sourceUrl: "https://www.whitehouse.gov/briefing-room/",
    topic: "policy",
    confidence: "HIGH",
    newsDate: "2026-03-28",
    isMajorUpdate: true,
    updateNote: "Executive Order signed — previously announced as draft framework",
    headlineEn: "Trump signs Executive Order restricting AI model exports to 22 nations",
    headlineCn: "特朗普签署行政令，限制向22国出口AI模型",
    whoEn: "President Donald Trump; Commerce Dept; BIS",
    whoCn: "总统特朗普；商务部；工业和安全局",
    whatEn: "EO restricts export of frontier AI models (>10^26 FLOPs training compute) to 22 countries without license",
    whatCn: "行政令限制向22国出口前沿AI模型（训练算力>10^26 FLOPs），需获许可证",
    whenEn: "March 28, 2026 — signed at 14:00 ET",
    whenCn: "2026年3月28日东部时间14:00签署",
    whereEn: "White House, Washington D.C.",
    whereCn: "白宫，华盛顿特区",
    whyEn: "National security concerns; prevents adversaries acquiring frontier AI capabilities via third-party routes",
    whyCn: "国家安全考量，防止对手通过第三方渠道获取前沿AI能力",
    investEn: "[Analysis] Near-term headwind for US AI cloud providers (MSFT, AMZN, GOOG) serving restricted markets. Long-term moat for US-based AI incumbents; barriers to entry rise globally.",
    investCn: "[分析] 短期利空为受限市场提供服务的美国AI云厂商（微软、亚马逊、谷歌）；长期有利于美国AI头部企业建立护城河，全球准入壁垒提升。",
    geoEn: "[Analysis] Accelerates AI bloc fragmentation. EU likely to face pressure to align. China will accelerate domestic model development.",
    geoCn: "[分析] 加速AI阵营分裂；欧盟将面临跟进压力；中国将加速本土大模型研发。",
    careerEn: "[Analysis] Surge in demand for AI compliance and export control specialists. International AI roles face uncertainty; US-based positions favored.",
    careerCn: "[分析] AI合规与出口管制专家需求激增；国际AI岗位面临不确定性，美国本土职位更受青睐。",
  },
  {
    rank: 3,
    sourceTier: "T2",
    source: "NVIDIA Investor Relations",
    sourceCn: "英伟达投资者关系",
    sourceUrl: "https://investor.nvidia.com/",
    topic: "tech",
    confidence: "HIGH",
    newsDate: "2026-03-28",
    isMajorUpdate: false,
    updateNote: "",
    headlineEn: "NVIDIA announces Blackwell Ultra B300 GPU: 2× memory bandwidth, ships Q3 2026",
    headlineCn: "英伟达发布Blackwell Ultra B300 GPU：内存带宽翻倍，2026年Q3出货",
    whoEn: "NVIDIA CEO Jensen Huang; datacenter customers",
    whoCn: "英伟达CEO黄仁勋；数据中心客户",
    whatEn: "B300 GPU features 288GB HBM4 memory, 15 TB/s bandwidth; pricing ~$40K per unit",
    whatCn: "B300 GPU搭载288GB HBM4显存，带宽15 TB/s，单卡售价约4万美元",
    whenEn: "March 28, 2026 — GTC 2026 keynote",
    whenCn: "2026年3月28日 GTC 2026主题演讲",
    whereEn: "SAP Center, San Jose, California",
    whereCn: "加州圣何塞SAP中心",
    whyEn: "Surging inference demand from LLM deployments; B200 supply constrained through Q2",
    whyCn: "大模型推理需求激增；B200供应持续紧张至Q2",
    investEn: "[Analysis] Supply chain winners: SK Hynix (HBM4 sole supplier), TSMC (N3P process). NVDA gross margin expansion expected to 78%+ in FY27.",
    investCn: "[分析] 供应链受益方：SK海力士（HBM4独家供应商）、台积电（N3P制程）。英伟达FY27毛利率预计升至78%以上。",
    geoEn: "[Analysis] B300 likely subject to new EO export controls immediately. Widens US-China AI hardware gap further.",
    geoCn: "[分析] B300可能立即受新行政令出口管制；进一步拉大中美AI硬件差距。",
    careerEn: "[Analysis] Strong demand for CUDA engineers, AI infra architects, and HBM memory design talent.",
    careerCn: "[分析] CUDA工程师、AI基础设施架构师及HBM存储设计人才需求强劲。",
  },
  {
    rank: 4,
    sourceTier: "T3",
    source: "Reuters",
    sourceCn: "路透社",
    sourceUrl: "https://www.reuters.com/",
    topic: "geo",
    confidence: "MED",
    newsDate: "2026-03-28",
    isMajorUpdate: false,
    updateNote: "",
    headlineEn: "China's PBOC injects ¥800B via 7-day reverse repo amid yuan pressure",
    headlineCn: "人民银行通过7天逆回购注入8000亿元，应对人民币贬值压力",
    whoEn: "People's Bank of China (PBOC)",
    whoCn: "中国人民银行",
    whatEn: "PBOC conducts ¥800B 7-day reverse repo at 1.5%; largest single-day operation since Jan 2024",
    whatCn: "央行开展8000亿元7天逆回购操作，利率1.5%，为2024年1月以来单日最大规模",
    whenEn: "March 28, 2026 — morning open market operation",
    whenCn: "2026年3月28日上午公开市场操作",
    whereEn: "Beijing, China",
    whereCn: "中国北京",
    whyEn: "Yuan weakened past 7.35/USD; capital outflow pressure following AI export EO announcement",
    whyCn: "人民币跌破7.35兑1美元；AI出口行政令发布后资本外流压力加剧",
    investEn: "[Analysis] Watch CNH/CNY spread as offshore pressure indicator. Chinese equities (A-shares) may face short-term liquidity headwind despite injection.",
    investCn: "[分析] 关注离岸在岸人民币价差作为压力指标；尽管有流动性注入，A股短期仍可能承压。",
    geoEn: "[Analysis] Liquidity injection signals Beijing prioritizing financial stability over currency defense — potentially allowing gradual yuan depreciation.",
    geoCn: "[分析] 流动性注入表明北京优先维护金融稳定而非汇率防守，或允许人民币渐进式贬值。",
    careerEn: "[Analysis] FX and macro roles in demand at regional banks managing China exposure.",
    careerCn: "[分析] 区域银行中负责中国敞口管理的外汇与宏观岗位需求上升。",
  },
  {
    rank: 5,
    sourceTier: "T3",
    source: "Financial Times",
    sourceCn: "金融时报",
    sourceUrl: "https://www.ft.com/",
    topic: "tech",
    confidence: "MED",
    newsDate: "2026-03-28",
    isMajorUpdate: false,
    updateNote: "",
    headlineEn: "EU AI Act enforcement begins: first wave of fines targets biometric surveillance",
    headlineCn: "欧盟AI法案开始执法：首批罚款针对生物识别监控系统",
    whoEn: "European AI Office; unnamed biometric surveillance vendors",
    whoCn: "欧盟AI办公室；匿名生物识别监控供应商",
    whatEn: "EU AI Office issues first enforcement actions under AI Act; fines up to €35M for prohibited biometric AI use",
    whatCn: "欧盟AI办公室依据AI法案发出首批执法行动；禁止使用的生物识别AI最高罚款3500万欧元",
    whenEn: "March 28, 2026",
    whenCn: "2026年3月28日",
    whereEn: "Brussels, Belgium",
    whereCn: "比利时布鲁塞尔",
    whyEn: "AI Act prohibited systems provisions came into force Feb 2, 2025; enforcement grace period expired",
    whyCn: "AI法案禁止性系统条款于2025年2月2日生效，执法宽限期届满",
    investEn: "[Analysis] Compliance risk for surveillance tech vendors operating in EU. Opportunity for AI auditing and compliance SaaS providers.",
    investCn: "[分析] 在欧盟运营的监控科技供应商合规风险上升；AI审计与合规SaaS服务商迎来机遇。",
    geoEn: "[Analysis] EU-US AI regulatory divergence widens; US EO on exports contrasts with EU's risk-based internal controls approach.",
    geoCn: "[分析] 欧美AI监管分歧扩大；美国出口管制行政令与欧盟基于风险的内部管控路径形成对比。",
    careerEn: "[Analysis] Demand surge for AI compliance officers, legal counsel specializing in EU AI Act, and technical auditors across Europe.",
    careerCn: "[分析] 欧洲AI合规官、欧盟AI法案专业法律顾问及技术审计人员需求激增。",
  },
];

function TierBadge({ tier }) {
  return (
    <span style={{
      background: "rgba(200,169,110,0.08)",
      color: TIER_COLOR[tier] || "#8a8880",
      border: `1px solid ${TIER_COLOR[tier]}44`,
      padding: "1px 7px",
      borderRadius: 3,
      fontSize: 10,
      fontFamily: "monospace",
      letterSpacing: "0.05em",
    }}>
      {tier}
    </span>
  );
}

function AnalysisBlock({ labelEn, labelCn, color, en, cn }) {
  if (!en) return null;
  return (
    <div style={{ marginBottom: 12 }}>
      <span style={{
        background: "rgba(0,0,0,0.3)",
        color,
        padding: "2px 8px",
        borderRadius: 3,
        fontSize: 10,
        fontFamily: "monospace",
      }}>
        {labelEn} · {labelCn}
      </span>
      <div style={{ color: "#dedad2", fontSize: 13, marginTop: 5, lineHeight: 1.55 }}>{en}</div>
      <div style={{ color: "#9a9890", fontSize: 11, marginTop: 3, lineHeight: 1.5 }}>{cn}</div>
    </div>
  );
}

function NewsCard({ item, index }) {
  const [expanded, setExpanded] = useState(false);
  const tier = item.sourceTier;
  const tierColor = TIER_COLOR[tier] || "#8a8880";
  const topicLabel = TOPIC_LABEL[item.topic] || item.topic;

  return (
    <div style={{
      border: "1px solid #363a40",
      borderRadius: 8,
      marginBottom: 14,
      overflow: "hidden",
      background: "#2c3038",
    }}>
      {/* Header */}
      <div style={{ padding: "16px 18px 0" }}>
        <div style={{
          fontSize: 11,
          color: "#7a7875",
          fontFamily: "monospace",
          marginBottom: 8,
          display: "flex",
          alignItems: "center",
          gap: 6,
          flexWrap: "wrap",
        }}>
          <span style={{ color: "#555" }}>#{index}</span>
          <TierBadge tier={tier} />
          <span style={{ color: "#555" }}>·</span>
          <span>{item.source}</span>
          <span style={{ color: "#555" }}>·</span>
          <span style={{ color: tierColor }}>{topicLabel}</span>
          <span style={{ color: "#555" }}>·</span>
          <span style={{ color: item.confidence === "HIGH" ? "#4db8a0" : item.confidence === "MED" ? "#c8a96e" : "#8a8880" }}>
            {item.confidence}
          </span>
          <span style={{ color: "#555" }}>·</span>
          <span>{item.newsDate}</span>
          {item.isMajorUpdate && (
            <span style={{ color: "#4db8a0", fontSize: 10 }}>⟳ Major update</span>
          )}
        </div>

        {/* Headline */}
        <a href={item.sourceUrl} target="_blank" rel="noreferrer" style={{
          display: "block",
          fontSize: 16,
          fontWeight: 400,
          lineHeight: 1.5,
          color: "#dedad2",
          textDecoration: "none",
          marginBottom: 3,
        }}>
          {item.headlineEn}
        </a>
        <div style={{ fontSize: 13, color: "#9a9890", fontFamily: "serif", marginBottom: 10 }}>
          {item.headlineCn}
        </div>
        {item.updateNote && (
          <div style={{ fontSize: 11, color: "#4db8a0", fontFamily: "monospace", marginBottom: 8 }}>
            Update: {item.updateNote}
          </div>
        )}
      </div>

      {/* 5W */}
      <div style={{ padding: "10px 18px", fontSize: 12 }}>
        {[
          ["WHO", "何人", "whoEn", "whoCn"],
          ["WHAT", "何事", "whatEn", "whatCn"],
          ["WHEN", "何时", "whenEn", "whenCn"],
          ["WHERE", "何地", "whereEn", "whereCn"],
          ["WHY", "为何", "whyEn", "whyCn"],
        ].map(([en, cn, enKey, cnKey]) => (
          <div key={en} style={{ marginBottom: 5, display: "flex", gap: 8 }}>
            <span style={{ color: "#7a7875", minWidth: 48, fontFamily: "monospace", fontSize: 10, paddingTop: 1 }}>{en}</span>
            <div>
              <div style={{ color: "#dedad2", lineHeight: 1.45 }}>{item[enKey] || "—"}</div>
              <div style={{ color: "#7a7875", fontSize: 11, lineHeight: 1.4 }}>{item[cnKey] || "—"}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Analysis toggle */}
      <div style={{ background: "#22252a", padding: "10px 18px" }}>
        <button
          onClick={() => setExpanded(!expanded)}
          style={{
            background: "none",
            border: "none",
            color: "#6090d8",
            fontSize: 11,
            fontFamily: "monospace",
            cursor: "pointer",
            padding: 0,
            letterSpacing: "0.05em",
          }}
        >
          {expanded ? "▲ Hide Analysis" : "▼ Show Analysis · 分析"}
        </button>

        {expanded && (
          <div style={{ marginTop: 12 }}>
            <AnalysisBlock labelEn="Investment" labelCn="投资" color="#6090d8" en={item.investEn} cn={item.investCn} />
            <AnalysisBlock labelEn="Geopolitics" labelCn="地缘" color="#c8a96e" en={item.geoEn} cn={item.geoCn} />
            <AnalysisBlock labelEn="Career" labelCn="职场" color="#70b880" en={item.careerEn} cn={item.careerCn} />
            <a href={item.sourceUrl} target="_blank" rel="noreferrer"
              style={{ color: "#6090d8", fontSize: 12, textDecoration: "none" }}>
              → Source
            </a>
          </div>
        )}
      </div>
    </div>
  );
}

export default function App() {
  const [lang, setLang] = useState("both");

  return (
    <div style={{
      background: "#1a1d21",
      minHeight: "100vh",
      padding: "0 0 40px",
      fontFamily: "Georgia, serif",
    }}>
      {/* Top bar */}
      <div style={{
        background: "#22252a",
        borderBottom: "1px solid #2e3138",
        padding: "10px 24px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        position: "sticky",
        top: 0,
        zIndex: 10,
      }}>
        <span style={{ color: "#7a7875", fontSize: 11, fontFamily: "monospace" }}>
          Intelligence Digest · Prototype
        </span>
        <div style={{ display: "flex", gap: 6 }}>
          {["both", "en", "cn"].map(l => (
            <button key={l} onClick={() => setLang(l)} style={{
              background: lang === l ? "#363a40" : "none",
              border: "1px solid #363a40",
              borderRadius: 4,
              color: lang === l ? "#c8a96e" : "#7a7875",
              fontSize: 10,
              fontFamily: "monospace",
              padding: "3px 10px",
              cursor: "pointer",
            }}>
              {l === "both" ? "EN·中" : l === "en" ? "EN" : "中文"}
            </button>
          ))}
        </div>
      </div>

      <div style={{ maxWidth: 680, margin: "0 auto", padding: "0 16px" }}>

        {/* Masthead */}
        <div style={{
          borderBottom: "1px solid #363a40",
          padding: "28px 0 20px",
          marginBottom: 24,
        }}>
          <div style={{ fontSize: 26, color: "#c8a96e", letterSpacing: "0.06em" }}>
            Intelligence Digest
          </div>
          <div style={{ fontSize: 11, color: "#7a7875", letterSpacing: "0.16em", marginTop: 4, fontFamily: "serif" }}>
            今日情报简报
          </div>
          <div style={{ fontSize: 11, color: "#555", marginTop: 8, fontFamily: "monospace" }}>
            {TODAY}
          </div>

          {/* Tier legend */}
          <div style={{ display: "flex", gap: 12, marginTop: 14, flexWrap: "wrap" }}>
            {Object.entries(TIER_COLOR).map(([tier, color]) => (
              <span key={tier} style={{ fontSize: 10, fontFamily: "monospace", color }}>
                <span style={{ background: color + "22", border: `1px solid ${color}44`, padding: "1px 6px", borderRadius: 3 }}>{tier}</span>
                {" "}{tier === "T1" ? "Official" : tier === "T2" ? "Corporate IR" : tier === "T3" ? "Major Media" : "Other"}
              </span>
            ))}
          </div>
        </div>

        {/* Cards */}
        {STORIES.map((story, i) => (
          <NewsCard key={story.rank} item={story} index={i + 1} />
        ))}

        {/* Footer */}
        <div style={{
          marginTop: 24,
          paddingTop: 18,
          borderTop: "1px solid #2a2a2a",
          textAlign: "center",
        }}>
          <div style={{ fontSize: 12, color: "#555", marginBottom: 14 }}>How was today's digest?</div>
          <div style={{ display: "flex", gap: 8, justifyContent: "center", flexWrap: "wrap", marginBottom: 14 }}>
            {[["👍 Useful today", "#3a7a50", "#70b880"], ["👎 Not relevant", "#6a3a3a", "#c86060"], ["⚑ Report issue", "#7a6030", "#d4943a"]].map(([label, border, color]) => (
              <span key={label} style={{
                padding: "7px 16px",
                border: `1px solid ${border}`,
                borderRadius: 6,
                color,
                fontSize: 12,
                cursor: "pointer",
              }}>{label}</span>
            ))}
          </div>
          <div style={{ fontSize: 10, color: "#444" }}>
            Analysis sections are AI inference — not confirmed fact.<br />
            分析部分为AI推断，非确认事实。
          </div>
        </div>

      </div>
    </div>
  );
}
