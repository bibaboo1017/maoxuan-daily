# 毛选 · 每日微信金句

按北京时间每天早上 8 点触发 GitHub Actions，通过 PushPlus 微信公众号渠道发送一条原文节选、篇名、写作日期、背景、简短解读和原文链接。电脑关机也可运行。GitHub 排队及通知平台处理可能造成延迟，不能保证 08:00 准点收到。

**当前交付的是经过本地测试的待部署版本，尚未接入微信或启动云端定时任务。**

## 首次配置

1. 在 [PushPlus](https://www.pushplus.plus/) 登录，按平台指引关注并绑定微信，完成其当前要求的实名认证，在个人中心取得发送 Token。无需把 Token 发给聊天助手。
2. 创建 GitHub 私有仓库 `maoxuan-daily`，把本目录内容上传至仓库根目录。务必包含隐藏目录 `.github/workflows/daily.yml`。工作流需位于默认分支。
3. 在仓库 `Settings → Secrets and variables → Actions → New repository secret` 中创建 `PUSHPLUS_TOKEN`，值为你的 Token。不要放进代码、截图或 README。
4. 确认仓库允许 Actions 运行，并允许此工作流写入提交记录。脚本使用 `contents: write` 保存 `state/deliveries.json`。若默认分支禁止机器人直接提交，请先解决该限制，否则防重复记录不能持久保存。
5. 打开仓库 `Actions → 毛选每日微信推送 → Run workflow`，运行一次。检查日志、PushPlus 发送记录和微信接收结果。手动运行也计为当天推送，当天定时运行将跳过。
6. 定时配置是 `0 0 * * *`（UTC），对应北京时间每天 08:00。GitHub 免费额度和计费以你的账户后台为准；该系统不调用付费 AI 接口。

如果创建了私有仓库但助手仍看不到，请在 GitHub 的应用授权中允许当前 GitHub 连接访问该仓库。

## 句库与每日更新

首版内置 **10 条人工核对过在线原文的短句/节选，10 天轮换一次**。这里的每日更新是按北京时间更换当天卡片，不是每日联网生成新金句，也不是永不重复。每条保留来源；解读是编写者理解，并与原文明示区分。在线文本使用中文马克思主义文库所收毛泽东文章，不冒称已逐页核对纸质版本。

扩充时在 `quotes.json` 末尾添加同结构条目，使用唯一 `id`，并核对篇名、日期、逐字原文及上下文。不要把现代改写、其他作者的话或作品引用他人的话误标为毛泽东原创。未标为完整句的内容会在背景中说明节选位置。增加或调整条目会改变按日期计算的轮换顺序。

## 预览与测试

Python 3.11 以上，无第三方依赖。在此目录运行：

```powershell
python daily.py --date 2026-09-20 --output preview.html
python -m unittest discover -s tests -v
```

仅 `python daily.py --send` 会调用发送接口。默认预览不会发送消息。

## 记录与故障处理

- 同一北京时间日期已提交的消息会跳过。正常云端运行通过提交 `state/deliveries.json` 保存记录。
- `accepted` 只表示 PushPlus 受理，不代表微信送达或已读。可用记录中的流水号在平台核查。
- `rejected` 表示平台明确拒绝，修复配置后可手动重跑。
- `pending` / `unknown` 表示结果不确定，程序不会自动重发。先查平台和微信；确认未收到后才删除当天记录并重跑。
- 云端任务终止、保存记录失败或外部平台异常，仍可能造成漏发或重复；本系统不承诺跨平台“恰好一次”。缺失日期不补发，恢复后发送当天内容。
- 工作流失败可在 GitHub Actions 查看，开启 GitHub 的 Actions 失败通知便于发现问题。受理之后的送达失败须查看 PushPlus 记录。
- 停用：在 Actions 中禁用该工作流；解除接入：删除 Secret，必要时在 PushPlus 重置 Token。

## 接口依据

- [PushPlus 消息接口与异步受理说明](https://pushplus.plus/doc/guide/api.html)
- [PushPlus 实名与使用额度](https://pushplus.plus/doc/guide/use.html)
- [GitHub 定时工作流及延迟限制](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)

接口资料核对日期：2026-09-19。平台额度、实名要求和可用渠道可能调整。
