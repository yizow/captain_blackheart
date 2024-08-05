import argparse
import asyncio
from datetime import datetime, timedelta
import os
import sys

import discord
from discord.ext import tasks


BLADES_ROLE_NAME = "blades"
TEXT_IN_THE_DARK_NAME = "text-in-the-dark"

NUM_PLAYER_QUORUM = 3

# Days of the week start with Monday=0 and increment through Sunday=6
SESSION_DAY = 1  # Tuesday
SESSION_HOUR = 18
SESSION_MINUTE = 30

POLL_DAY = 3  # Thursday
POLL_HOUR = 10
POLL_MINUTE = 0

QUORUM_DAY = 0  # Monday

POLL_TEXT = f"""{{mention}} Arrr, when be our next plunderin' session? Ye best be respondin' by Saturday, if ye can, or by Sunday at the latest! This'll help me chart me course for the week ahead, arrr! 🏴‍☠️
{{session_dates[0]}} {REACTIONS[0]}
{{session_dates[1]}} {REACTIONS[1]}
{{session_dates[2]}} {REACTIONS[2]}
None of these dates work {X}"""

EVENT_TEXT = """Arrr, we be settin' sail for our game {demonstrative} Tuesday, {session.month}/{session.day}. Sharpen yer cutlasses and ready yer wits -- time to plot our next cunning caper!"""

NO_QUORUM_TEXT = """Arrr, not enough scallywags for the crew! Only {players} of ye have answered the call. We be needin' more hands on deck!"""


COMMAND_PREFIX = "!"

TOKEN_NAME = "CAPTAIN_BLACKHEART_TOKEN"


ONE = "\U00000031\U000020E3"
TWO = "\U00000032\U000020E3"
THREE = "\U00000033\U000020E3"
X = "\U0000274C"
REACTIONS = [ONE, TWO, THREE, X]


TESTING_NAME = "testing"


class CaptainBlackheart(discord.Client):
    def __init__(self, intents, args):
        super().__init__(intents=intents)
        self.COMMANDS = {
            "poll": self.create_poll,
            "quorum": self.count_quorum,
            "reset": self.reset,
        }

        self.scheduled_session = None

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
        today = datetime.now()

        if today.weekday() == POLL_DAY:
            await self.create_poll()
        elif today.weekday() == QUORUM_DAY:
            await self.count_quorum()

    @check_weekday.before_loop
    async def before_check_weekday(self):
        now = datetime.now()
        future = datetime(now.year, now.month, now.day, POLL_HOUR, POLL_MINUTE)
        if now.timestamp() > future.timestamp():
            future += timedelta(days=1)

        wait_seconds = (future - now).total_seconds()
        await asyncio.sleep(wait_seconds)

    async def create_poll(self):
        # Already have a scheduled_session, no need to poll again
        if self.scheduled_session and self.scheduled_session > datetime.now():
            return

        sessions = self.next_sessions()
        session_dates = [f"{session.month}/{session.day}" for session in sessions]
        poll_message = await self.channel.send(
            POLL_TEXT.format(
                mention=self.blades_role.mention, session_dates=session_dates
            )
        )

        for reaction in REACTIONS:
            await poll_message.add_reaction(reaction)

        self.last_poll = poll_message
        self.scheduled_session = None

    async def count_reacts(self):
        message = await self.channel.fetch_message(self.last_poll.id)
        reactions = [0, 0, 0, 0]

        for reaction in message.reactions:
            try:
                index = REACTIONS.index(str(reaction.emoji))
                # -1 because we subtract our own vote
                reactions[index] = reaction.count - 1
            except ValueError:
                pass

        return reactions

    async def count_quorum(self):
        if self.last_poll == None:
            return

        players = await self.count_reacts()
        # drop the "x" no-vote
        players = players[:-1]

        # Send out a reminder, but only @mention if its happening this week
        if self.scheduled_session:
            imminent = is_imminent(self.scheduled_session)
            await self.send_event_text(mention=imminent)
            return

        for num_players, session in zip(players, self.next_sessions()):
            if num_players >= NUM_PLAYER_QUORUM:
                self.scheduled_session = session
                await self.send_event_text(mention=True)
                break

        if self.scheduled_session == None:
            await self.channel.send(NO_QUORUM_TEXT.format(players=max(players)))

    def next_sessions(self):
        """Returns the dates of the next 3 sessions"""
        today = datetime.today()
        session = datetime(
            today.year, today.month, today.day, SESSION_HOUR, SESSION_MINUTE
        )
        days_ahead = (SESSION_DAY - today.weekday()) % 7

        return (
            session + timedelta(days=days_ahead),
            session + timedelta(days=days_ahead, weeks=1),
            session + timedelta(days=days_ahead, weeks=2),
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

    async def send_event_text(self, mention=False):
        text = EVENT_TEXT.format(
            session=self.scheduled_session,
            demonstrative="this" if is_imminent(self.scheduled_session) else "on",
        )

        if mention:
            text = self.blades_role.mention + " " + text

        await self.channel.send(text)

    async def reset(self):
        print("Manually resetting poll info")
        self.last_poll = None
        self.scheduled_session = None


def is_imminent(session):
    today = datetime.today()
    delta = session - today
    return delta <= timedelta(days=4)


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
