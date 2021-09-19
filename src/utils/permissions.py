import discord

from .shadow_bot import bot


def is_helper(member: discord.Member):
    if is_mod(member):
        return True

    role_ids = [r.id for r in member.roles]
    perms = bot.get_config(member.guild)['permissions']

    helpers = perms.get('helper') or []

    return any(
        [r in helpers for r in role_ids]
    )


def is_mod(member: discord.Member):
    if is_admin(member):
        return True

    role_ids = [r.id for r in member.roles]
    perms = bot.get_config(member.guild)['permissions']

    mods = perms.get('mods') or []

    return any(
        [r in mods for r in role_ids]
    )


def is_admin(member: discord.Member):
    if member.guild.owner_id == member.id:
        return True

    role_ids = [r.id for r in member.roles]
    perms = bot.get_config(member.guild)['permissions']

    admins = perms.get('admins') or []

    return any(
        [r in admins for r in role_ids]
    )


def can_affect(actor: discord.Member, affected: discord.Member):
    return not hasattr(affected, 'guild') \
        or actor.top_role > affected.top_role \
        or affected.guild.owner == actor
