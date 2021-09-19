import discord
import aiohttp
import logging
import yaml
import os
import sys
import re
import traceback

from discord.ext import commands
from datetime import datetime
from pymongo import MongoClient
from .errors import Error

conversion_fail_re_comp = re.compile(
    r'Converting to \"[a-zA-Z0-9.]+\" failed for parameter \"'
    r'[a-zA-Z0-9]+\"\.'
)
conversion_args_re_comp = re.compile('\"[a-zA-Z0-9.]+\"')


class ShadowBot(commands.AutoShardedBot):
    def __init__(self, *args, **kwargs):
        super().__init__(None, *args, **kwargs)
        self.default_prefix = ';'
        self.icon = ""  # TODO get a nice icon url
        self.color = discord.Color(15533317)
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.logger = logging.getLogger("bird")

        with open("config.yaml") as f:
            self._config = yaml.safe_load(f.read())

        self.debug_bot = any('debug' in arg.lower() for arg in sys.argv)
        self.db = MongoClient(
            os.environ.get('DB_HOST'),
            27017,
            username=os.environ.get('DB_USERNAME'),
            password=os.environ.get('DB_PASSWORD')
        )['bird-db']

    def embed(
            self, content, success_or_colour=True,
            show_author=True, image=None,
            title=None, author=None
    ):
        if success_or_colour is True:
            clr = self.color
        elif success_or_colour is False:
            clr = discord.Colour.red()
        else:
            clr = success_or_colour

        em = discord.Embed(
            type='rich',
            description=content,
            colour=clr,
            timestamp=datetime.utcnow()
        )

        if title:
            em.title = title

        if show_author:
            em.set_author(
                name=author if author else "",
                icon_url=self.icon
            )

        if image:
            em.set_image(url=image)

        return em

    def get_config(self, guild: discord.Guild):
        id = str(guild.id)
        if id not in self._config:
            return {}

        return self._config[id]

    def log(self, guild: discord.Guild, embed: discord.Embed, log_type="default"):
        logs = self.get_config(guild).get("logging") or {}
        log_type = log_type if log_type in logs else "default"

        if log_type in logs:
            channel = guild.get_channel(logs[log_type])
            channel.send(embed=embed)

    async def on_command_error(self, ctx, error):
        async def resp(ctx, embed_text):
            try:
                await ctx.send(
                    embed=self.embed(embed_text, author="Error Occured", success_or_colour=False),
                    delete_after=20
                )
            except discord.Forbidden:
                return

        if isinstance(error, Error):
            await self.handle_error(ctx, error)
        elif isinstance(error, commands.CommandNotFound):
            pass
        elif isinstance(error, commands.NoPrivateMessage):
            await resp(ctx, "This command can't be ran in DM's.")
        elif isinstance(error, commands.DisabledCommand):
            await resp(ctx, "This command is currently disabled.")
        elif isinstance(error, commands.CommandOnCooldown):
            await resp(
                ctx, f"This command is on cooldown. Try in {int(error.retry_after)} seconds."
            )
        elif isinstance(error, commands.CheckFailure) or isinstance(
                error, commands.MissingPermissions):
            await resp(ctx, "You do not have permission to run this command.")
        elif isinstance(error, commands.BadArgument):
            if not ctx.command:
                usage = ""
            elif ctx.command.usage:
                usage = f" {ctx.command.usage}"
            else:
                usage = ""

            if len(error.args) > 0:
                msg = error.args[0]

                if conversion_fail_re_comp.match(msg):
                    matches = conversion_args_re_comp.findall(msg)
                    value_type = matches[0].strip('"')
                    arg = matches[1].strip('"')
                    msg = f"Failed to convert `{arg}` to the type which is " \
                        f"required (which is `{value_type}`). Please make sure" \
                        " you are following the usage instructions: " \
                        f"`{ctx.prefix}{ctx.invoked_with}{usage}`"

                await resp(ctx, msg)
        else:
            await resp(ctx, "Oops, an unknown error has occurred, please notify one of my developers")
            traceback.print_exception(type(error), error, error.__traceback__)

    async def get_prefix(self, msg):
        if msg.guild and 'prefix' in bot.get_config(msg.guild):
            return bot.get_config(msg.guild)['prefix']
        else:
            return bot.default_prefix

    async def handle_error(self, channel: discord.abc.Messageable, error: Error):
        await channel.send(embed=self.embed(error.value, False))

    # TODO: add logging


_intents = discord.Intents.default()
_intents.members = True

bot = ShadowBot(
    description="A Python bot for help in protecting servers",
    intents=_intents,
)
