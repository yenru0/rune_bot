import random
import os
import os.path
import glob
import json
import datetime

import discord
from discord.ext import commands

import function

DATA_ROUTE = "./private_data/"
PUBLIC_DATA_ROUTE = "./public_data/"
ADMIN_DATA_ROUTE = "./admin.json"

DEFAULT_USER_STATUS = {
    "ticket": 1,
    "stats": {
        "rsp_win": 0,
        "rsp_tie": 0,
        "rsp_lose": 0,
        "rsp_try": 0,
        "ticket_total_gain": 1,
        "ticket_total_consume": 0
    }
}
DEFAULT_EVENT_STATUS = {
    '1': [],
    '2': [],
    '3': [],
    '4': [],
    '5': []
}
DEFAULT_ADMIN = {
    "lock": False,
    "admins": [

    ]
}

KST = datetime.timezone(datetime.timedelta(hours=9))
REGULAR_TIME_BURNING_BETWEEN = (datetime.time(hour=21, tzinfo=KST), datetime.time(hour=23, tzinfo=KST))

intents = discord.Intents.default()
intents.members = True
app = commands.Bot(command_prefix=['룬 ', ':!'], intents=intents)

cached_users_id: list = []  # List[int]
cached_users_status: dict = {}  # dict
users_last_rsp_try = {}

cached_admin: dict = DEFAULT_ADMIN.copy()

cached_event: dict = DEFAULT_EVENT_STATUS.copy()


def check_joined_event(user_id) -> bool:
    if cached_admin["lock"]:
        return False
    if user_id in cached_users_id:
        return True
    else:
        return False


def ticket_gain(user_id, amount=1) -> bool:
    cached_users_status[user_id]['ticket'] += amount
    cached_users_status[user_id]['stats']['ticket_total_gain'] += amount
    return True


def ticket_consume(user_id, amount) -> bool:
    if cached_users_status[user_id]['ticket'] > 0:
        cached_users_status[user_id]['ticket'] -= amount
        cached_users_status[user_id]['stats']['ticket_total_consume'] += amount
        return True
    else:
        return False


def add_ticket(user_id, num: int):
    cached_event[str(num)].append(user_id)


def save_event():
    with open(PUBLIC_DATA_ROUTE + "event.json", "w", encoding='utf-8') as f:
        json.dump(cached_event, f)


def is_timeburning():
    return REGULAR_TIME_BURNING_BETWEEN[0] <= datetime.datetime.now(tz=KST).timetz() <= REGULAR_TIME_BURNING_BETWEEN[1]


@app.event
async def on_ready():
    print(app.user.name, 'has connected to Discord!')
    # 유저 아이디 캐싱
    paths = glob.glob(DATA_ROUTE + "*.user")
    for path in paths:
        user_id = int(os.path.splitext(os.path.basename(path))[0])
        cached_users_id.append(user_id)
        with open(path, 'r', encoding='utf-8') as f:
            cached_users_status[user_id] = function.dict_update_recursive(DEFAULT_USER_STATUS.copy(), json.load(f))

    if not os.path.isfile(PUBLIC_DATA_ROUTE + "event.json"):
        with open(PUBLIC_DATA_ROUTE + "event.json", "w", encoding='utf-8') as f:
            json.dump(DEFAULT_EVENT_STATUS, f)

    with open(PUBLIC_DATA_ROUTE + "event.json", "r", encoding='utf-8') as f:
        cached_event.update(json.load(f))

    with open(ADMIN_DATA_ROUTE, "r", encoding='utf-8') as f:
        cached_admin.update(json.load(f))

    with open(ADMIN_DATA_ROUTE, "w", encoding='utf-8') as f:
        json.dump(cached_admin, f)

    await app.change_presence(status=discord.Status.online, activity=discord.Game("룬 도움"))
    print("ready")


@app.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        # await ctx.send("입력하신 커맨드는 없는 커맨드입니다.")
        return
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("입력하신 커맨드의 인자를 제대로 받지 못하였습니다.")
        return
    raise error


@app.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    await app.process_commands(message)
    # 그냥 대강 모든 메세지 처리함
    if check_joined_event(message.author.id):
        with open(DATA_ROUTE + f"{message.author.id}.user", "w", encoding='utf-8') as f:
            json.dump(cached_users_status[message.author.id], f)


async def 강매(ctx: discord.ext.commands.Context):
    if cached_admin["lock"]:
        embed = discord.Embed(title=f"이벤트가 관리자에 의해 멈췄습니다.")
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"`룬 이벤트 참가`를 통해 이벤트에 참가해주세요!")


@app.command()
async def 자기소개(ctx: discord.ext.commands.Context):
    await ctx.send("> **안녕하세요, 저는 시온왕국의 마스코트이자 앞으로 시온 왕국에서 펼쳐지는 스페셜 이벤트를 도울 이벤트 도우미 봇 룬입니다!**")


@app.command()
async def 도움(ctx):
    embed = discord.Embed(
        title="도움",
        color=0x0000FF
    )
    embed.add_field(
        name="가위바위보",
        value="""
        ```룬 가위바위보 (가위|바위|보)
룬 (가위|바위|보)```
가위바위보의 쿨타임은 ***10초***입니다.
""",
        inline=False
    )
    embed.add_field(
        name="응모",
        value="""
`룬 응모 현황`: 현재 응모 현황을 보여줍니다.
`룬 응모 1~5`: 1~5의 번호에 티켓을 소모해 응모합니다.
"""
    )
    embed.add_field(
        name="정보",
        value="""
`룬 정보`: 현재 가지고 있는 티켓을 볼 수 있습니다.
"""
    )
    embed.add_field(
        name="타임버닝",
        value="`룬 타임버닝`: 타임버닝은 이벤트 기간 중 매일 9시부터 11시까지 진행됩니다! 이 시간에는 가위바위보 승리시 얻는 티켓의 갯수가 2배가 됩니다.",
    )
    embed.set_footer(text="*이벤트는 관리자에 의해 언제든지 중지될 수 있습니다.")
    await ctx.send(embed=embed)


@app.command()
async def 가위바위보(ctx: discord.ext.commands.Context, rsp: str = None):
    if not check_joined_event(ctx.author.id):
        await 강매(ctx)
        return
    if ctx.author.id in users_last_rsp_try:
        if (datetime.datetime.now() - users_last_rsp_try[ctx.author.id]).seconds > 10:
            users_last_rsp_try[ctx.author.id] = datetime.datetime.now()
        else:
            await ctx.send("가위바위보 쿨타임입니다.")
            return
    else:
        users_last_rsp_try[ctx.author.id] = datetime.datetime.now()

    rsp = function.convert_rsp_str_int(rsp)
    if rsp is None:
        embed = discord.Embed(title="가위바위보",
                              description=f"룬과의 가위바위보에서 이겨서 티켓을 얻어 이벤트 상품 응모에 참여해보세요.\n`룬 가위`, `룬 바위`, `룬 보` 세가지 키워드를 입력하여 룬과 가위바위보를 할 수 있습니다!")
        await ctx.send(embed=embed)
        return
    W = [1, 1, 1]
    W[(rsp - 1) % 3] += (0.5 if is_timeburning() else 0.6)
    com_rsp = random.choices(range(3), W, k=1)[0]
    result = function.judge_rsp(rsp, com_rsp)

    member = ctx.guild.get_member(ctx.author.id)
    embed = discord.Embed(
        title=f"{function.convert_rsp_int_str(com_rsp)}, {member.nick if member.nick else member.name}님 제가 {function.convert_state_int_str(-result)}",
        description=f"당신이 {function.convert_state_int_str(result)}",
        color=0xCC8899)
    if is_timeburning():
        ticket_get = random.randint(2, 2)
    else:
        ticket_get = random.randint(1, 1)
    embed.set_footer(
        text=f"{f'티켓 +{ticket_get}' if result > 0 else ''}(현재 티켓: {cached_users_status[ctx.author.id]['ticket']})", )
    if result == 1:
        ticket_gain(ctx.author.id, ticket_get)
        cached_users_status[ctx.author.id]['stats']['rsp_win'] += 1
    elif result == 0:
        cached_users_status[ctx.author.id]['stats']['rsp_tie'] += 1
    elif result == -1:
        cached_users_status[ctx.author.id]['stats']['rsp_lose'] += 1
    cached_users_status[ctx.author.id]['stats']['rsp_try'] += 1
    await ctx.send(embed=embed)


@app.command()
async def 바위(ctx: discord.ext.commands.Context):
    await 가위바위보(ctx, "바위")


@app.command()
async def 가위(ctx: discord.ext.commands.Context):
    await 가위바위보(ctx, "가위")


@app.command()
async def 보(ctx: discord.ext.commands.Context):
    await 가위바위보(ctx, "보")


@app.command()
async def 타임버닝(ctx: discord.ext.commands.Context):
    if not check_joined_event(ctx.author.id):
        await 강매(ctx)
        return

    if is_timeburning():
        await ctx.send(embed=discord.Embed(title="지금은 ***타임버닝*** 시간입니다.",
                                           description="타임버닝은 이벤트 기간 중 매일 9시부터 11시까지 진행됩니다! 이 시간에는 가위바위보 승리시 얻는 티켓의 갯수가 2배가 됩니다.",
                                           color=0xFF0000))
    else:
        await ctx.send(embed=discord.Embed(title="지금은 타임버닝 시간이 아닙니다.",
                                           description="타임버닝은 이벤트 기간 중 매일 9시부터 11시까지 진행됩니다! 이 시간에는 가위바위보 승리시 얻는 티켓의 갯수가 2배가 됩니다."))


@app.command()
async def 정보(ctx: discord.ext.commands.Context):
    if not check_joined_event(ctx.author.id):
        await 강매(ctx)
        return
    embed = discord.Embed(
        title=f"{ctx.author.nick if ctx.author.nick else ctx.author.name}님의 정보",
        description=f"티켓:ticket: 개수: {cached_users_status[ctx.author.id]['ticket']}",
        color=0xFF0000
    )
    await ctx.send(embed=embed)


@app.command()
async def 내아이디(ctx: discord.ext.commands.Context):
    await ctx.send(f"> 당신의 아이디는 '{ctx.author.id}' 입니다.")


@app.command()
async def 응모(ctx: discord.ext.commands.Context, subcommand: str):
    if not check_joined_event(ctx.author.id):
        await 강매(ctx)
        return
    if subcommand == "현황":
        lens = [len(v) for v in cached_event.values()]
        sums = sum(lens)
        embed = discord.Embed(
            title=f"응모 현황",
            color=0xFF0000
        )
        for i in range(5):
            embed.add_field(name=f"{i + 1}", value=f"{lens[i]}개({round(lens[i] / sums * 100, 2) if sums != 0 else 0}%)",
                            inline=True)
        await ctx.send(embed=embed)
    elif subcommand.isdigit():
        num = int(subcommand)
        if 1 <= num <= 5:
            if ticket_consume(ctx.author.id, 1):
                add_ticket(ctx.author.id, num)
                save_event()
                await ctx.send(f"{num}에 성공적으로 넣었습니다!")
            else:
                await ctx.send(f"티켓이 부족합니다!")
        else:
            await ctx.send("없는 응모 번호입니다. 1~5까지의 번호를 입력해주세요.")

    else:
        await ctx.send("없는 명령어입니다.")


@app.command()
async def 이벤트(ctx: discord.ext.commands.Context, subcommand: str):
    if subcommand in ("참여", "참가"):
        if not check_joined_event(ctx.author.id):
            cached_users_id.append(ctx.author.id)
            cached_users_status[ctx.author.id] = DEFAULT_USER_STATUS.copy()
            await ctx.send("성공적으로 참여하셨습니다.\n+1:ticket:")
        else:
            await ctx.send("이미 참여한 아이디입니다.")
    else:
        await ctx.send("없는 명령어입니다.")


@app.command()
async def 관리자(ctx: discord.ext.commands.Context, subcommand: str, subsubcommand: str = "", subsubsubcommand: str = ""):
    if ctx.author.id in cached_admin["admins"]:
        pass
    else:
        await ctx.send("관리자 권한이 없습니다.")
        return
    if subcommand == "확인":
        await ctx.send("관리자 권한을 확인하였습니다.")
    elif subcommand == "도움":
        embed = discord.Embed(title="관리자 권한 도움말", description="", color=0x00FF00)
        embed.add_field(name="이벤트",
                        value="`룬 관리자 이벤트 추첨`\n`룬 관리자 이벤트 응모현황 (id)`\n`룬 관리자 이벤트 비우기`\n`룬 관리자 이벤트 절멸`\n`룬 관리자 이벤트 중지`\n`룬 관리자 이벤트 재시작`")
        await ctx.send(embed=embed)
    elif subcommand == "이벤트":
        if subsubcommand == "추첨":
            copied = cached_event.copy()
            lens = [len(v) for v in cached_event.values()]
            if all(lens):
                pass
            else:
                await ctx.send("응모가 충분히 진행되지 않았습니다.")
                return
            embed = discord.Embed(
                title=f"이벤트 추첨 결과",
                color=0xFF0000
            )
            for i in range(5):
                if len(copied[str(i + 1)]) == 0:
                    await ctx.send("응모가 충분히 진행되지 않았습니다. 부족한 인원수")
                    return
                user_id = copied[str(i + 1)][random.randrange(0, len(copied[str(i + 1)]))]
                embed.add_field(name=f"{i + 1}",
                                value=f"{ctx.guild.get_member(user_id)}님",
                                inline=False
                                )
                for j in range(5):
                    copied[str(j + 1)] = list(filter(lambda x: x != user_id, copied[str(j + 1)]))

            await ctx.send(embed=embed)
            return
        elif subsubcommand == "응모현황":
            if subsubsubcommand.isdigit():
                user_id = int(subsubsubcommand)
                if user_id in cached_users_id:
                    per = [len(list([1 for poll in cached_event[str(i + 1)] if poll == user_id])) for i in range(5)]
                    embed = discord.Embed(title=f"개인 응모 현황({ctx.guild.get_member(user_id)})", )
                    for i in range(5):
                        embed.add_field(name=f"{i + 1}", value=f"{per[i]}", inline=False)
                else:
                    embed = discord.Embed(title="없는 아이디입니다.")
                await ctx.send(embed=embed)
            return
        elif subsubcommand == "비우기":
            await ctx.send("모든 응모 현황을 삭제합니다.")
            cached_event.update(DEFAULT_EVENT_STATUS)
            save_event()
            await ctx.send("삭제하였습니다.")
        elif subsubcommand == "절멸":
            await ctx.send("모든 응모 현황 및 이벤트 참여 기록을 삭제합니다.")
            cached_event.update(DEFAULT_EVENT_STATUS)
            save_event()
            for us in cached_users_id:
                os.remove(DATA_ROUTE + f"{us}.user")
            cached_users_status.update(DEFAULT_USER_STATUS)
            cached_users_id.clear()
            await ctx.send("삭제하였습니다.")
            return
        elif subsubcommand == "중지":
            cached_admin["lock"] = True
            with open(ADMIN_DATA_ROUTE, "w", encoding='utf-8') as f:
                json.dump(cached_admin, f)
            await ctx.send("이벤트 멈춰!")
            return
        elif subsubcommand == "재시작":
            cached_admin["lock"] = False
            with open(ADMIN_DATA_ROUTE, "w", encoding='utf-8') as f:
                json.dump(cached_admin, f)
            await ctx.send("이벤트 다시시작!")
            return
    else:
        await ctx.send("없는 명령어입니다.")


if __name__ == '__main__':
    if not os.path.isdir(PUBLIC_DATA_ROUTE):
        os.mkdir(PUBLIC_DATA_ROUTE)
    if not os.path.isdir(DATA_ROUTE):
        os.mkdir(DATA_ROUTE)
    if not os.path.isfile(ADMIN_DATA_ROUTE):
        with open(ADMIN_DATA_ROUTE, "w", encoding='utf-8') as f:
            json.dump(DEFAULT_ADMIN, f)
    if not os.path.isfile("token.token"):
        TOKEN = os.getenv("TOKEN")
        print(TOKEN)
        if TOKEN:
            print("Token from env")
        else:
            print("There is No Token")
            quit()
    else:
        with open("token.token", "r", encoding='utf-8') as f:
            print("Token from token.token")
            TOKEN = f.read()

    app.run(TOKEN)
