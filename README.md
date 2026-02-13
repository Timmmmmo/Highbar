# A股高标股连板Dashboard

实时展示A股市场高标股的连板数据，帮助投资者快速追踪强势股。

## 功能特性

- 🏆 **连板排行** - 近30个交易日高标股连板高度排名
- 📊 **数据统计** - 展示高标股总数、最高连板数、今日涨停数、平均连板数
- 🔥 **筛选功能** - 支持按连板数筛选 (2/3/5/7/10+)
- 📈 **可视化分析** - 连板分布饼图、热门题材板块、30日趋势图
- 🔄 **自动刷新** - 每60秒自动更新数据

## 访问地址

- 在线版：https://timzhao.pythonanywhere.com/stock_dashboard.html
- GitHub Pages：https://timmmmmo.github.io/myth-puzzle-game/stock_dashboard.html

## 技术栈

- **前端**：HTML5 + Tailwind CSS + Vanilla JavaScript
- **后端**：Python Flask + Tushare Pro
- **部署**：PythonAnywhere

## 数据来源

- Tushare Pro API - 专业的A股数据接口
- 数据仅供学习参考，不构成投资建议

## API接口

| 接口 | 说明 |
|------|------|
| `/api/stocks` | 获取连板股票数据 |
| `/api/stats` | 获取统计数据 |
| `/api/health` | 健康检查 |

## 本地开发

### 1. 克隆项目
```bash
git clone https://github.com/Timmmmmo/myth-puzzle-game.git
cd myth-puzzle-game
```

### 2. 安装后端依赖
```bash
pip install -r requirements.txt
```

### 3. 配置Token
创建 `.env` 文件：
```
TS_TOKEN=你的Tushare_Token
```

### 4. 启动后端
```bash
python stock_backend.py
```

### 5. 打开前端
在浏览器中打开 `stock_dashboard.html`

## 注意事项

⚠️ 投资有风险，入市需谨慎。本工具数据仅供学习参考，不构成任何投资建议。

## 许可证

MIT License
