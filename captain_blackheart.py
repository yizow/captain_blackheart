import argparse
import asyncio
import datetime
import os
import sys

import discord
from discord.ext import tasks


ONE = "\U00000031\U000020E3"
TWO = "\U00000032\U000020E3"
THREE = "\U00000033\U000020E3"
X = "\U0000274C"

NUM_PLAYER_QUORUM = 3

TEXT_IN_THE_DARK_NAME = "text-in-the-dark"
TESTING_NAME = "testing"

BLADES_ROLE_NAME = "blades"

SESSION_DAY = 1  # Tuesday
SESSION_HOUR = 18
SESSION_MINUTE = 30

POLL_DAY = 3  # Thursday
POLL_HOUR = 10
POLL_MINUTE = 0

QUORUM_DAY = 0  # Monday

POLL_TEXT = f"""{{mention}} Arrr, when be our next plunderin' session? Ye best be respondin' by Saturday, if ye can, or by Sunday at the latest! This'll help me chart me course for the week ahead, arrr! 🏴‍☠️
{{session_dates[0]}} {ONE}
{{session_dates[1]}} {TWO}
{{session_dates[2]}} {THREE}
None of these dates work {X}"""

EVENT_TEXT = """{mention} Arrr, we be settin' sail for our game this Tuesday, {session.month}/{session.day}. Shapern yer cutlasses and reader yer wits -- time to plot our next cunning caper!"""

NO_QUORUM_TEXT = """Arrr, not enough scallywags for the crew! Only {players} of ye have answered the call. We be needin' more hands on deck!"""

TOKEN_NAME = "CAPTAIN_BLACKHEART_TOKEN"

COMMAND_PREFIX = "!"


class CaptainBlackheart(discord.Client):
    def __init__(self, intents, args):
        super().__init__(intents=intents)
        self.COMMANDS = {"poll": self.create_poll, "quorum": self.count_quorum}

        self.testing = args.testing
        self.poll = args.poll

    async def on_ready(self):
        print(f"We have logged in as {self.user}")

        # Assuming we only have a single guild (server), single channel
        for guild in self.guilds:
            print(f"Guild: {guild.name}")

            self.blades_role = discord.utils.get(guild.roles, name=BLADES_ROLE_NAME)
            print(self.blades_role)

            if self.testing:
                channel_name = TESTING_NAME
            else:
                channel_name = TEXT_IN_THE_DARK_NAME

            for channel in guild.channels:
                if channel.name == channel_name:
                    self.channel = channel

        self.last_poll = None
        if args.poll:
            try:
                self.last_poll = await self.channel.fetch_message(self.poll)
                print("Continuing from last poll message")
            except discord.NotFound:
                print("Could not find last poll message, starting fresh")

        print(f"Monitoring channel {self.channel.name}: {self.channel.id}")

        self.check_weekday.start()

    @tasks.loop(hours=24)
    async def check_weekday(self):
        today = datetime.datetime.now()

        if today.weekday() == POLL_DAY:
            await self.create_poll()
        elif today.weekday() == QUORUM_DAY:
            await self.count_quorum()

    @check_weekday.before_loop
    async def before_check_weekday(self):
        now = datetime.datetime.now()
        future = datetime.datetime(now.year, now.month, now.day, POLL_HOUR, POLL_MINUTE)
        if now.timestamp() > future.timestamp():
            future += datetime.timedelta(days=1)

        wait_seconds = (future - now).total_seconds()
        await asyncio.sleep(wait_seconds)

    async def create_poll(self):
        sessions = self.next_sessions()
        session_dates = [f"{session.month}/{session.day}" for session in sessions]
        poll_message = await self.channel.send(
            POLL_TEXT.format(
                mention=self.blades_role.mention, session_dates=session_dates
            )
        )

        await poll_message.add_reaction(ONE)
        await poll_message.add_reaction(TWO)
        await poll_message.add_reaction(THREE)
        await poll_message.add_reaction(X)

        self.last_poll = poll_message

    async def count_reacts(self):
        message = await self.channel.fetch_message(self.last_poll.id)
        for reaction in message.reactions:
            if str(reaction.emoji) == ONE:
                # -1 because we subtract our own vote
                return reaction.count - 1
        return 0

    async def count_quorum(self):
        if self.last_poll == None:
            pass
        else:
            players = await self.count_reacts()
            session = self.next_sessions()[0]
            if players >= NUM_PLAYER_QUORUM:
                await self.channel.send(
                    EVENT_TEXT.format(mention=self.blades_role.mention, session=session)
                )
            else:
                await self.channel.send(NO_QUORUM_TEXT.format(players=players))

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

    async def on_message(self, message):
        if self.channel != message.channel:
            return
        if not message.content.startswith(COMMAND_PREFIX):
            return

        command = message.content[len(COMMAND_PREFIX) :]
        action = self.COMMANDS.get(command, None)

        if action:
            await action()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="CaptainBlackheart",
        description="Discord bot to poll and schedule sessions",
    )

    parser.add_argument("-t", "--testing", action="store_true")
    parser.add_argument(
        "-p",
        "--poll",
        type=int,
        help="Message ID of the last poll, if you needed to restart the bot",
    )
    args = parser.parse_args()

    token = os.environ.get(TOKEN_NAME, None)
    if not token:
        sys.exit("No token found in environment")

    intents = discord.Intents.default()
    intents.message_content = True

    client = CaptainBlackheart(intents, args)
    client.run(token)
