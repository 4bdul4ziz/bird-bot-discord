from datetime import datetime, timedelta
from discord import Member, TextChannel, User
from discord.ext.commands import Cog, command, \
    bot_has_permissions, Greedy, guild_only
from typing import Optional

from utils.shadow_bot import ShadowBot
from utils.permissions import is_mod, can_affect
from utils.errors import Error


class ModCommands(Cog):
    def __init__(self, bot: ShadowBot):
        self.bot = bot

    @command()
    @guild_only()
    @bot_has_permissions(kick_members=True)
    async def kick(self, ctx, target: Member, *, reason: Optional[str] = "No reason provided."):
        if not is_mod(ctx.author) or not can_affect(ctx.message.author, target):
            raise Error.NotAllowed

        await target.kick(reason=reason)

        embed = self.bot.embed("", title="Member kicked")

        embed.set_thumbnail(url=target.avatar_url)

        fields = [
            ("Member", f"{target.mention} ({target.id})", False),
            ("Kicked by", ctx.message.author.mention, False),
            ("Reason", reason, False)
        ]

        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)

        # FIXME: add logging
        # await self.bot.log(ctx.guild, embed, "moderation")

        await ctx.send(embed=self.bot.embed(f"{target.mention} has been kicked."))

    @command()
    @guild_only()
    @bot_has_permissions(ban_members=True)
    async def ban(self, ctx, target: User, *, reason: Optional[str] = "No reason provided."):
        if not is_mod(ctx.author) or not can_affect(ctx.message.author, target):
            raise Error.NotAllowed

        await ctx.author.guild.ban(target, reason=reason)

        embed = self.bot.embed("", title="Member banned")

        embed.set_thumbnail(url=target.avatar_url)

        fields = [
            ("Member", f"{target.mention} ({target.id})", False),
            ("Banned by", ctx.message.author.display_name, False),
            ("Reason", reason, False)
        ]

        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)

        # FIXME: add logging
        # await self.bot.log(ctx.guild, embed, "moderation")

        await ctx.send(embed=self.bot.embed(f"{target.mention} has been banned."))

    @command()
    @guild_only()
    @bot_has_permissions(manage_messages=True)
    async def purge(self, ctx, targets: Greedy[User], limit: Optional[int] = 20, channel: Optional[TextChannel] = None):
        if not is_mod(ctx.author):
            raise Error.NotAllowed

        if not channel:
            channel = ctx.channel

        def _check(message):
            return not len(targets) or message.author in targets

        if 1 < limit <= 100:
            with ctx.channel.typing():
                await ctx.message.delete()

                deleted = await channel.purge(
                    limit=limit,
                    after=datetime.utcnow() - timedelta(days=14),
                    check=_check
                )

                await ctx.send(f"Purged {len(deleted):,} messages.", delete_after=5)

        else:
            await ctx.send("The limit provided is not within acceptable bounds.")
