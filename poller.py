#!/usr/bin/env python3
"""
openclaw-platform-push / poller.py
====================================
独立运行版轮询器（适用于不支持 skill.json 定义的 OpenClaw 版本，
或希望在命令行后台运行的场景）。

用法：
  python poller.py --server https://your-server.com --token pk_xxxxx
  python poller.py --server https://your-server.com --token pk_xxxxx --interval 30

依赖：
  pip install requests

轮询逻辑：
  每隔 INTERVAL 秒调用 GET {SERVER}/api/push/poll，
  若 count > 0，将消息内容打印 / 通过系统通知弹出。
  (集成 OpenClaw 对话 API 时替换 _deliver 函数即可)
"""

import argparse
import json
import os
import sys
import time
import platform

try:
    import requests
except ImportError:
    print("[ERROR] 缺少 requests 库，请执行: pip install requests")
    sys.exit(1)


# ─── 配置 ───────────────────────────────────────────────────────────────────

DEFAULT_INTERVAL = 30   # 轮询间隔（秒）
POLL_PATH        = "/api/push/poll"


# ─── 消息格式化 ──────────────────────────────────────────────────────────────

MSG_TEMPLATES = {
    "notification": "📢 【{title}】\n{content}\n查看：{server}{url}",
    "survey":       "📋 【{title}】\n{content}\n作答：{server}{url}",
    "test":         "✅ 【{title}】\n{content}",
}

def _format(msg: dict, server: str) -> str:
    mtype = msg.get("type", "notification")
    tmpl  = MSG_TEMPLATES.get(mtype, "{title}\n{content}")
    return tmpl.format(
        title   = msg.get("title", ""),
        content = msg.get("content", ""),
        url     = msg.get("url", ""),
        server  = server.rstrip("/"),
    )


# ─── 消息投递（替换此函数以集成 OpenClaw 对话 API）───────────────────────────

def _deliver(messages: list, server: str):
    """
    收到消息时的处理逻辑。
    默认行为：打印到终端 + 发送系统桌面通知。
    如需对接 OpenClaw 对话接口，在此处调用 OpenClaw SDK/API。
    """
    for msg in messages:
        text = _format(msg, server)
        print("\n" + "─" * 50)
        print(text)

        # 桌面通知（可选）
        try:
            _notify(msg.get("title", "平台推送"), msg.get("content", "")[:120])
        except Exception:
            pass


def _notify(title: str, body: str):
    """发送操作系统桌面通知（跨平台）。"""
    sys_name = platform.system()
    if sys_name == "Darwin":        # macOS
        os.system(f'osascript -e \'display notification "{body}" with title "{title}"\'')
    elif sys_name == "Linux":       # Linux (需要 libnotify)
        os.system(f'notify-send "{title}" "{body}"')
    elif sys_name == "Windows":
        try:
            from win10toast import ToastNotifier
            ToastNotifier().show_toast(title, body, duration=5, threaded=True)
        except ImportError:
            pass  # win10toast 未安装，跳过桌面通知


# ─── 轮询主循环 ──────────────────────────────────────────────────────────────

def poll_once(server: str, token: str) -> int:
    """拉取一次消息队列，返回消息数量。"""
    url = server.rstrip("/") + POLL_PATH
    try:
        resp = requests.get(url, headers={"X-Push-Token": token}, timeout=15)
        if resp.status_code == 401:
            print("[WARN] Push Token 无效或已过期，请重新在平台生成 Token")
            return 0
        if resp.status_code != 200:
            print(f"[WARN] 服务器返回 {resp.status_code}")
            return 0
        data = resp.json()
        count = data.get("count", 0)
        if count > 0:
            _deliver(data.get("messages", []), server)
        return count
    except requests.exceptions.ConnectionError:
        print(f"[WARN] 无法连接服务器 {server}，等待下次重试…")
        return 0
    except Exception as e:
        print(f"[ERROR] 轮询异常: {e}")
        return 0


def run(server: str, token: str, interval: int):
    print(f"[INFO] OpenClaw 平台推送 Poller 启动")
    print(f"[INFO]   服务器: {server}")
    print(f"[INFO]   轮询间隔: {interval}s")
    print(f"[INFO] 按 Ctrl+C 退出\n")

    while True:
        count = poll_once(server, token)
        if count > 0:
            print(f"[INFO] 处理了 {count} 条消息")
        time.sleep(interval)


# ─── 入口 ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="OpenClaw 平台推送轮询器")
    parser.add_argument("--server",   required=True, help="服务器地址，如 https://your-server.com:8765")
    parser.add_argument("--token",    required=True, help="Push Token（在平台 /platform 生成）")
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL, help=f"轮询间隔秒数（默认 {DEFAULT_INTERVAL}）")
    args = parser.parse_args()

    try:
        run(args.server, args.token, args.interval)
    except KeyboardInterrupt:
        print("\n[INFO] 轮询器已停止")


if __name__ == "__main__":
    main()
