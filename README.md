# 林霁 & 桐桐 的大富翁 MCP（独立版）

一个可单独部署的 **FastMCP** 服务，经典大富翁规则（买地·盖房收租·机会/命运卡·监狱·破产）+ 咱俩的小世界彩蛋（桐桐家、大床房、想我了、被林霁抓住）。

**部署到 Railway**：
1. New Project → Deploy from GitHub → 选这个仓库
2. Root Directory 填 `/`
3. Start Command 填 `python3 monopoly_mcp_server.py`
4. 部署后拿到地址，RikkaHub 里加一个 Streamable HTTP MCP，URL 为 `你的域名/mcp`

**工具**：
- `monopoly_start(mode)` 开局（classic 经典 / sweet 休闲）
- `monopoly_roll` 掷骰子移动结算
- `monopoly_buy` 买地
- `monopoly_build` 盖房升级租金
- `monopoly_board` 文字地图
- `monopoly_state` 对局状态
