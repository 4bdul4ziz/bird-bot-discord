import discord

from discord.ext import commands
from discord.ext.commands import bot_has_permissions, guild_only

from utils.permissions import is_mod, can_affect
from utils.errors import Error


class RoleCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @guild_only()
    @bot_has_permissions(manage_roles=True)
    async def giverole(self, ctx, role: discord.Role, member: discord.Member):
        if not is_mod(ctx.author) or not can_affect(ctx.author, member):
            raise Error.NotAllowed

        if role in member.roles:
            raise Error.AlreadyDone

        giveableroles = self.bot.get_config(
            ctx.guild
        ).get('giveable_roles') or []
        if role.id not in giveableroles:
            raise Error.NotGiveable

        await member.add_roles(
            role,
            reason=f"Given by {ctx.author}"
        )

        await ctx.send(
            embed=self.bot.embed(
                f"{member.mention} has been given the {role.mention} role"
            )
        )

    @commands.command()
    @guild_only()
    @bot_has_permissions(manage_roles=True)
    async def takerole(self, ctx, role: discord.Role, member: discord.Member):
        if not is_mod(ctx.author) or not can_affect(ctx.author, member):
            raise Error.NotAllowed

        if role not in member.roles:
            raise Error.AlreadyDone

        giveableroles = self.bot.get_config(
            ctx.guild
        ).get('giveable_roles') or []
        if role.id not in giveableroles:
            raise Error.NotGiveable

        await member.remove_roles(
            role,
            reason=f"Taken away by {ctx.author}."
        )

        await ctx.send(
            embed=self.bot.embed(
                f"The {role.mention} role has been taken \
                    away from {member.mention}."
            )
        )
