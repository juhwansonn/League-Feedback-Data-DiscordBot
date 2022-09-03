#reference: https://hextechdocs.dev/how-to-verify-your-application-using-github/

import discord
import os
import requests
from dotenv import load_dotenv
from discord.ext import commands
from datetime import date
import json
import datetime
load_dotenv()

#get discord token and riot api key from .env file
TOKEN = os.environ['DISCORD_TOKEN']
APIKEY = os.environ['APIKEY']

#each server should have different reported db
class Server:
    def __init__(self):
        self.report = {} #{reportedid:[reporter,date,reason]}

servers = {}
bot = commands.Bot(command_prefix='&', description='db for discord server')
@bot.event
async def on_ready():
    GUILD = []
    async for guild in bot.fetch_guilds(limit=150):
        servers[guild.name] = Server()
        GUILD.append(guild.name)    
    #which guild use this discord bot : now only HAN server
    print(f"Allowed servers: {GUILD}")
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('-'*20)
    await bot.change_presence(activity=discord.Game(name='&help'))
    
@bot.command(name='test', aliases=['t','Test','T'], help='For test')
async def test(ctx):
    print ("check")
    await ctx.send("test!!!")

#report user to DB
@bot.command(name='report', aliases=['r','Report','R'], help='Reporting league user')
async def report(ctx, *reporting):
    """
    1. self.report에 저장 
    2. text file에 저장 
    &report Kevin Kookies, 분당 와드 한개
    Kevin Kookies, 분당 와드 한개
    self.report = {} #{reportedid:[reporter,date,reason]} 
    """
    #  &report Kevin Kookies, 분당 와드 한개
    reportingline = ' '.join(reporting)
    await ctx.send(reportingline)
    id_and_reason = reportingline.split(', ')
    reportedid = id_and_reason[0]
    reason = id_and_reason[1]
    summonerInfo = (requests.get('https://'+'na1'+'.api.riotgames.com/lol/summoner/v4/summoners/by-name/' + reportedid + '?api_key=' + APIKEY)).json()
    puuid = summonerInfo['puuid']
    servers[ctx.message.guild.name].report[puuid] = [ctx.author, datetime.datetime.now(), reason]
    with open ('data.txt', 'a') as data:
        data.write(str(puuid) + "/" + str(ctx.author) + '/' + str(datetime.datetime.now()) + '/' + reason + '\n')
    data.close()

#search user in DB
@bot.command(name='search', aliases=['s','Search','S'], help='Searching users in the dict')
async def search(ctx, *searching):
    searchingline = ' '.join(searching)
    users = searching.split(' joined the lobby')
    puuids = []
    for user in users:
        puuids.append((requests.get('https://'+'na1'+'.api.riotgames.com/lol/summoner/v4/summoners/by-name/' + user + '?api_key=' + APIKEY)).json())
    if len(puuids) != 5:
        ctx.send('Error: Missing Info. Copy and paste summoner infos again.')
        # raise ValueError('')
        return 
    await ctx.send(searchingline)
    with open ('data.txt', 'r') as data:
        for line in data:
            info = line.split('/')
            for puuid in puuids:
                if puuid == info[0]:
                    is_present = True
                    ctx.send(info[-1])
        if not is_present:
            return ctx.send('Users do not exist in the database. You are good to play!')
    data.close()

#just for fun. mimicing multisearch. very slow
@bot.command(name='match', aliases=['m','Match','M'], help='Match history for searched user')
async def match(ctx, *searching):
    searchingline = ' '.join(searching)
    print(searchingline)
    joincnt = searchingline.count('joined the lobby')
    joinppl = []
    oneppl = ''
    for oneterm in searching:
        if oneterm == 'joined':
            joinppl.append(oneppl)
            oneppl = ''
        elif oneterm == 'lobby':
            oneppl = ''
        else:
            oneppl = oneppl + oneterm
    multisearch = {}
    for idx, person in enumerate(joinppl):
        summonerInfo = (requests.get('https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-name/' + person + '?api_key=' + APIKEY)).json()
        if len(summonerInfo)<=1:
            print('There is no such username ' + person)
            await ctx.send('There is no such username ' + person)
        else:
            puuid = summonerInfo['puuid']
            matchhistory = (requests.get('https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/'+puuid+'/ids?type=ranked&start=0&count=5' + '&api_key=' + APIKEY)).json()
            #print(matchhistory)
            for match in matchhistory:
                prev = (requests.get('https://americas.api.riotgames.com/lol/match/v5/matches/'+match+'?api_key=' + APIKEY)).json()
                participantinfo = prev['info']['participants']
                for eachparti in participantinfo:
                    if eachparti['puuid'] == puuid:
                        if eachparti['win'] == 1:
                            win = 'win'
                        else:
                            win = 'lose'
                        if eachparti['summonerName'] in multisearch.keys():
                            multisearch[eachparti['summonerName']].append([win, eachparti['championName'], eachparti['kills'], eachparti['deaths'], eachparti['assists']])
                        else:
                            multisearch[eachparti['summonerName']] = [[win, eachparti['championName'], eachparti['kills'], eachparti['deaths'], eachparti['assists']]]
                        
                        # print(eachparti['summonerName'])
                        # print(eachparti['win'])
                        # print(eachparti['championName'])
                        # print(eachparti['killingSprees'])
                        # print(eachparti['kills'])
                        # print(eachparti['deaths'])
                        # print(eachparti['assists'])
                        # print(eachparti['basicPings'])
                        # print(eachparti['challenges']['enemyJungleMonsterKills'])
                        # print(eachparti['challenges']['soloKills'])
                        # print(eachparti['challenges']['alliedJungleMonsterKills'])
    print(json.dumps(multisearch,sort_keys=True, indent=4))
    await ctx.send(multisearch)


bot.run(TOKEN)