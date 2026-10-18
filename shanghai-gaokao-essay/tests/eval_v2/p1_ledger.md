# 证据账本（p1）取材日期 2026-10-18

| id | 类型 | 拟用表述 | 来源 URL | 来源原文摘录 | 等级 | 状态 | 段 | 备注 |
|---|---|---|---|---|---|---|---|---|
| E1 | 事件 | 1928年，细菌学家弗莱明休假归来，发现培养皿被霉菌污染，霉菌周围细菌不再生长 | https://wwwnc.cdc.gov/eid/article/23/5/16-1556_article | "A chance event in a London laboratory in 1928... Fleming, a bacteriologist at St. Mary's Hospital, had returned from a vacation when... he noticed a zone around an invading fungus on an agar plate in which the bacteria did not grow." | T1(CDC期刊)+ PMC/Britannica 互证 | verified | 2 | "培养皿"=agar plate；"污染"见PMC "contaminated" |
| E2 | 事件 | 弗莱明多看了一眼 | https://pmc.ncbi.nlm.nih.gov/articles/PMC11189133/ | "...had not taken a second look at a contaminated..."（搜索摘要） | T1 | weakened | 3 | 文学化表述，仅指"留意到"，不夸大 |
| E3 | 事件 | 弗莱明1929年发表发现，却无力提纯，此后近十年没有进展 | CDC 同上 | "Fleming published his findings in 1929... efforts to purify... proved beyond his capabilities. For a decade, no progress was made" | T1 | weakened | 3 | 写"近十年" |
| E4 | 事件 | 1939年牛津弗洛里组建团队，钱恩成功提纯 | CDC 同上 | "In 1939, Howard Florey assembled a team... Chain, who successfully purified penicillin" | T1 | verified | 3 | 不写具体提纯年份，只写1939年组队 |
| E5 | 数字/事实 | 1945年三人共同获诺贝尔奖 | https://www.nobelprize.org/prizes/medicine/1945/summary/ | "awarded jointly to Sir Alexander Fleming, Ernst Boris Chain and Sir Howard Walter Florey" | T1 | verified | 3 | |
| E6 | 观点归属 | 巴斯德1854年的演讲中指出，在观察的领域里，机遇只偏爱有准备的头脑（转述，不加引号） | wikimedia/wikisource 文件描述（Pasteur 1854 Douai 演讲）；todayinsci | "Dans les champs de l'observation le hasard ne favorise que les esprits préparés."（搜索摘要，原文法语） | T2 | paraphrase-only | 3 | 法文原句T2互证；中文不加引号；不写地点 |
| E7 | 人物/作品 | 苏轼因乌台诗案被贬黄州，写前后《赤壁赋》，《定风波》“一蓑烟雨任平生” | evidence-bank 苏轼条（见 assets/evidence-audit.json） | — | bank | verified(bank) | 5 | 角度：逆境中的精神自由；"没有人替他安排"为推断性修辞 |
| E8 | 常识事件 | "一场突如其来的疫情" | 无（不写年份、数字） | — | — | weakened | 1 | 只作现象，不含可核验细节 |
| E9 | 审题校准 | 本题为2020年上海高考真题 | https://www.shmeea.edu.cn/page/08000/20200707/14229.html | 专家点评：“事物发展进程”可小可大，指向"客观性、规律性和个体主观能动性" | T1 | verified | — | 仅校准，未照搬 |

## 闸门
- [x] claims 抽取项（1928/1854/1929/1939/1945、赤壁赋、一蓑烟雨任平生）均有行；C1（预见转折何时发生）、C3/C4/C9/C12 为误报
- [x] 无 dropped 残留（本篇无 dropped 行）
- [x] paraphrase-only（E6）无引号
- [x] 无仅T3事实
- [x] 强度≤来源（E2/E3 已降级）
- [x] evidence-bank 外新增案例1个（弗莱明）≤2
