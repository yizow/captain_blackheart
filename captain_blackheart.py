import datetime

import discord
from discord.ext import tasks

import weekly_poll


ONE = "\U00000031\U000020E3"
TWO = "\U00000032\U000020E3"
THREE = "\U00000033\U000020E3"
X = "\U0000274C"

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


channel_ids = {}

TEXT_IN_THE_DARK_NAME = "testing"

pollCog = weekly_poll.WeeklyPoll()


@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")

    for guild in client.guilds:
        print(f"Guild: {guild.name}")
        for channel in guild.channels:
            if channel.name == TEXT_IN_THE_DARK_NAME:
                channel_ids[TEXT_IN_THE_DARK_NAME] = channel.id

    print("Monitoring channels:")
    print(channel_ids)

    check_weekday.start()



@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith("$hello"):
        await message.channel.send("Avast ye matey!")

""" Returns next 3 Tuesdays """
def next_sessions():
    TUESDAY = 1

    today = datetime.datetime.today()
    days_ahead = (TUESDAY - today.weekday())% 7
    return today + datetime.timedelta(days_ahead), today+datetime.timedelta(days_ahead + 7), today+datetime.timedelta(days_ahead +14)



async def create_poll():
    print("creating poll")
    channel_id = channel_ids[TEXT_IN_THE_DARK_NAME]
    channel = client.get_channel(channel_id)

    sessions = next_sessions()
    session_dates = [f"{session.month}/{session.day}" for session in sessions]
    poll_text = f"""Arrr, when be our next plunderin' session? Ye best be respondin' by Saturday, if ye can, or by Sunday at the latest! This'll help me chart me course for the week ahead, arrr! 🏴‍☠️
{session_dates[0]} {ONE}
{session_dates[1]} {TWO}
{session_dates[2]} {THREE}
None of these dates work {X}"""
    poll_message = await channel.send(poll_text)

    await poll_message.add_reaction(ONE)
    await poll_message.add_reaction(TWO)
    await poll_message.add_reaction(THREE)
    await message.add_reaction(X)


@tasks.loop(hours=24)
async def check_weekday():
    print("check_weekday")
    today = datetime.datetime.now()
    print(today.weekday())

    # Thursday
    if today.weekday() == 4:
        await create_poll()
    # Monday
    elif today.weekday() == 0:
        await create_poll()


client.run(TOKEN)
