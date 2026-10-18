# p4 证据账本（取材日期 2026-10-18）

| id | 类型 | 拟用表述 | 来源 URL | 来源原文摘录 | 等级 | 状态 | 段 | 备注 |
|---|---|---|---|---|---|---|---|---|
| E1 | 事件/年份 | 1609年末，伽利略用望远镜观察月球 | https://www.mdpi.com/2076-3263/9/1/5 ; https://www.britannica.com/biography/Galileo-Galilei/Telescopic-discoveries | MDPI: "In late 1609 he discovered that the Moon was not a smooth heavenly sphere but had mountains and valleys"; Britannica: "In the fall of 1609 Galileo began observing the heavens... In December he drew the Moon's phases" | T1(期刊/百科)+T1 | verified | 2 | 写"年末"而非具体月份（观测起点学界有9月至12月推断，见 doi 10.1017/s1743921310007234） |
| E2 | 作品↔年代 | 次年（1610）在《星际信使》中断定月面并非光滑完美的球体，而有山岭与深谷 | https://www.sites.hps.cam.ac.uk/starry/galsidnun.html ; https://en.wikipedia.org/wiki/Sidereus_Nuncius | 剑桥HPS: "published Sidereus Nuncius... in 1610... the surface of the moon was not smooth and perfectly spherical, but was pitted with craters and had mountains" ; 原文译本: "not smooth, uniform, and precisely spherical as a great number of philosophers believe" | T1+T2 | verified | 2 | 用"断定"而非"看到"：Galileo 1611 自述山峦靠推断而非直接所见 |
| E3 | 观点归属 | 在当时不少哲学家眼中，天体理应光滑而完美 | 同 E2（原文 "as a great number of philosophers believe it to be"）；Rice Galileo Project | "not smooth, uniform, and precisely spherical as a great number of philosophers believe it (and the other heavenly bodies) to be" | T1 | verified | 2 | 措辞不高于来源（"不少"） |
| E4 | 学术概念 | 李普曼指出人们依赖脑中的图像去认识无法亲见的世界（转述，无引号） | evidence-bank §1 李普曼《舆论》（来源见 assets/evidence-audit.json） | bank: 人们依赖脑中的"图像"而非直接经验认识世界 | bank | paraphrase-only | 3 | 未写"媒介为我们构造世界"；未加引号 |
| E5 | 引文 | 庄子说"物物而不物于物" | evidence-bank §1 庄子（《庄子·山木》）〔直引〕 | bank: "物物而不物于物"（《庄子·山木》） | bank | verified | 5 | 文中未署篇名，只署庄子 |
| E6 | 时代现象 | 输入一句话，屏幕上浮出一座悬在云端的城市（生成式模型） | evidence-bank §4 时代语料（AI生成内容对想象力的挑战） | bank: 一笔带过，不加具体数字 | bank | verified(现象概括) | 1 | 假设性场景，无具体产品/数字 |
| E7 | 无来源概念 | 人的认知吝啬、省力原则 | prompt-analysis.md 归因词库 | 认知吝啬（省力原则） | skill内 | 概括性心理学表述 | 3 | 不作为事实案例 |
| E8 | 题干校准 | 立意落在官方专家共识空间：科技既拓展想象边界，也可能削弱想象的主体性与独立性 | https://www.eol.cn/kaoshi/gaokao/gkzx/202606/t20260607_2742382.shtml ; shanghai.gov.cn 20260608 | "它既能拓展人类想象的疆域……也能影响想象的主体性、消解想象的独立性" | T1转载 | verified | -- | 仅校准，未引入文中 |

新增外部案例（evidence-bank之外）：1个（伽利略）≤2。
## 闸门
- [x] claims 抽取项：星际信使(E2)、1609年(E1)、物物而不物于物/庄子(E5)均有行；speaker 误报"一座悬在""普曼早就"为抽取噪声；李普曼、伽利略未被 claims 抽出，已手动入账(E4,E1-3)
- [x] 无 dropped 残留（本稿无 dropped 行）
- [x] paraphrase-only(E4) 无引号
- [x] 无仅T3来源事实
- [x] 措辞强度 ≤ 来源
- [x] 新增案例 1 ≤ 2
