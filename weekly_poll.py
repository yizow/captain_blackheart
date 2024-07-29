from discord.ext import tasks, commands


class WeeklyPoll(commands.Cog):
    def __init__(self):
        print("Starting weekly poll")
        self.index = 0

    def cog_unload(self):
        self.printer.cancel()

    @tasks.loop(seconds=1.0, count=5)
    async def printer(self):
        print(f"Poll: {self.index}")
        self.index += 1
