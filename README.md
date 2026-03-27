# qdfy-platform-push

OpenClaw Skill：接收青蝶飞云协作平台推送的通知和问卷消息。

## 架构

```
协作平台（后端）
  └─ 发通知/问卷 → 写入用户消息队列
                              ↑  每 30 秒轮询
                     OpenClaw Skill
                              ↓  有消息时
                     在独立会话中展示
```

服务器 **无需**主动连接微信/iLink/第三方服务，完全由 Skill 主动拉取。

---

## 安装方式

### 方式 A：在 OpenClaw 中导入 Skill（推荐）

1. 打开 OpenClaw → Skill 管理 → 导入
2. 填入本仓库地址：`https://github.com/qd213618/qdfy-platform-push`
3. 安装后进入 Skill 设置，填入：
   - **服务器地址**：`https://your-server.com:8765`（协作平台地址）
   - **Push Token**：见下方「获取 Push Token」

### 方式 B：独立 Python 脚本（不依赖 OpenClaw Skill 系统）

```bash
pip install requests
python poller.py --server https://your-server.com:8765 --token pk_xxxxxx
```

---

## 获取 Push Token

1. 用浏览器打开协作平台，登录账号
2. 进入 `/platform` → 点击顶部「📡 OpenClaw 推送」标签页
3. 点击 **「生成 / 重新生成 Token」**，复制 Token（格式：`pk_xxxxxxxxxxxxxxxx`）
4. 将 Token 粘贴到 Skill 配置的 **Push Token** 字段

> ⚠️ Token 是个人身份凭证，请勿分享给他人。重新生成后旧 Token 立即失效。

---

## 验证连通

配置完成后，回到平台 `/platform → OpenClaw 推送` 页面，点击 **「📨 投入测试消息」**。

等待约 30 秒（一个轮询周期），OpenClaw 应收到测试消息并在推送会话中显示。

---

## API 说明

Skill 使用的唯一接口：

```
GET {server_url}/api/push/poll
Header: X-Push-Token: pk_xxxxxx

Response:
{
  "messages": [
    {
      "id": "uuid",
      "type": "notification" | "survey" | "test",
      "title": "消息标题",
      "content": "消息正文（最多 300 字）",
      "url": "/notifications",   // 相对路径，用于跳转到平台详情页
      "queued_at": "2026-03-27T10:00:00"
    }
  ],
  "count": 1,
  "user_name": "张医生"
}
```

- 成功拉取后队列自动清空（消息不会重复下发）
- Token 无效时返回 `401`，Skill 会停止轮询并提示重新配置

---

## 自定义消息格式

编辑 `poller.py` 中的 `MSG_TEMPLATES` 和 `_deliver` 函数，可自定义消息展示方式（如调用 OpenClaw 内部 API 创建特定格式的会话消息）。

---

## License

MIT
