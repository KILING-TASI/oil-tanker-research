# 油运行业研究 Skill

从运输供需、有效运力和航线运价，分析油运公司的盈利、现金流与估值。按问题选择研究深度，独立核对事实，再组织综合判断。

[下载v0.1.0安装包](https://github.com/KILING-TASI/oil-tanker-research/releases/tag/v0.1.0) · [Skill入口](skill/SKILL.md) · [研究框架](skill/references/research-framework.md) · [在线介绍](https://kiling-tasi.github.io/oil-tanker-research/) · [MIT](LICENSE)

## 使用

将完整`skill`目录复制到所用助手的Skill目录，并命名为`oil-tanker-research`，按助手规则加载。调用示例：

> 使用 $oil-tanker-research 分析油运景气变化如何影响一家公司的盈利，区分已披露事实、情景假设与未知资料。

适用于行业景气判断、公司比较、盈利与估值情景、用户资料复核。文字研究无需Python；不默认依赖其他仓库、数据库账号或作者缓存。Skill没有内置联网采集器，不执行交易。

## 最短离线验证

需要Python 3.10+，计算脚本使用标准库。在仓库根目录运行：

```console
python skill/scripts/research_checks.py --input skill/examples/earnings-scenario.json
```

合成示例应输出税前机械增量10,500,000元、税后机械增量7,875,000元及`sourceVerified: false`。这不是实际公司数据或净利润预测。在已安装Skill目录运行时省略路径前面的`skill/`。

## 研究与工具

- [行业框架](skill/references/research-framework.md)：供需 → 运价 → 公司兑现 → 估值与情景。
- [数据字典](skill/references/data-dictionary.md)与[来源边界](skill/references/data-sources.md)：指标、期间、定义与来源定位。
- [计算契约](skill/references/calculation-contracts.md)：浮舱成本、集合去重、TCE增量与分位。
- [证据核对契约](skill/references/evidence-contracts.md)：期间、航线、公司身份、敞口及有基准的运价反推。
- [研究简报模板](skill/assets/research-brief.md)：事实、计算和判断分开记录，按问题删减。

脚本只检查声明输入；运行成功不认证来源或投资结论。HTML静态语法检查另需Node.js，通过不替代浏览器验收。

## 打包与验证

```console
python tools/package_skill.py --output oil-tanker-research-skill.zip
python -m unittest discover -s tests -v
```

独立包包含中文调用入口、全部引用与脚本、合成示例、许可证和SHA256清单。解压后的`oil-tanker-research`目录可按助手规则安装。打包工具拒绝覆盖已有文件。当前检查范围见[VALIDATION.md](VALIDATION.md)。

原创代码及模板采用MIT；第三方公告、研报、数据和代码保留各自权利范围，见[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

## 公开底稿验收

[覆盖登记](PUBLIC_VALIDATION.json)区分公开事实、混合教学与尚缺样本。运行 `python tools/verify_public_validation.py --run-checks --output reports/public-validation-v1.json` 可核对冻结文本与已登记反例；重复运行使用新文件。通过不表示重新认证原文或真实市场效果，未取得的样本仍列为缺口。
