import disnake, json
from disnake.ext import commands
import asyncio

class Mute(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        with open('config.json') as f:
            self.configs = json.load(f)

    @commands.command(name="mute", description="Commande pour rendre muet")
    @commands.has_permissions(administrator=True)
    async def mute(self, ctx, member: disnake.Member, *, reason="Aucune raison donnée"):
        muted_role = disnake.utils.get(ctx.guild.roles, name="Mute")
        if not muted_role:
            muted_role = await ctx.guild.create_role(name="Mute")
            for channel in ctx.guild.channels:
                await channel.set_permissions(muted_role, speak=False, send_messages=False, read_message_history=True, read_messages=True)
        await member.add_roles(muted_role, reason=reason)
        await ctx.send(f"{member.mention} a été rendu muet \n Raison: {reason}")

    @commands.command(name="unmute", description="Commande pour annuler le mute")
    @commands.has_permissions(administrator=True)
    async def unmute(self, ctx, member: disnake.Member):
        muted_role = disnake.utils.get(ctx.guild.roles, name="Mute")
        if muted_role in member.roles:
            await member.remove_roles(muted_role)
            await ctx.send(f"{member.mention} n'est plus muet")
        else:
            await ctx.send(f"{member.mention} n'est pas muet.")

    @commands.command(name="tempmute", description="Commande pour rendre muet temporairement")
    @commands.has_permissions(administrator=True)
    async def tempmute(self, ctx, member: disnake.Member, time: int, *, reason=None):
        muted_role = disnake.utils.get(ctx.guild.roles, name="Mute")
        if not muted_role:
            muted_role = await ctx.guild.create_role(name="Mute")
            for channel in ctx.guild.channels:
                await channel.set_permissions(muted_role, speak=False, send_messages=False, read_message_history=True, read_messages=True)
        await member.add_roles(muted_role, reason=reason)
        await ctx.send(f"{member.mention} a été rendu muet pour {time} secondes pour {reason}")
        await asyncio.sleep(time)
        if muted_role in member.roles:
            await member.remove_roles(muted_role, reason="Le temps de mute temporaire est écoulé.")
            await ctx.send(f"{member.mention} n'est plus muet.")

def setup(bot: commands.Bot):
    bot.add_cog(Mute(bot))
    print("Mute cog is loaded")

def teardown(bot):
    bot.remove_cog("Mute")
    print("Mute cog is unloaded")