# 油运行业研究

整理原油与成品油海运的供需、运价、公司敞口和估值证据，核对声明假设下的算术，不自动给出买卖建议。

[原创代码 MIT](LICENSE) · [研究与数据权利](THIRD_PARTY_NOTICES.md) · [Skill 使用说明](skill/SKILL.md) · [在线入口](https://kiling-tasi.github.io/oil-tanker-research/) · [网页源码](index.html)

本仓是 **Skill、独立核对脚本和历史报告**，不是已安装的数据服务或完整预测模型。Python **3.10+**；基础脚本无第三方依赖。HTML 内联 JavaScript 语法核对另需 Node.js。当前无 Python 发行包和已核验的 Release 安装包。

## 快速开始

```console
git clone https://github.com/KILING-TASI/oil-tanker-research.git
cd oil-tanker-research
python skill/scripts/research_checks.py --input examples/teaching.json
python -m unittest discover -s tests -v
```

教学输入为原创合成假设。结果列出浮舱成本门槛、船队去重、声明期间 TCE 弹性与经验分位，运行成功不表示实际来源已核实。

用自己的 JSON 资料替换教学字段，可加 `--output 新文件.json` 保存；已有文件会拒绝覆盖。参数和计算边界见 [方法与口径](METHODS.md)。

## 能做什么

| 问题 | 当前支持 | 保留的缺口 |
|---|---|---|
| 运价为何变化 | 五维资料框架、吨海里和船舶周转解释 | 需真实海运量、运距、效率和同口径数据 |
| 老船和受限船是否重复扣减 | 两集合重叠核对；未知重叠给范围 | 艘数不能直接当有效 DWT 或可成交运力 |
| 浮舱价差够不够 | 同期限租船、资金和其他成本情景 | 油种、地点、交割、租约和保险仍需逐案确认 |
| 运价变化对公司意味着什么 | 船数、盈利天数、敞口、汇率与税率的条件桥接 | 不是公司净利润模型；租入船不能一律剔除 |
| PB 在声明样本的位置 | 严格小于的经验分位，列出并列数 | 不认证窗口、历史净资产或估值风险 |
| HTML 是否有明显结构问题 | 嵌套、重复 ID、字面图表目标和逐块 JS 语法 | 不认证浏览器渲染、事实或来源 |

FFA 是现金结算的远期运费合约，报价可用于描述远期定价；单个历史案例不能证明“预测误差稳定小于10%”。PB 也不是唯一风险变量。方法来源见 [METHODS.md](METHODS.md)。

## 报告检查

```console
python skill/scripts/check_report.py skill/assets/dashboard-template.html
```

退出码 **0**：所列静态项目通过；**1**：发现问题；**2**：JavaScript 检查未完成。未安装 Node 或显式使用 `--no-js` 时，不会显示全部通过。`--node` 可指定 Node 路径，`--json-out` 可保存检查记录。

严格嵌套检查针对本仓显式闭合的报告模板；部分合法 HTML 的可省略闭合写法可能被提示，需人工复核。真实报告仍需打开浏览器验收。

## 助手 Skill

将 `skill` 完整目录放到支持本地 Skill 的助手目录，并按该助手规则注册；只复制 SKILL.md 会丢失脚本、模板和引用资料。Skill 名称为 `oil-tanker-research`，不依赖其他研究仓库，不假定任何数据库接口或付费账号已经可用。不执行交易。

## 历史案例

- [2026-10-14 状态仪表盘](油运行业状态仪表盘-20261014.html)
- [2026-10-14 数据拆解](油运行业数据拆解-20261014.html)

两份报告保留旧论证和来源声明，**本轮没有重新取得其全部原文与行情序列**，不应把其中“已核清”“唯一”“不可能”等表述当成当前认证。旧样本、纠错轮次和机构名称不等于预测能力或证据独立性。

旧报告图表使用 ECharts CDN，联网加载失败时保留正文并提示图表不可用；不能称为零网络依赖。新模板不依赖 CDN，提供空白证据表，避免复用时夹带旧结论。

[数据来源与权限](skill/references/data-sources.md) · [数据字典](skill/references/data-dictionary.md) · [历史踩坑记录](skill/references/pitfalls.md) · [本轮验收](VALIDATION.md)
