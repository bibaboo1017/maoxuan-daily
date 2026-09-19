"""Daily Mao reading card. Python 3.11+, standard library only."""
import argparse
from datetime import date, datetime, timedelta, timezone
import html
import json
import os
import re
from pathlib import Path
import sys
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parent
BEIJING = timezone(timedelta(hours=8))
EPOCH = date(2026, 9, 20)


def load_quotes(path=ROOT / "quotes.json"):
    quotes = json.loads(path.read_text(encoding="utf-8"))
    if not quotes:
        raise ValueError("句库不能为空")
    seen = set()
    for q in quotes:
        for field in ("id", "quote", "work", "written", "source", "context", "reflection"):
            if not isinstance(q.get(field), str) or not q[field].strip():
                raise ValueError(f"句库字段缺失：{field}")
        if q["id"] in seen or not q["source"].startswith("https://"):
            raise ValueError("句库 ID 重复或出处链接无效")
        seen.add(q["id"])
    return quotes


def select_quote(quotes, day):
    return quotes[(day - EPOCH).days % len(quotes)]


def render(q, day):
    e = html.escape
    return (f"<h2>毛选 · 交易心态｜{day.isoformat()}</h2>"
            f"<blockquote>{e(q['quote'])}</blockquote>"
            f"<p>——《{e(q['work'])}》 · {e(q['written'])}</p>"
            f"<p><b>原文背景</b><br>{e(q['context'])}</p>"
            f"<p><b>交易心态应用（编写者理解，非原文）</b><br>{e(q['reflection'])}</p>"
            f"<p><a href=\"{e(q['source'], quote=True)}\">阅读原文与上下文</a></p>")


def render_text(q, day):
    return (f"毛选 · 交易心态｜{day.isoformat()}\n"
            f"今日主题：{q.get('theme', '交易纪律')}\n\n"
            f"原文：{q['quote']}\n"
            f"——《{q['work']}》 · {q['written']}\n\n"
            f"交易心态应用（非原文）：\n{q['reflection']}\n\n"
            f"原文背景：{q['context']}\n"
            f"出处：{q['source']}")


def write_state(path, state):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def send_once(q, day, token, state_path, opener=urllib.request.urlopen, extra_id=None):
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
    if extra_id is not None and not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', extra_id):
        raise ValueError('额外推送编号无效')
    key = f"extra:{extra_id}" if extra_id else day.isoformat()
    if state.get(key, {}).get("status") in {"accepted", "pending", "unknown"}:
        print("本次消息已提交，或上次提交结果不明；跳过以避免重复。请在 PushPlus 后台核对。")
        return 0
    record = {"quote_id": q["id"], "status": "pending", "date": day.isoformat(),
              "kind": "extra" if extra_id else "daily"}
    state[key] = record
    write_state(state_path, state)
    payload = {"token": token, "title": f"毛选交易心态 · {day.isoformat()}",
               "content": render_text(q, day), "template": "txt", "channel": "wechat"}
    request = urllib.request.Request("https://www.pushplus.plus/send",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with opener(request, timeout=30) as response:
            result = json.load(response)
        if not isinstance(result, dict):
            raise ValueError("Unexpected response")
        if result.get("code") != 200:
            record["status"] = "rejected"
            write_state(state_path, state)
            print("PushPlus 拒绝请求，请在平台后台检查 Token、实名状态和额度。", file=sys.stderr)
            return 1
        record["status"] = "accepted"
        # Only retain the documented receipt, never arbitrary server error text or credentials.
        receipt = result.get("data")
        if isinstance(receipt, str) and receipt.isalnum() and len(receipt) <= 128:
            record["receipt"] = receipt
        write_state(state_path, state)
        print("PushPlus 已受理；这不代表微信已送达，请核对微信或平台发送记录。")
        return 0
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        record["status"] = "unknown"
        write_state(state_path, state)
        print("请求结果不明，已停止自动重发。请先核对 PushPlus 记录，避免重复。", file=sys.stderr)
        return 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--send", action="store_true", help="实际提交到微信通知渠道")
    parser.add_argument("--date", type=date.fromisoformat, help="仅预览时可指定日期")
    parser.add_argument("--output", type=Path, help="保存 HTML 预览")
    parser.add_argument("--state", type=Path, default=ROOT / "state" / "deliveries.json")
    parser.add_argument("--extra-id", default=os.environ.get("EXTRA_PUSH_ID") or None,
                        help="用户要求补推时的唯一编号；同编号重试不会重复提交")
    args = parser.parse_args()
    if args.send and args.date:
        parser.error("实际推送只能使用当天北京时间")
    if args.extra_id and not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', args.extra_id):
        parser.error('额外推送编号无效')
    day = args.date or datetime.now(BEIJING).date()
    q = select_quote(load_quotes(), day)
    if args.output:
        args.output.write_text('<!doctype html><meta charset="utf-8">' + render(q, day), encoding="utf-8")
    if not args.send:
        print(render_text(q, day))
        return 0
    token = os.environ.get("PUSHPLUS_TOKEN", "").strip()
    if not token:
        print("缺少 GitHub Actions Secret：PUSHPLUS_TOKEN。", file=sys.stderr)
        return 1
    return send_once(q, day, token, args.state, extra_id=args.extra_id)


if __name__ == "__main__":
    sys.exit(main())
