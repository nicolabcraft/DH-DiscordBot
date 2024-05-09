import disnake, os, socketio, json, pprint
from disnake.ext import commands, tasks
from datetime import datetime
from uptime_kuma_api import UptimeKumaApi
from uptime_kuma_api.exceptions import UptimeKumaException, Timeout
from dotenv import load_dotenv

load_dotenv()

UPTIME_KUMA_SERVER = os.getenv('UPTIME_KUMA_SERVER')
UPTIME_KUMA_USERNAME = os.getenv('UPTIME_KUMA_USERNAME')
UPTIME_KUMA_PASSWORD = os.getenv('UPTIME_KUMA_PASSWORD')
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
COMMAND_PREFIX = os.getenv('COMMAND_PREFIX')
CHANNEL_ID = os.getenv('CHANNEL_ID')
ACTIVITY_NAME = os.getenv('ACTIVITY_NAME')
ACTIVITY_TYPE = os.getenv('ACTIVITY_TYPE')

intents = disnake.Intents.default()
intents.message_content = True
activity = disnake.Activity(
    name=ACTIVITY_NAME,
    type=disnake.ActivityType.ACTIVITY_TYPE,
)
bot = commands.Bot(command_prefix='!!', intents=intents, activity=activity)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    channel = bot.get_channel(CHANNEL_ID)  # Replace with your channel ID

    # Check if the message ID exists in a file
    try:
        with open("message_id.txt", "r") as file:
            message_id = int(file.read())
            message = await channel.fetch_message(message_id)
    except (FileNotFoundError, disnake.NotFound):
        # If the message ID does not exist or the message does not exist, send a new message
        embed = create_embed()
        message = await channel.send(embed=embed)
        with open("message_id.txt", "w") as file:
            file.write(str(message.id))

    auto_send_embed.message = message
    auto_send_embed.start()

def create_embed():
    api = None
    try:
        api = UptimeKumaApi(UPTIME_KUMA_SERVER)
        api.login(UPTIME_KUMA_USERNAME, UPTIME_KUMA_PASSWORD)

        embed = disnake.Embed(
            title='Status des serveurs',
            description='Les status sur cette page sont actualisés toutes les 60 secondes. Une version web est disponible [ici](https://status.dayhosting.fr)\n',
            color=disnake.Color.blue(),
            timestamp=datetime.now()
        )
        embed.set_thumbnail(
            url="https://cdn.discordapp.com/icons/833439085950664714/bbfb624af1ee9d6b3d2921d82102be0f.png?size=512" # Image du serveur
        )
        embed.set_author(
            name='DayHosting', # Nom de l'auteur
            url='https://dayhosting.fr', # Lien de l'auteur
            icon_url='https://cdn.discordapp.com/icons/833439085950664714/bbfb624af1ee9d6b3d2921d82102be0f.png?size=512' # Image de l'auteur
        )
        embed.set_footer(
            text=f'Dernière actualisation des données'
        )

        data = api.get_status_page("dayhosting")

        if data['maintenanceList'] != []:
            maintenances = []
            monitors_list_maintenance = []
            for i in range(len(data['maintenanceList'])):
                maintenance_id = data['maintenanceList'][i]["id"]
                maintenance_data = api.get_monitor_maintenance(maintenance_id)
                for k in range(len(maintenance_data)):
                    monitors_list_maintenance.append(maintenance_data[k]['id'])
                maintenances.append({'id': maintenance_id,'title': data['maintenanceList'][i]['title'], 'description':data['maintenanceList'][i]['description'],'monitors':monitors_list_maintenance})



        for i in range(len(data['publicGroupList'])):
            embed_title = data['publicGroupList'][i]['name']
            embed_value = ""
            for n in range(len(data['publicGroupList'][i]['monitorList'])):
                server_id = data['publicGroupList'][i]['monitorList'][n]['id']
                server_name = data['publicGroupList'][i]['monitorList'][n]['name']
                server_status = ":red_circle:"
                maintenance_status = ""
                get_server_status_id= api.get_monitor_status(server_id).value
                if get_server_status_id == 0:
                    server_status = ":red_circle:"
                elif get_server_status_id == 1:
                    server_status = ":green_circle:"
                elif get_server_status_id == 2:
                    server_status = ":yellow_circle:"
                elif get_server_status_id == 3:
                    for l in range(len(maintenances)):
                        if server_id in maintenances[l]['monitors']:
                            maintenance_status = f"\n__Raison__ :\n `{maintenances[l]['title']}`\n__Description__ :\n `{maintenances[l]['description']}`"
                    server_status = ":warning:"
                embed_value += f"{server_status} - {server_name}{maintenance_status}\n"

            embed.add_field(
                name=embed_title,
                value=embed_value,
                inline=False
            )
        embed.add_field(
            name="Légende:",
            value="<a:online:1237966542352945192> - Serveur en ligne\n<a:warning:1237966536212349010> - Serveur en attente\n<a:offline:1237966540519768144> - Serveur hors ligne\n<a:maintenance:1237966537483358228> - Serveur en maintenance\n",
            inline=False
        )
        api.logout()

    except(UptimeKumaException,Timeout,socketio.exceptions.TimeoutError) as e:
        embed = disnake.Embed(
            title='Status des serveurs',
            description='Une erreur est survenu avec la connexion a notre serveur de status, merci de patienter quelques instants ou de contacter un <@&841787186558926898>.',
            color=disnake.Color.blue(),
            timestamp=datetime.now()
        )
        if api is not None:
            api.logout()
        print(e)


    print(f"Embed updated at {datetime.now()}")

    return embed

@bot.command()
async def ping(ctx):
    await ctx.send('pong')
@bot.command()
@commands.has_permissions(administrator=True)
async def reload(ctx):
    cogs = [cog for cog in bot.cogs]
    for cog in cogs:
        try:
            bot.reload_extension(f'cogs.{cog}')
            await ctx.send(f'{cog} reloaded')
        except Exception as e:
            await ctx.send(f'{cog} failed to reload: {e}')
    await ctx.send('All cogs reloaded successfully')
@bot.command()
@commands.has_permissions(administrator=True)
async def reload_status(ctx):
    await ctx.message.delete()
    embed = create_embed()
    await auto_send_embed.message.edit(embed=embed)
    await ctx.send('Status reloaded successfully', delete_after=5)
@tasks.loop(seconds=300)
async def auto_send_embed():
    embed = create_embed()
    await auto_send_embed.message.edit(embed=embed)

bot.run('DISCORD_BOT_TOKEN')