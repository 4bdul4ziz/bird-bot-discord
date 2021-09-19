import os
import discord

from utils.shadow_bot import bot
from events import VerificationSystem, CustomCommands
from commands import RoleCommands, GeneralCommands, ModCommands


@bot.event
async def on_ready():
    print("############")
    print('Logged in as:')
    print(bot.user.name)
    print(bot.user.id)
    print('oauth link:')
    print(discord.utils.oauth_url(bot.user.id))
    print("Guilds:", str(len(bot.guilds)))
    print("Users:", str(len(set(bot.get_all_members()))))
    print("############")


if __name__ == '__main__':
    if bot.debug_bot:
        bot.command_prefix = ';;'
        token = os.environ.get("DEBUG_TOKEN")
    else:
        token = os.environ.get("BOT_TOKEN")

    # event handlers
    bot.add_cog(VerificationSystem(bot))

    # commands
    bot.add_cog(RoleCommands(bot))
    bot.add_cog(ModCommands(bot))
    bot.add_cog(GeneralCommands(bot))
    bot.add_cog(CustomCommands(bot))

    bot.run(token.strip(), reconnect=True)
