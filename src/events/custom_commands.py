import discord

from discord.ext import commands

from utils.permissions import is_admin, is_mod, is_helper, can_affect
from utils.errors import Error


class CustomCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.actions = {
            "text": self.execute_text,
            "self_role": self.execute_self_role,
            "give_role": self.execute_give_role,
            "take_role": self.execute_take_role
        }

    async def execute_text(self, text: str, ctx: commands.Context, _msg: discord.Message):
        await ctx.send(embed=self.bot.embed(text))

    async def execute_self_role(self, role_ids, _ctx: commands.Context, msg: discord.Message):
        roles = [msg.guild.get_role(r) for r in make_list(role_ids)]
        await msg.author.add_roles(*roles)

    async def execute_give_role(self, role_ids, ctx: commands.Context, msg: discord.Message):
        if len(msg.content.split(" ")) < 2:
            raise Error.MissingArgument

        target = await commands.MemberConverter().convert(ctx, msg.content.split(" ")[1])
        if not can_affect(msg.author, target):
            raise Error.NotAllowed

        roles = [msg.guild.get_role(r) for r in make_list(role_ids)]
        await target.add_roles(*roles)

    async def execute_take_role(self, role_ids, ctx: commands.Context, msg: discord.Message):
        if len(msg.content.split(" ")) < 2:
            raise Error.MissingArgument

        target = await commands.MemberConverter().convert(ctx, msg.content.split(" ")[1])
        if not can_affect(msg.author, target):
            raise Error.NotAllowed

        roles = [msg.guild.get_role(r) for r in make_list(role_ids)]
        await target.remove_roles(*roles)

    async def check_permission(self, perm: str, actor: discord.Member):
        if perm == "admin":
            return is_admin(actor)
        elif perm == "moderator" or perm == "mod":
            return is_mod(actor)
        elif perm == "helper":
            return is_helper(actor)
        return False

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.guild is None:
            return

        prefix = await self.bot.get_prefix(msg)
        if not msg.content.startswith(prefix):
            return

        content = msg.content.strip(prefix)
        cmd = content.split(" ")[0]

        cmd_settings = None
        if "custom_commands" in self.bot.get_config(msg.guild):
            for cc in self.bot.get_config(msg.guild)["custom_commands"]:
                if cc["name"] == cmd:
                    cmd_settings = cc
                    break

        if cmd_settings is None:
            return

        if "min_perm" in cmd_settings and not await self.check_permission(cmd_settings["min_perm"], msg.author):
            await self.bot.handle_error(msg.channel, Error.NotAllowed)

        ctx = commands.Context(message=msg, bot=self.bot, prefix=prefix)
        for key, value in cmd_settings.items():
            if key in self.actions:
                try:
                    await self.actions[key](value, ctx, msg)
                except Exception as e:
                    await self.bot.on_command_error(ctx, e)


def make_list(args):
    if isinstance(args, list):
        return args
    return [args]
