import asyncio
import datetime
import sys

import discord
from discord.ext import tasks

import os


ONE = "\U00000031\U000020E3"
TWO = "\U00000032\U000020E3"
THREE = "\U00000033\U000020E3"
X = "\U0000274C"

NUM_PLAYER_QUORUM = 3

TEXT_IN_THE_DARK_NAME = "text-in-the-dark"

BLADES_ROLE_NAME = "blades"

SESSION_DAY = 1  # Tuesday
SESSION_HOUR = 18
SESSION_MINUTE = 30

POLL_DAY = 3  # Thursday
POLL_HOUR = 10
POLL_MINUTE = 0

QUORUM_DAY = 0  # Monday

POLL_TEXT = """{mention} Arrr, when be our next plunderin' session? Ye best be respondin' by Saturday, if ye can, or by Sunday at the latest! This'll help me chart me course for the week ahead, arrr! 🏴‍☠️
{session_dates[0]} {ONE}
{session_dates[1]} {TWO}
{session_dates[2]} {THREE}
None of these dates work {X}"""

EVENT_TEXT = """{mention} Arrr, we be settin' sail for our game this Tuesday, {session.month}/{session.day}. Shapern yer cutlasses and reader yer wits -- time to plot our next cunning caper!"""

NO_QUORUM_TEXT = """Arrr, not enough scallywags for the crew! Only {players} of ye have answered the call. We be needin' more hands on deck!"""


class CaptainBlackheart(discord.Client):
    async def on_ready(self):
        print(f"We have logged in as {self.user}")

        # Assuming we only have a single guild (server), single channel
        for guild in self.guilds:
            print(f"Guild: {guild.name}")

            self.blades_role = discord.utils.get(guild.roles, name=BLADES_ROLE_NAME)
            print(self.blades_role)

            for channel in guild.channels:
                if channel.name == TEXT_IN_THE_DARK_NAME:
                    self.channel = channel.id

        print("Monitoring channels: {self.channel}")

        self.last_poll = None

        self.check_weekday.start()

    @tasks.loop(hours=24)
    async def check_weekday(self):
        channel = self.get_channel(self.channel)

        today = datetime.datetime.now()

        if today.weekday() == POLL_DAY:
            await self.create_poll()
        elif today.weekday() == QUORUM_DAY:
            if self.last_poll == None:
                pass
            else:
                players = await count_reacts(self.last_poll)
                session = self.next_sessions()[0]
                if players >= NUM_PLAYER_QUORUM:
                    await channel.send(
                        EVENT_TEXT.format(mention=self.blades_role.mention)
                    )
                else:
                    await channel.send(NO_QUORUM_TEXT.format(players=players))

    @check_weekday.before_loop
    async def before_check_weekday(self):
        now = datetime.datetime.now()
        future = datetime.datetime(now.year, now.month, now.day, POLL_HOUR, POLL_MINUTE)
        if now.timestamp() > future.timestamp():
            future += datetime.timedelta(days=1)

        wait_seconds = (future - now).total_seconds()
        await asyncio.sleep(wait_seconds)

    async def create_poll(self):
        channel = self.get_channel(self.channel)

        sessions = self.next_sessions()
        session_dates = [f"{session.month}/{session.day}" for session in sessions]
        poll_message = await channel.send(
            POLL_TEXT.format(mention=self.blades_role.mention)
        )

        await poll_message.add_reaction(ONE)
        await poll_message.add_reaction(TWO)
        await poll_message.add_reaction(THREE)
        await poll_message.add_reaction(X)

        self.last_poll = poll_message

    async def count_reacts(self):
        message = self.last_poll
        for reaction in message.reactions:
            if str(reaction.emoji) == ONE:
                return reaction.count
        return 0

    def next_sessions(self):
        """Returns the dates of the next 3 sessions"""
        today = datetime.datetime.today()
        session = datetime.datetime(
            today.year, today.month, today.day, SESSION_HOUR, SESSION_MINUTE
        )
        days_ahead = (SESSION_DAY - today.weekday()) % 7

        return (
            session + datetime.timedelta(days=days_ahead),
            session + datetime.timedelta(days=days_ahead, weeks=1),
            session + datetime.timedelta(days=days_ahead, weeks=2),
        )


TOKEN_NAME = "CAPTAIN_BLACKHEART_TOKEN"
TOKEN = os.environ.get(TOKEN_NAME, None)
if not TOKEN:
    sys.exit("No token found in environment")


intents = discord.Intents.default()
intents.message_content = True

client = CaptainBlackheart(intents=intents)
client.run(TOKEN)
