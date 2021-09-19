import discord
import time

from discord.ext import commands


class GeneralCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        """pong."""
        t1 = time.perf_counter()
        async with ctx.message.channel.typing():
            t2 = time.perf_counter()
        ep = discord.Embed(
            colour=self.bot.color,
            description="Pong! -| **{0}**ms 🏓\n".format(
                str(round((t2 - t1) * 1000))
            )
        )
        ep.set_author(name='Pong!', icon_url=self.bot.icon)
        await ctx.send(embed=ep)
