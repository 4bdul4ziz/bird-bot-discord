import discord

from discord.ext import commands


class VerificationSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.step_executors = {
            "message": self.execute_message,
            "password": self.execute_password,
            "give_role": self.execute_give_role,
            "take_role": self.execute_take_role,
            "reaction": self.execute_reaction,
        }

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if 'verification' not in self.bot.get_config(member.guild):
            return

        print(f"start verification of {member}")

        self.bot.db.verification_system.insert_one(
            {
                'member_id': member.id,
                'guild': member.guild.id,
                'step': 0,
                'wait_on': None
            }
        )
        await self.execute_step(member, 0)

    @commands.Cog.listener()
    async def on_member_leave(self, member: discord.Member):
        self.remove_member(member)

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.guild is None or not hasattr(msg.author, 'guild'):
            return

        if 'verification' not in self.bot.get_config(msg.guild):
            return

        found_step = None
        for index, step in enumerate(self.bot.get_config(msg.guild)['verification']):
            if step['action'] == 'password' \
                    and step['channel'] == msg.channel.id \
                    and step['password'] == msg.content.strip().lower():
                found_step = index
                break

        if found_step is None:
            return

        user_status = self.bot.db.verification_system.find_one(
            {
                'member_id': msg.author.id,
                'guild': msg.guild.id,
                'wait_on': 'password'
            }
        )
        if user_status is None or found_step != user_status['step']:
            return

        try:
            await msg.delete()
        except Exception:
            pass

        self.bot.db.verification_system.update_one(
            {'member_id': msg.author.id, 'guild': msg.guild.id},
            {'$set': {'wait_on': None}}
        )

        await self.execute_step(msg.author, user_status['step'] + 1)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.Member):
        if not hasattr(user, 'guild'):
            return

        if 'verification' not in self.bot.get_config(user.guild):
            return

        found_step = None
        for index, step in enumerate(self.bot.get_config(user.guild)['verification']):
            if step['action'] == 'reaction' \
                    and step['channel'] == reaction.message.channel.id \
                    and (reaction.message.id in step['messages'] if 'messages' in step else step.get('message') == reaction.message.id) \
                    and (any([check_emoji(emoji, reaction.emoji) for emoji in step['emojis']])
                         if 'emojis' in step else check_emoji(step.get('emoji'), reaction.emoji)):
                found_step = index
                break

        if found_step is None:
            return

        user_status = self.bot.db.verification_system.find_one(
            {
                'member_id': user.author.id,
                'guild': user.guild.id,
                'wait_on': 'reaction'
            }
        )
        if user_status is None or found_step != user_status['step']:
            return

        self.bot.db.verification_system.update_one(
            {'member_id': user.id, 'guild': user.guild.id},
            {'$set': {'wait_on': None}}
        )

        await self.execute_step(user, user_status['step'] + 1)

    async def execute_step(self, member: discord.Member, step_num: int):
        if step_num >= len(self.bot.get_config(member.guild)['verification']):
            self.remove_member(member)
            return

        self.bot.db.verification_system.update_one(
            {'member_id': member.id, 'guild': member.guild.id},
            {'$set': {'step': step_num}}
        )

        step = self.bot.get_config(member.guild)['verification'][step_num]
        print(
            f"execute step {step_num} {step['action']} for verifying {member}"
        )
        await self.step_executors[step['action']](member, step_num, step)

    async def execute_message(
        self,
        member: discord.Member,
        step_num: int,
        step
    ):
        if step['channel'] == 'dm':
            channel = member
        else:
            channel = member.guild.get_channel(int(step['channel']))

        print(f"sending message to {channel} for verifying {member}")

        if step.get('embed'):
            em = self.bot.embed(
                step['text'].replace(
                    "{member}", member.mention
                )
            )

            em.set_thumbnail(url=member.avatar_url)

            await channel.send(
                embed=em
            )
        else:
            await channel.send(
                content=step['text'].replace("{member}", member.mention)
            )

        await self.execute_step(member, step_num + 1)

    async def execute_password(
        self,
        member: discord.Member,
        _step_num: int,
        _step
    ):
        self.bot.db.verification_system.update_one(
            {'member_id': member.id, 'guild': member.guild.id},
            {'$set': {'wait_on': 'password'}}
        )

    async def execute_give_role(
        self,
        member: discord.Member,
        step_num: int,
        step
    ):
        role = member.guild.get_role(step['role_id'])
        print(f"giving role {role} to {member}")
        await member.add_roles(role)
        await self.execute_step(member, step_num + 1)

    async def execute_take_role(
        self,
        member: discord.Member,
        step_num: int,
        step
    ):
        role = member.guild.get_role(step['role_id'])
        print(f"taking role {role} from {member}")
        await member.remove_roles(role)
        await self.execute_step(member, step_num + 1)

    async def execute_reaction(
        self,
        member: discord.Member,
        step_num: int,
        step
    ):
        self.bot.db.verification_system.update_one(
            {'member_id': member.id, 'guild': member.guild.id},
            {'$set': {'wait_on': 'reaction'}}
        )

    def remove_member(self, member: discord.Member):
        print(f"removing {member}")
        self.bot.db.verification_system.delete_one(
            {'member_id': member.id, 'guild': member.guild.id}
        )


def check_emoji(emoji_id, emoji):
    emoji_id == emoji if isinstance(emoji, str) else emoji_id == emoji.id
