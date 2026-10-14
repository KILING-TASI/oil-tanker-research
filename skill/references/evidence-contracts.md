# 口径与证据攻击检查

运行 `python scripts/evidence_checks.py --input 输入.json`。标准库即可运行，不需要其他仓库。输出 `sourceVerified: false` 是固定边界，程序不替代原文取证。成功退出只代表所列核对完成，结果中的 `blocked` 必须保留，不能包装为研究通过。

根对象至少包含以下一项。CLI遇到缺字段、非法日期、重复来源、非有限数字等输入错误返回1。

- `margin`：`current/prior`各含start/end（ISO日期）、scope、unit、revenue、cost；prior另含restatementStatus（restated或not-required）。必须同范围、同币种、相隔一年同起止月份日。得到的是不含额外税费的简单毛利率，不能识别因果。
- `freight`：asOf；forecast/realized各含start/end、route、vesselBasis、unit、aggregation、benchmark、value；forecast另含quoteDate。报价在未来窗口开始前冻结、窗口已经结束、聚合均为settlement-period-mean且其他字段匹配，才输出一个声明样本的误差。一个样本不认证稳定预测能力。
- `sources`：列表，每项id唯一；可声明parent指向转引来源或originalPublisher指向源头。转载按源头去重，未知源头不计独立数。此处统计声明发布者，不验证数据库上游独立。
- `exposure`：profitWeight/spotWeight各含value（0到1）、population、period、measure。不同分母、期间或度量阻断相乘；匹配也只是机械乘积，不认证真实利润敞口。
- `valuation`：source、netAssetBasis、samplingBasis、asOf、retrievedAt、start/end、currentDate、current、observations（date/value列表）。重复、越界、非有限值和末日不一致拒绝。calendar-daily必须自然日连续完整；vendor-sampled只如实列间隔。返回样本严格小于分位、并列数和实际起止。历史净资产与发布时间需要另外取得，任何声明都不会把pointInTimeCertified改为true。

不要把范围未知填成零，或把转载、原文取得、算术复算、预测和投资结论合并成一个“已核实”。股票代码与公司全称也须核对，不能将中远海能600026与其他中远系公司混淆。身份、来源真伪和真实历史可得性仍须人工证据。

- `identity`：asOf、claim、evidence；两对象各含symbol、start/end、metric、unit、definition、value；evidence另含publishedAt。公司、完整期间、指标、单位及定义必须相同；证据不得晚于研究时点。absoluteTolerance可声明绝对误差（默认0），输出差额，不认证来源。不得把年报贴为半年报，或交换两家分红。未知税费/期间不填写为默认值。

- `profitInverse`：反推运价仅用于有基准的局部情景。target、anchor、sensitivity各声明symbol、start/end、scope、profitDefinition、profitUnit、taxBasis、ownershipBasis且一致；anchor和sensitivity另声明相同route、tceDefinition、tceUnit。target.value为目标利润，sensitivity.value为每1个tceUnit变化对应的profitUnit变化。根对象另含baselineTce、baselineProfit、validTceRange（低/高边界）及otherFactorsHeldConstant=true。计算为基准运价＋（目标利润−基准利润）/系数。基准缺失、未知税费、归属不一、全公司利润配单船型系数或超出局部范围均阻断。通过只代表声明情景可计算，不认证共识、真实保本或可投资性。
