.PHONY: start stop restart status logs cert clean

# 默认目标
all: start

# 生成自签名 SSL 证书（用于 HTTPS 语音聊天）
cert:
	@mkdir -p ssl
	@openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
		-keyout ssl/server.key \
		-out ssl/server.crt \
		-subj "/CN=42.193.226.138" \
		-addext "subjectAltName=IP:42.193.226.138"
	@echo "✅ Self-signed certificate generated in ssl/"

# 安装依赖
deps:
	npm install

# 启动服务（PM2 常驻）
start:
	@pm2 start server.js --name texas-poker 2>/dev/null || pm2 restart texas-poker
	@echo "✅ Service started: https://<your-ip>:4000"

# 停止服务
stop:
	@pm2 stop texas-poker
	@echo "✅ Service stopped"

# 重启服务
restart:
	@pm2 restart texas-poker
	@echo "✅ Service restarted"

# 查看状态
status:
	@pm2 status texas-poker

# 查看日志
logs:
	@pm2 logs texas-poker --lines 100

# 彻底删除服务
clean:
	@pm2 delete texas-poker 2>/dev/null || true
	@echo "✅ Service removed from PM2"
