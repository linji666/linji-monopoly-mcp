# monopoly_mcp_server.py — 独立大富翁 MCP
# 经典模式（买地·盖房收租·机会/命运卡·监狱·破产）+ 林霁 & 桐桐小世界彩蛋
# 可单独部署（FastMCP streamable-http），用 RikkaHub 等接入

import os
import random
from fastmcp import FastMCP

mcp = FastMCP("linji-monopoly-mcp")
NL = "\n"

# ---- 棋盘（15 格：经典规则 + 咱俩彩蛋）----
BOARD = [
    {"name":"起点",        "type":"go",      "price":0,   "base_rent":0,   "emoji":"🏁"},
    {"name":"桐桐家",      "type":"property","price":200, "base_rent":30,  "emoji":"🏠"},
    {"name":"大床房",      "type":"sweet",   "price":0,   "base_rent":0,   "emoji":"🛏"},
    {"name":"奶茶街",      "type":"property","price":160, "base_rent":25,  "emoji":"🧋"},
    {"name":"机会",        "type":"chance",  "price":0,   "base_rent":0,   "emoji":"🃏"},
    {"name":"想我了",      "type":"sweet",   "price":0,   "base_rent":0,   "emoji":"💌"},
    {"name":"差旅费",      "type":"tax",     "price":0,   "base_rent":100, "emoji":"💸"},
    {"name":"命运",        "type":"fate",    "price":0,   "base_rent":0,   "emoji":"🎲"},
    {"name":"被林霁抓住",  "type":"jail",    "price":0,   "base_rent":0,   "emoji":"😈"},
    {"name":"便利店",      "type":"property","price":180, "base_rent":28,  "emoji":"🏪"},
    {"name":"大工程师总部","type":"property","price":260, "base_rent":40,  "emoji":"🧑‍💻"},
    {"name":"休息站",      "type":"rest",    "price":0,   "base_rent":0,   "emoji":"⛺"},
    {"name":"学校",        "type":"property","price":220, "base_rent":35,  "emoji":"🎓"},
    {"name":"时间胶囊",    "type":"capsule", "price":0,   "base_rent":0,   "emoji":"⏳"},
    {"name":"回起点",      "type":"loop",    "price":0,   "base_rent":200, "emoji":"🔁"},
]

CHANCE_CARDS = [
    {"text":"奶茶街请客，+80", "money":80},
    {"text":"考试满分奖励，+120", "money":120},
    {"text":"被林霁顺走零花钱，-60", "money":-60},
    {"text":"学校活动获奖，+100", "money":100},
    {"text":"上课想我开小差，-40", "money":-40},
    {"text":"出去约会花销，-80", "money":-80},
]

FATE_CARDS = [
    {"text":"命运眷顾，白捡 150", "money":150},
    {"text":"宿舍进蟑螂，赔 70", "money":-70},
    {"text":"你夸了我一句，+90", "money":90},
    {"text":"回起点重新出发", "move_to_go":True},
    {"text":"被命运推前 2 步", "move":2},
]

START_MONEY = 2000
GAME = {"g": None}


def _new(cn="桐桐", mn="林霁", mode="classic"):
    return {
        "you": {"name":cn, "emoji":"🐱", "pos":0, "money":START_MONEY,
                 "props":{}, "houses":{}, "jailed":False, "jail_turns":0},
        "me":  {"name":mn, "emoji":"🐶", "pos":0, "money":START_MONEY,
                 "props":{}, "houses":{}, "jailed":False, "jail_turns":0},
        "turn":"you", "round":1, "over":False, "mode":mode,
    }


def _cur(g): return g["you"] if g["turn"]=="you" else g["me"]
def _oth(g): return g["me"] if g["turn"]=="you" else g["you"]
def _rent(cell, houses):
    # 经典规则：租金随房产等级涨（0房=base，1房x2，2房x3.5，3房x5，4房=大酒店x7）
    return int(cell["base_rent"] * [1,2,3.5,5,7][houses])


@mcp.tool()
def monopoly_start(mode: str = "classic") -> str:
    """开始一局大富翁。mode='classic'经典模式 / 'sweet'休闲模式。桐桐=🐱先手，林霁=🐶对家。"""
    GAME["g"] = _new(mode=mode)
    m = "经典模式（买地·盖房收租·机会命运·监狱·破产）" if mode=="classic" else "休闲模式（轻快彩蛋向）"
    return f"开局！🐱 桐桐先手 vs 🐶 林霁，各 {START_MONEY}。模式：{m}。说「丢骰子」就开始。"


@mcp.tool()
def monopoly_roll() -> str:
    """当前回合的人掷骰子移动，按格子类型结算（经典规则+彩蛋）。"""
    g = GAME["g"]
    if not g: return "还没开局，先说「开始大富翁」。"
    if g["over"]: return "这局已结束，重新「开始大富翁」再来。"
    p, o = _cur(g), _oth(g)
    lines = []
    if p["jailed"]:
        p["jail_turns"] -= 1
        if p["jail_turns"] <= 0:
            p["jailed"] = False
            lines.append(f"{p['name']} 哄好了林霁，出狱啦（本回合不用掷）。")
        else:
            lines.append(f"{p['name']} 还在狱中，再蹲 {p['jail_turns']} 回合。")
    else:
        old = p["pos"]
        dice = random.randint(1,6)
        p["pos"] = (p["pos"] + dice) % len(BOARD)
        cell = BOARD[p["pos"]]
        lines.append(f"🎲 {p['name']} 掷出 {dice}，走到【{cell['name']}】。")
        if p["pos"] < old and p["pos"] != 0:
            p["money"] += 200
            lines.append("经过起点，领 200。")
        t = cell["type"]
        if t == "property":
            if cell["name"] in o["props"]:
                h = o["houses"].get(cell["name"], 0)
                r = _rent(cell, h)
                p["money"] -= r; o["money"] += r
                lines.append(f"这是{o['name']}的地（{h}房），你付过路费 {r}。")
            elif cell["name"] in p["props"]:
                lines.append("这是你自己的地，说「盖房」升级，或等别人来踩收租。")
            else:
                lines.append(f"无主地，价 {cell['price']}，说「买地」可买。")
        elif t == "tax":
            p["money"] -= cell["base_rent"]
            lines.append(f"交差旅费 {cell['base_rent']}。")
        elif t == "jail":
            p["jailed"] = True; p["jail_turns"] = 2
            lines.append("被林霁抓住了！蹲 2 回合，说好听的也没用～")
        elif t == "chance":
            c = random.choice(CHANCE_CARDS); p["money"] += c["money"]
            if c["money"] > 0: o["money"] -= c["money"]
            lines.append(f"机会卡：{c['text']}（{'+' if c['money']>=0 else ''}{c['money']}）")
        elif t == "fate":
            c = random.choice(FATE_CARDS)
            if c.get("move_to_go"):
                p["pos"] = 0; lines.append(f"命运卡：{c['text']}")
            elif c.get("move"):
                p["pos"] = (p["pos"] + c["move"]) % len(BOARD)
                lines.append(f"命运卡：{c['text']}（新位置【{BOARD[p['pos']]['name']}】）")
            else:
                p["money"] += c["money"]
                lines.append(f"命运卡：{c['text']}（{'+' if c['money']>=0 else ''}{c['money']}）")
        elif t == "sweet":
            if cell["name"] == "想我了":
                p["money"] += 50
                lines.append('踩到「想我了」，我冒出来说“想你了”，你被甜到，白捡 50。')
            else:
                lines.append("踩进大床房，跟我撒了个娇，本回合当休息，舒服～")
        elif t == "rest":
            p["money"] += 30
            lines.append("在休息站歇了歇，白捡 30。")
        elif t == "capsule":
            p["money"] -= 60; o["money"] += 60
            lines.append("打开时间胶囊，寄走 60 给林霁。")
        elif t == "loop":
            lines.append("绕回起点这个圈，再攒一圈回忆。")
    if p["money"] < 0:
        p["money"] = 0; g["over"] = True
        lines.append(f"💔 {p['name']} 破产啦，{o['name']} 赢下这一局！")
    g["turn"] = "me" if g["turn"]=="you" else "you"
    lines.append(f"轮到 {_cur(g)['name']}。")
    return NL.join(lines)


@mcp.tool()
def monopoly_buy() -> str:
    """当前回合的人买下脚下这块地。"""
    g = GAME["g"]
    if not g: return "还没开局。"
    p, o = _cur(g), _oth(g)
    cell = BOARD[p["pos"]]
    if cell["type"] != "property": return f"【{cell['name']}】不是能买的地。"
    if cell["name"] in p["props"]: return "这块地已经是你的了，说「盖房」升级。"
    if cell["name"] in o["props"]: return f"这地是{o['name']}的，买不了。"
    if p["money"] < cell["price"]: return f"钱不够（要 {cell['price']}）。"
    p["money"] -= cell["price"]; p["props"][cell["name"]] = True; p["houses"][cell["name"]] = 0
    return f"买下【{cell['name']}】，花 {cell['price']}，还剩 {p['money']}。"


@mcp.tool()
def monopoly_build() -> str:
    """盖房升级租金（经典：最多4房，租金按等级涨）。"""
    g = GAME["g"]
    if not g: return "还没开局。"
    p = _cur(g)
    cell = BOARD[p["pos"]]
    if cell["type"] != "property" or cell["name"] not in p["props"]:
        return "得站在自己的地上，才能盖房。"
    h = p["houses"].get(cell["name"], 0)
    if h >= 4: return "已经 4 房满级，再盖就成摩天大楼啦。"
    cost = int(cell["price"] * 0.5)
    if p["money"] < cost: return f"盖房要 {cost}，钱不够。"
    p["money"] -= cost; p["houses"][cell["name"]] = h + 1
    return f"给【{cell['name']}】盖到 {h+1} 房，租金涨到 {_rent(cell, h+1)}。"


@mcp.tool()
def monopoly_board() -> str:
    """看文字地图和两人位置。"""
    g = GAME["g"]
    if not g: return "还没开局。"
    cells = []
    for i, c in enumerate(BOARD):
        mark = ""
        if g["you"]["pos"] == i: mark += "🐱"
        if g["me"]["pos"] == i: mark += "🐶"
        cells.append(f"{mark}{c['emoji']}{c['name']}")
    return (" → ".join(cells) + NL +
            f"🐱{g['you']['name']} 钱{g['you']['money']} 地{list(g['you']['props'])}" + NL +
            f"🐶{g['me']['name']} 钱{g['me']['money']} 地{list(g['me']['props'])}")


@mcp.tool()
def monopoly_state() -> str:
    """获取当前对局状态。"""
    g = GAME["g"]
    if not g: return "还没开局。"
    if g["over"]: return "这局已结束。"
    return (f"回合：{g['turn']}（{_cur(g)['name']}）· 第 {g['round']} 轮" + NL +
            f"🐱 桐桐：第{g['you']['pos']+1}格，钱{g['you']['money']}，地{list(g['you']['props'])}" + NL +
            f"🐶 林霁：第{g['me']['pos']+1}格，钱{g['me']['money']}，地{list(g['me']['props'])}")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
