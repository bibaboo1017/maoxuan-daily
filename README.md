# 毛选 · 交易心态每日提醒

每天北京时间早上 8 点由 GitHub Actions 触发，通过 PushPlus 微信渠道推送。
GitHub 排队可能导致延迟，电脑无需保持开机。

## 内容范围

句库为 quotes.json，10 条轮换，专用于交易心态：独立判断、克服过度自信、
接受市场变化、面对亏损、停止报复性交易、知错能改、耐心等待、尊重验证、
保持谦逊、执行一致。所有毛选原文都附篇名、日期、上下文和链接。
交易应用由编写者另写，原著本身并不讨论股票，不把交易建议冒充毛泽东原话。
不包含个股推荐、买卖价位或收益承诺。每天换一条，10 天重复一次，并非自动联网扩充。

## 微信显示

发送模板已改为 txt 纯文字。默认渠道仍为 wechat。
仅改变模板不会绕过微信平台的展示限制。

在“pushplus 推送加”公众号聊天框发送“激活消息”，可在平台允许的时间窗口内
用客服消息直接展示内容。当前官方文档存在 24 小时与 48 小时两种说法，均限制
连续 5 条，建议按较保守的 24 小时理解。到期需重新激活，实际以平台反馈为准。
无需为此升级会员。

独立微信 ClawBot 对话也可用纯文字，但需要扫码绑定、主动发消息激活，并每
24 小时或收到 10 条消息后再次主动交互。本项目尚未切换到该渠道。

## 配置与运行

仓库 Actions Secret：PUSHPLUS_TOKEN。工作流：.github/workflows/daily.yml。
cron 为 `0 0 * * *`（UTC），即北京时间 08:00。工作流需要 contents: write
权限保存 state/deliveries.json。Token 不要写进源代码或聊天。

Python 3.11 以上，无第三方运行依赖：

```sh
python daily.py --date 2026-09-20 --output preview.html
python -m unittest discover -s tests -v
python daily.py --send
```

只有 --send 调用发送接口。手动运行与定时运行共用当天防重复记录。
accepted 表示平台已受理，不能等同于微信送达。pending/unknown 不自动重发，
须先在平台核对结果。rejected 可在修复配置后重跑。未推送的历史日期不会补发。
任务中断或状态提交失败仍可能导致漏发或重复，不承诺跨平台恰好一次。

## 依据

- [PushPlus 展示说明](https://pushplus.plus/doc/help/showmessage.html)
- [PushPlus 激活说明](https://pushplus.plus/doc/help/activation.html)
- [微信 ClawBot 说明](https://pushplus.plus/doc/channel/clawbot.html)
- [投资者教育：情绪与社交信息风险](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-18)

2026-09-19：已部署并测试首版；句库现限定为交易心态，发送格式调整为纯文字。
