from source_code.data import db_session
from discord.ext import commands, tasks
from source_code.data.users import Users
from source_code.data.privileges import Privileges
from source_code.constants import MAIN_DISCORD_GUILD_ID
from source_code.bots.discord.discord_bot import DiscordBot


class DiscordCommands(commands.Cog):
    def __init__(self, bot: DiscordBot):
        self.bot = bot
        self.update_roles_loop.start()

    # получение id сервера/гильдии
    @commands.command(name='get_server_id')
    async def get_server_id(self, ctx):
        await ctx.send(f'Server id: {ctx.guild.id}')

    # update_roles_loop, только с запуском через команду
    @commands.command(name='update_roles')
    async def update_roles(self, ctx):
        await self.update_roles_loop()
        await ctx.send(f'Роли обновлены')

    # обновление всех ролей у пользователей в дискорде каждую минуту
    @tasks.loop(minutes=1)
    async def update_roles_loop(self):
        try:
            db_sess = db_session.create_session()
        except TypeError:
            return
        all_privileges_names = [privilege.name for privilege in db_sess.query(Privileges)]
        guild = self.bot.get_guild(MAIN_DISCORD_GUILD_ID)
        discord_roles = {role.name: role for role in guild.roles}

        for member in guild.members:
            user = db_sess.query(Users).filter(Users.discord == f'{member.name}#{member.discriminator}').first()
            member_roles_names = [role.name for role in member.roles]

            # проверка, что пользователь существует
            if user is None:
                continue

            # удаление тех ролей, которые не должны быть
            user_privileges = {privilege.name: privilege for privilege in user.privileges}
            for role in member.roles:
                role_name = role.name
                # если роли нет в базе, то пропускаем
                if role_name not in all_privileges_names:
                    continue
                # удаление роли (используется asyncio)
                if role_name not in user_privileges.keys() or not user_privileges[role_name].is_displaying:
                    await member.remove_roles(role)

            # добавление тех ролей, которые должны быть
            for privilege_name, privilege in user_privileges.items():
                # если роль не должна отображаться, то пропускаем
                if not privilege.is_displaying:
                    continue
                # если роли нет в базе, то пропускаем
                if privilege_name not in discord_roles.keys():
                    continue
                # добавление роли (используется asyncio)
                if privilege_name not in member_roles_names:
                    await member.add_roles(discord_roles[privilege_name])
        db_sess.close()
