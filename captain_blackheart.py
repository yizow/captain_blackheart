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


TEXT_IN_THE_DARK_NAME = "testing"

BLADES_ROLE_NAME = "blades"


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

        print("Monitoring channels: {channel.id}")

        self.last_poll = None

        self.check_weekday.start()

    @tasks.loop(hours=24)
    async def check_weekday(self):
        channel = self.get_channel(self.channel)

        today = datetime.datetime.now()

        # Thursday
        if today.weekday() == 4:
            await self.create_poll()
        # Monday
        elif today.weekday() == 0:
            if self.last_poll == None:
                pass
            else:
                players = await count_reacts(self.last_poll)
                session = next_sessions()[0]
                if players >= NUM_PLAYER_QUORUM:
                    event_text = f"""{self.blades_role.mention} Arrr, we be settin' sail for our game this Tuesday, {session.month}/{session.day}. Shapern yer cutlasses and reader yer wits -- time to plot our next cunning caper!"""
                    await channel.send(event_text)
                else:
                    await channel.send(
                        f"""Arrr, not enough scallywags for the crew! Only {players} of ye have answered the call. We be needin' more hands on deck!"""
                    )
                    event_text = f"""{self.blades_role.mention} Arrr, we be settin' sail for our game this Tuesday, {session.month}/{session.day}. Shapern yer cutlasses and reader yer wits -- time to plot our next cunning caper!"""
                    await channel.send(event_text)

    async def create_poll(self):
        channel = self.get_channel(self.channel)

        sessions = next_sessions()
        session_dates = [f"{session.month}/{session.day}" for session in sessions]
        poll_text = f"""{self.blades_role.mention} Arrr, when be our next plunderin' session? Ye best be respondin' by Saturday, if ye can, or by Sunday at the latest! This'll help me chart me course for the week ahead, arrr! 🏴‍☠️
{session_dates[0]} {ONE}
{session_dates[1]} {TWO}
{session_dates[2]} {THREE}
None of these dates work {X}"""
        poll_message = await channel.send(poll_text)

        await poll_message.add_reaction(ONE)
        await poll_message.add_reaction(TWO)
        await poll_message.add_reaction(THREE)
        await poll_message.add_reaction(X)

        self.last_poll = poll_message


def next_sessions():
    """Returns next 3 Tuesdays"""
    TUESDAY = 1

    today = datetime.datetime.today()
    days_ahead = (TUESDAY - today.weekday()) % 7
    return (
        today + datetime.timedelta(days_ahead),
        today + datetime.timedelta(days_ahead + 7),
        today + datetime.timedelta(days_ahead + 14),
    )


async def count_reacts(message):
    for reaction in message.reactions:
        if str(reaction.emoji) == ONE:
            return reaction.count
    return 0


TOKEN_NAME = "CAPTAIN_BLACKHEART_TOKEN"
TOKEN = os.environ.get(TOKEN_NAME, None)
if not TOKEN:
    sys.exit("No token found in environment")


intents = discord.Intents.default()
intents.message_content = True

client = CaptainBlackheart(intents=intents)
client.run(TOKEN)
