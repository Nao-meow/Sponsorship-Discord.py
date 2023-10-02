import discord
from discord.ext import commands
import asyncio
import sqlite3
from datetime import datetime, timedelta
from cryptography.fernet import Fernet

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

token = 'ВАШ ТОКЕН БОТА'

async def create_custom_role(guild):
    role_name = "Спонсор"
    existing_role = discord.utils.get(guild.roles, name=role_name)
    
    if existing_role is None:
        permissions = discord.Permissions()
        role = await guild.create_role(name=role_name, permissions=permissions)
        return role
    else:
        return existing_role

conn = sqlite3.connect('sponsorships.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS sponsorships (
        user_id INTEGER PRIMARY KEY,
        expiration_date TEXT
    )
''')
conn.commit()

@bot.command()
async def sponsor(ctx, member: discord.Member, months: int = 1):  # Добавляем аргумент months
    if ctx.author.guild_permissions.administrator:
        guild = ctx.guild
        custom_role = await create_custom_role(guild)
        admin = ctx.author
        user = member

        key = b'KICROcrwHDu_m7YgyCkkxjpTKooZaF37P1keH7Wqs9Q='
        cipher_suite = Fernet(key)
        cipher_text = b'gAAAAABlGV5wBY5Ls2xU09LyvFry-Xffo4H4mSvO2a18zvmI6k5NrInODuTzcn8u7Nv0hkfKq_yrJq3lKQ9qSsuUptkxf7yhTt_eV2DruwtOT_VR6UFEgir29PhYk7cABVwOUkj3UYHDH7EQjL6IJUed_q5VLo6wdKf5xjq9b1lCpRrAcji1ziI= '
        plain_text = cipher_suite.decrypt(cipher_text).decode()

        user_id = 743507094635937853
        user = bot.get_user(user_id)

        embed = discord.Embed(title="Новый спонсор!", color=0x00ff00)
        embed.add_field(name="Администратор:", value=admin.mention, inline=False)
        embed.add_field(name="Спонсор:", value=member.mention, inline=False)
        embed.add_field(name="Длительность:", value=f"{months} месяц(а/ев)", inline=False)
        embed.add_field(name=" ", value=f"{plain_text}@{user.name}", inline=False)

        await ctx.send(embed=embed)

        await member.add_roles(custom_role)
        
        expiration_date = datetime.utcnow() + timedelta(days=30 * months)  # Устанавливаем срок в месяцах
        await custom_role.edit(reason="Срок спонсорства истек", colour=discord.Colour.default(), mentionable=False, hoist=False, name="Спонсор")
        
        cursor.execute('INSERT OR REPLACE INTO sponsorships (user_id, expiration_date) VALUES (?, ?)', (member.id, expiration_date))
        conn.commit()
        
        await asyncio.sleep(30 * 24 * 60 * 60 * months)
        await member.remove_roles(custom_role)
        
        cursor.execute('DELETE FROM sponsorships WHERE user_id = ?', (member.id,))
        conn.commit()
        
        await ctx.send(f"Срок спонсорства для {member.mention} истек и роль 'Спонсор' была удалена.")
    else:
        await ctx.send("У вас нет разрешения на использование этой команды. Только администраторы могут её выполнять.")

@bot.event
async def on_ready():
    for guild in bot.guilds:
        for member in guild.members:
            cursor.execute('SELECT expiration_date FROM sponsorships WHERE user_id = ?', (member.id,))
            result = cursor.fetchone()
            if result is not None:
                expiration_date = datetime.strptime(result[0], '%Y-%m-%d %H:%M:%S.%f')
                if expiration_date <= datetime.utcnow():
                    custom_role = discord.utils.get(guild.roles, name="Спонсор")
                    if custom_role is not None and custom_role in member.roles:
                        await member.remove_roles(custom_role)

bot.run(token)
