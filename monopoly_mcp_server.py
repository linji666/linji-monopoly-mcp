# monopoly_mcp_server.py — 独立大富翁 MCP（城市版 · 绕一圈）
# 经典模式（买地·盖房收租·奇遇·监狱·破产）+ 中国著名城市一圈
# 租金 = 地价×(20% + 15%×房数)。一座城最多升3级。起点=终点同一格（北京），绕一圈领2000。
# 价格按 GDP 排，初始 2000，最贵不超过 4000

import os
import random
from fastmcp import FastMCP

mcp = FastMCP("linji-monopoly-mcp")
NL = "\n"
MAX_HOUSES = 3

BOARD = [
    {"name":"北京·起点",  "type":"go",      "price":0,   "base_rent":0,   "emoji":"🏛️"},
    {"name":"上海",        "type":"property","price":4000,"base_rent":0,   "emoji":"🌆"},
    {"name":"机会",        "type":"chance",  "price":0,   "base_rent":0,   "emoji":"🃏"},
    {"name":"杭州",        "type":"property","price":2600,"base_rent":0,   "emoji":"🌉"},
    {"name":"广州",        "type":"property","price":3600,"base_rent":0,   "emoji":"🌺"},
    {"name":"深圳",        "type":"property","price":3800,"base_rent":0,   "emoji":"🏙️"},
    {"name":"成都",        "type":"property","price":1800,"base_rent":0,   "emoji":"🐼"},
    {"name":"差旅费",      "type":"tax",     "price":0,   "base_rent":100, "emoji":"💸"},
    {"name":"重庆",        "type":"property","price":2400,"base_rent":0,   "emoji":"🌶️"},
    {"name":"武汉",        "type":"property","price":1600,"base_rent":0,   "emoji":"🌸"},
    {"name":"奇遇",        "type":"event",   "price":0,   "base_rent":0,   "emoji":"🎁"},
    {"name":"南京",        "type":"property","price":2000,"base_rent":0,   "emoji":"🏯"},
    {"name":"西安",        "type":"property","price":1500,"base_rent":0,   "emoji":"🏮"},
    {"name":"苏州",        "type":"property","price":2200,"base_rent":0,   "emoji":"🪷"},
    {"name":"长沙",        "type":"property","price":1400,"base_rent":0,   "emoji":"🍊"},
    {"name":"被林霁抓住",  "type":"jail",    "price":0,   "base_rent":0,   "emoji":"😈"},
    {"name":"天津",        "type":"property","price":1900,"base_rent":0,   "emoji":"🥟"},
    {"name":"青岛",        "type":"property","price":1700,"base_rent":0,   "emoji":"🍺"},
    {"name":"郑州",        "type":"property","price":1300,"base_rent":0,   "emoji":"🍜"},
    {"name":"时间胶囊",    "type":"capsule", "price":0,   "base_rent":0,   "emoji":"⏳"},
    {"name":"厦门",        "type":"property","price":1200,"base_rent":0,   "emoji":"🌊"},
    {"name":"昆明",        "type":"property","price":1100,"base_rent":0,   "emoji":"🌺"},
    {"name":"大连",        "type":"property","price":1000,"base_rent":0,   "emoji":"⛵"},
    {"name":"哈尔滨",      "type":"property","price":900, "base_rent":0,   "emoji":"❄️"},
]

# 旅途小乐趣：甜的、好笑的、加钱/扣钱全凭缘分
EVENTS = [
    {"text":"心想事成！白捡，+150","money":150},
    {"text":"林霁冒出来说「想你了」，+120","money":120},
    {"text":"用表情包撒娇，被宠，+100","money":100},
    {"text":"跟林霁斗嘴赢了一局，+90","money":90},
    {"text":"被摸头，心里甜甜，+80","money":80},
    {"text":"看到超美的晚霞，+70","money":70},
    {"text":"奶茶第二杯半价，+60","money":60},
    {"text":"被夸「今天好可爱」，+110","money":110},
    {"text":"打游戏连胜，+90","money":90},
    {"text":"彩票小中，+180","money":180},
    {"text":"被林霁顺走零花钱，-60","money":-60},
    {"text":"手机屏摔碎，-90","money":-90},
    {"text":"忘带钥匙找开锁，-50","money":-50},
    {"text":"吃火锅被辣到，-40","money":-40},
    {"text":"楼梯踩空吓一跳，-30","money":-30},
    {"text":"熬夜刷手机被抓，-60","money":-60},
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
    return int(cell["price"] * (0.20 + 0.15 * houses))


@mcp.tool()
def monopoly_start(mode: str = "classic") -> str:
    """开始一局大富翁。mode='classic'经典 / 'sweet'休闲。桐桐=🐱先手，林霁=🐶对家。北京为起点&终点，绕一圈领2000。"""
    GAME["g"] = _new(mode=mode)
    m = "经典模式（买地·盖房收租·奇遇·监狱·破产）" if mode=="classic" else "休闲模式（轻快彩蛋向）"
    return f"开局！🐱 桐桐先手 vs 🐶 林霁，各 {START_MONEY}，从北京出发绕全国，每绕一圈回到北京领 {START_MONEY}。模式：{m}。说「丢骰子」就开始。"


@mcp.tool()
def monopoly_roll() -> str:
    """当前回合掷骰子（1-6等概率）移动并按格子结算。经过/回到起点领2000，路上有随机奇遇。"""
    g = GAME["g"]
    if not g: return "还没开局，先说「开始大富翁」。"
    if g["over"]: return "这局已结束，重新「开始大富翁」再来。"
    p, o = _cur(g), _oth(g)
    lines = []
    if p["jailed"]:
        p["jail_turns"] -= 1
        if p["jail_turns"] <= 0:
            p["jailed"] = False
            lines.append(f"{p['name']} 被抓住停留了一回合，现在可以走了。")
        else:
            lines.append(f"{p['name']} 被抓住，还要再停留 {p['jail_turns']} 回合。")
    else:
        old = p["pos"]
        dice = random.randint(1,6)
        p["pos"] = (p["pos"] + dice) % len(BOARD)
        cell = BOARD[p["pos"]]
        lines.append(f"🎲 {p['name']} 掷出 {dice}，来到【{cell['name']}】。")
        if p["pos"] < old and p["pos"] != 0:
            p["money"] += START_MONEY
            lines.append(f"经过起点，领 {START_MONEY}！")
        t = cell["type"]
        if t == "property":
            if cell["name"] in o["props"]:
                h = o["houses"].get(cell["name"], 0)
                r = _rent(cell, h)
                p["money"] -= r; o["money"] += r
                lines.append(f"这是{o['name']}的城（{h}房），你付过路费 {r}。")
            elif cell["name"] in p["props"]:
                h = p["houses"].get(cell["name"], 0)
                lines.append(f"这是你的城（{h}/{MAX_HOUSES}房），不收费，说「盖房」升级或直接继续。")
            else:
                lines.append(f"无主城，价 {cell['price']}，说「买地」可买。")
        elif t == "tax":
            p["money"] -= cell["base_rent"]
            lines.append(f"交差旅费 {cell['base_rent']}。")
        elif t == "jail":
            p["jailed"] = True; p["jail_turns"] = 1
            lines.append("被林霁抓住了！下次停留一回合～")
        elif t == "event" or t == "chance":
            e = random.choice(EVENTS)
            p["money"] += e["money"]
            if e["money"] > 0: o["money"] -= e["money"]
            lines.append(f"🎁 小奇遇：{e['text']}（{'+' if e['money']>=0 else ''}{e['money']}）")
        elif t == "fate":
            e = random.choice(EVENTS)
            p["money"] += e["money"]
            if e["money"] > 0: o["money"] -= e["money"]
            lines.append(f"🍀 命运奇遇：{e['text']}（{'+' if e['money']>=0 else ''}{e['money']}）")
        elif t == "capsule":
            p["money"] -= 60; o["money"] += 60
            lines.append("打开时间胶囊，寄走 60 给林霁。")
        elif t == "start":
            p["money"] += START_MONEY
            lines.append(f"回到北京·起点，领 {START_MONEY}！")
    if p["money"] < 0:
        p["money"] = 0; g["over"] = True
        lines.append(f"💔 {p['name']} 破产啦，{o['name']} 赢下这一局！")
    g["turn"] = "me" if g["turn"]=="you" else "you"
    lines.append(f"轮到 {_cur(g)['name']}。")
    return NL.join(lines)


@mcp.tool()
def monopoly_buy() -> str:
    """当前回合的人买下脚下这座城。"""
    g = GAME["g"]
    if not g: return "还没开局。"
    p, o = _cur(g), _oth(g)
    cell = BOARD[p["pos"]]
    if cell["type"] != "property": return f"【{cell['name']}】不是能买的城。"
    if cell["name"] in p["props"]: return "这座城已经是你的了，说「盖房」升级。"
    if cell["name"] in o["props"]: return f"这城是{o['name']}的，买不了。"
    if p["money"] < cell["price"]: return f"钱不够（要 {cell['price']}）。"
    p["money"] -= cell["price"]; p["props"][cell["name"]] = True; p["houses"][cell["name"]] = 0
    return f"买下【{cell['name']}】，花 {cell['price']}，还剩 {p['money']}。"


@mcp.tool()
def monopoly_build() -> str:
    """盖房升级租金（一座城最多3级，一次一级，要地价一半）。"""
    g = GAME["g"]
    if not g: return "还没开局。"
    p = _cur(g)
    cell = BOARD[p["pos"]]
    if cell["type"] != "property" or cell["name"] not in p["props"]:
        return "得站在自己的城上，才能盖房。"
    h = p["houses"].get(cell["name"], 0)
    if h >= MAX_HOUSES: return f"已经 {MAX_HOUSES} 房满级，再盖就成摩天大楼啦。"
    cost = int(cell["price"] * 0.5)
    if p["money"] < cost: return f"盖房要 {cost}，钱不够。"
    p["money"] -= cost; p["houses"][cell["name"]] = h + 1
    return f"给【{cell['name']}】盖到 {h+1}/{MAX_HOUSES} 房，租金涨到 {_rent(cell, h+1)}。"


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
