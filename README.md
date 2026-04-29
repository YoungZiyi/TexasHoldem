# Texas Hold'em ♠️♥️♦️♣️

一个纯 Web 技术栈的德州扑克游戏，无需数据库，适合朋友间联机娱乐。

## 功能特性

- 🎮 **创建/加入房间**：输入名字即可创建房间，分享 6 位房间号邀请好友
- 🔄 **断线重连**：游戏进行中刷新页面或断线，用相同名字重新加入即可接管原身份
- 🃏 **完整牌局流程**：翻牌前 → 翻牌圈 → 转牌圈 → 河牌圈 → 摊牌比大小
- 💰 **标准德州规则**：大小盲注、跟注、加注、过牌、弃牌、All-in
- 🏆 **边池分配**：支持多玩家 All-in 时的边池（Side Pot）正确计算
- 🔄 **自动循环**：每局结束 6 秒后自动开始下一局，筹码归零可重新买入
- 📱 **多端适配**：支持桌面浏览器和手机浏览器，响应式界面

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端 | 原生 HTML + CSS + JavaScript | 零框架依赖，单页应用 |
| 后端 | Node.js + `ws` | 唯一外部依赖，WebSocket 实时通信 |
| 状态 | 内存存储 | 无数据库，房间状态保存在服务端内存 |

## 部署

### 环境要求

- Node.js 18+

### 快速启动

```bash
# 克隆仓库
git clone git@github.com:YoungZiyi/TexasHoldem.git
cd TexasHoldem

# 安装依赖（仅 ws 一个包）
npm install

# 启动服务
node server.js
```

默认监听 `3000` 端口，访问 `http://localhost:3000` 即可游玩。

### 生产环境部署

**使用 PM2 常驻运行：**

```bash
npm install -g pm2
pm2 start server.js --name texas-poker
pm2 save
pm2 startup
```

**配合 Nginx 反向代理（可选）：**

```nginx
server {
    listen 80;
    server_name poker.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 使用指南

### 开始游戏

1. 打开浏览器访问游戏地址
2. 输入你的名字，点击**创建房间**
3. 将生成的 6 位房间号（如 `A3B7C9`）发给朋友
4. 朋友输入名字和房间号，点击**加入房间**
5. 房主点击**开始游戏**

### 操作说明

| 按钮 | 说明 |
|------|------|
| **弃牌** | 放弃本局，不再参与本轮下注 |
| **过牌** | 不下注，轮到你且无人加注时可用 |
| **跟注** | 跟入当前最高下注额以继续参与 |
| **加注** | 输入金额，提高当前下注额 |
| **全下** | 押上所有剩余筹码 |

### 断线重连

如果游戏过程中刷新页面或网络断开，重新进入游戏后：
1. 输入**相同的名字**
2. 输入原来的**房间号**
3. 点击**加入房间**
4. 系统会自动接管你之前的身份和状态

### 重新买入

当筹码归零时，在房间等待界面会显示**重新买入**按钮，点击后恢复为 1000 筹码。

## 项目结构

```
TexasHoldem/
├── server.js          # 服务端：WebSocket 服务 + 德州扑克游戏逻辑
├── package.json       # 项目配置
├── .gitignore         # Git 忽略规则
├── README.md          # 本文档
└── public/
    └── index.html     # 前端：牌桌 UI、交互逻辑、WebSocket 客户端
```

## 注意事项

- 服务端无持久化存储，重启服务后所有房间数据会丢失
- 建议 2~9 人游戏，体验最佳
- 所有状态保存在服务端内存中，不适合大规模公开部署
- 手机游玩时建议保持屏幕常亮，避免锁屏断连

## License

MIT
