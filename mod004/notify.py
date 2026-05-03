# MOD-004 Telegram 通知模块
import urllib.request, urllib.parse, json

TOKEN = "7989308993:AAG8tSiO9ChTynydtMkvLlEZvPBIgC6DLvM"
CHAT_ID = "6461135333"


def send(msg: str):
    """发送 Telegram 消息"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "HTML",
    }).encode()
    try:
        urllib.request.urlopen(url, data, timeout=10)
        return True
    except Exception as e:
        print(f"Telegram send error: {e}")
        return False


def send_query_result(results: list):
    """发送查询结果摘要"""
    today = __import__('datetime').datetime.now().strftime('%Y-%m-%d')
    lines = [f"<b>🚢 {today} 海运动态</b>\n"]

    ok = [r for r in results if r.success]
    fail = [r for r in results if not r.success]

    for r in ok:
        containers = len(r.containers)
        line = f"✅ <b>{r.carrier}</b> {r.batch_no}: {r.status} | {containers}柜"
        if r.locations:
            line += f" @{r.locations[0]}"
        lines.append(line)

    if fail:
        lines.append(f"\n❌ 失败 {len(fail)} 条")

    lines.append(f"\n<i>Excel 已更新</i>")
    send("\n".join(lines))
