import discord
from discord.ext import commands
import dbl
import aiohttp
import asyncio
import logging
import json
import random
from config import Config as cfg

from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from decimal import Decimal

import exchange as ex

ex = ex.Exchange(cfg)
description = '''Stone Tip-Bot'''
bot = commands.Bot(command_prefix='?', description=description)

global logger


class soakobj:
    member = {}
    address = ""


class DiscordBotsOrgAPI:
    """Handles interactions with the discordbots.org API"""

    def __init__(self, bot):
        self.bot = bot
        self.token = 'dbl_token'  #  set this to your DBL token
        self.dblpy = dbl.Client(self.bot, self.token, loop=bot.loop)
        self.updating = bot.loop.create_task(self.update_stats())

    async def update_stats(self):
        """This function runs every 30 minutes to automatically update your server count"""
        await self.bot.is_ready()
        while not bot.is_closed():
            logger.info('Attempting to post server count')
            try:
                await self.dblpy.post_server_count()
               
            except Exception as e:
                logger.exception('Failed to post server count\n{}: {}'.format(type(e).__name__, e))
            await asyncio.sleep(1800)


def setup(bot):
    logger = logging.getLogger('bot')
    bot.add_cog(DiscordBotsOrgAPI(bot))


""" Custom function to allow check for Digit with decimals """
def isNumeric(value):
    isdecimal = False
    try:
        t = Decimal(value)
        isdecimal = True
    except Exception as e:
        isdecimal = False
    return isdecimal


def txLink(txId):
    return 'http://explorer.stonecoin.rocks/tx/' + txId


def addyLink(address):
    return 'http://explorer.stonecoin.rocks/address/' + address


@bot.command(pass_context=True)
async def balance(ctx):
    """Check account balance."""
    stone = AuthServiceProxy("http://%s:%s@%s"%(cfg.stone.user, cfg.stone.password,cfg.stone.host))
    if len(ctx.message.mentions) > 0:
        user = ctx.message.mentions[0]
    else:
        user = ctx.message.author
 
    await ex.exchange(str(user.id),stone,ctx)

    balance = stone.getbalance(str(str(user.id)))
    if not balance:
       balance = "0.0000000"

    embed=discord.Embed()
    embed.footer.text = "\u00A9 "
    embed.title = "**:moyai::moneybag: **STONE Balance!** :moneybag::moyai:**"
    embed.color = 1363892
    embed.add_field(name="__User__",value="<@" + str(user.id) + ">",inline=False) 
    embed.add_field(name =  "__Balance__",value = " STONE **" + str(balance) + "**",inline=False) 
    await ctx.message.channel.send(embed=embed)


async def getaddress(userid, coin):
    stone = AuthServiceProxy("http://%s:%s@%s"%(cfg.stone.user, cfg.stone.password,cfg.stone.host))
    address = coin.getaddressesbyaccount(userid)
    if len(address) == 0:
        address = coin.getnewaddress(userid)
        if(len(address) == 0):
            return False
        else:
            address = [address]
    return address


@bot.command(pass_context=True)
async def deposit(ctx):
    """Get address for deposit."""
    stone = AuthServiceProxy("http://%s:%s@%s"%(cfg.stone.user, cfg.stone.password,cfg.stone.host))
    address = await getaddress(str(ctx.message.author.id), stone)
        
    if(address == False):
        await ctx.message.channel.send("Error getting your STONE deposit address.", delete_after = 10)
        return
    
    embed=discord.Embed()
    embed.footer.text = "\u00A9 "
    embed.title = "**:bank::moyai: **STONE Address!** :moyai::bank:**"
    embed.color = 1363892
    embed.add_field(name =  "__User__",value = "<@" + str(ctx.message.author.id) + ">",inline=False) 
    
    addresses = address[0] 
    coins = "STONE"
    rate = str(round(Decimal(ex.config.stone.last),8)) + " BTC"

    await ex.getDepositAdresses(ctx.message.author,coins,addresses,rate, embed, ctx)


@bot.command(pass_context=True)
async def withdraw(ctx, address, amount):
    """ Withdraw funds """
    stone = AuthServiceProxy("http://%s:%s@%s"%(cfg.stone.user, cfg.stone.password,cfg.stone.host))
    user = ctx.message.author

    if(not amount):
        await ctx.message.channel.send("Specify a amount -> Usage: withdraw <address> <amount>", delete_after=10)
        return

    if(not isNumeric(amount) or amount == "0"):
        await ctx.message.channel.send("Invalid amount -> Usage: withdraw <address> <amount>", delete_after=10)
        return

    if(Decimal(amount) < 0):
        await ctx.message.channel.send("Amount must be higher then 0 -> Usage: withdraw <address> <amount>", delete_after=10)
        return

    balance = stone.getbalance(str(user.id))
    if((not balance) or (balance < Decimal(amount) + Decimal(cfg.stone.txfee))):
        await ctx.message.channel.send("Not enough funds, leave " + str(cfg.stone.txfee) + " for transaction fee", delete_after=10)
        return
    
    if (not address or len(address) < 5):
        await ctx.message.channel.send("Usage: withdraw <address> <amount>", delete_after=10)
        return

    txid = stone.sendfrom(str(user.id),address,amount,6)    
    if(txid):
        embed = discord.Embed()
        embed.footer.text = "\u00A9 "
        embed.title = ":outbox_tray::money_with_wings::moneybag:**STONE Transaction Completed!:moneybag::money_with_wings::outbox_tray:**"
        embed.color = 1363892
        embed.add_field(name =  "__Sender__",value = "<@" + str(user.id) + ">",inline=True) 
        embed.add_field(name =  "__Receiver__",value = "**" + address + "**\n" + addyLink(address),inline=True)
        embed.add_field(name =  "__txid__",value = "**" + txid + "**\n" + txLink(txid),inline=False)
        embed.add_field(name = '__Amount__',value = '**' + str(amount) + ' STONE**',inline = True)
        embed.add_field(name = '__Fee__',value = '**' + str(cfg.stone.txfee) + '**',inline = True)
        await ctx.message.channel.send(embed=embed)
    else:
        await ctx.message.channel.send("Transaction failed, Make sure if you deposited the transaction has 6 confirms", delete_after=10)


def hasRole(member, role):
    if(role == ""):
        return True

    for r in member.roles:
        if(role[3:-1] == str(r.id)):
            return True

    return False        


@bot.command(pass_context=True)
async def soak(ctx, amount, role = ""):
    """Soak. Usage: soak <amount> [<role>]"""
    stone = AuthServiceProxy("http://%s:%s@%s"%(cfg.stone.user, cfg.stone.password,cfg.stone.host))
    user = ctx.message.author
    
    await ex.exchange(str(user.id),stone,ctx)

    if(not amount):
        await ctx.message.channel.send("Specify a amount -> Usage: soak <amount>", delete_after=10)
        return

    if(not isNumeric(amount) or amount == "0"):
        await ctx.message.channel.send("Invalid amount -> Usage: soak <amount>", delete_after=10)
        return

    if(Decimal(amount) < 0):
        await ctx.message.channel.send("Amount must be higher then 0 -> Usage: soak <amount>", delete_after=10)
        return

    balance = stone.getbalance(str(str(user.id)))
    if((not balance) or (balance < Decimal(amount))):
        await ctx.message.channel.send("Not enough funds to soak STONE: " + str(amount), delete_after=10)
        return

    """my_list = ctx.message.guilds.members"""
    mlist = []
    for member in ctx.message.channel.members:
        if not member.bot and member.status.value == "online" and member.id != ctx.message.author.id:
            if(hasRole(member,role) or role == "@here" or role == "@everyone"):
                tes = soakobj()
                tes.member = member
                tes.address = ""
                mlist.append(tes)
    
    if(len(mlist) == 0):
        return
   
    receiver = ""
    i = 0
    result = True
    tpay = Decimal(amount) / len(mlist)

    header = "<@" + str(ctx.message.author.id) + "> Sent **" + str(tpay) + "**  Stone   to: "   

    for member in mlist:
        member.address = await getaddress(str(member.member.id), stone)
     
        if(not stone.move(str(ctx.message.author.id), str(member.member.id), Decimal(tpay))):
            result = False

        if(i == 0):
            receiver = ""

        receiver += "<@" + str(member.member.id) + "> "    
        i += 1

        if(i == 90):
            embed=discord.Embed()
            embed.color = 1741945
            embed.footer.text = "\u00A9 "
            embed.author.name = "Soak!"
            embed.description = header + receiver
            await ctx.message.channel.send(embed=embed)
            i = 0

    if(i > 0):
        embed=discord.Embed()
        embed.color = 1741945
        embed.footer.text = "\u00A9 "
        embed.author.name = "Soak!"
        embed.description = header + receiver
        await ctx.message.channel.send(embed=embed)
        i = 0

    if(not result):
        await ctx.message.channel.send("Some transfers failed")


@bot.command(pass_context=True)
async def tip(ctx, target ,amount):
    """Tip a user. Usage: tip <user> <amount>"""
    stone = AuthServiceProxy("http://%s:%s@%s"%(cfg.stone.user, cfg.stone.password,cfg.stone.host))
    user = ctx.message.author

    await ex.exchange(str(user.id),stone,ctx)

    if (not target or len(target) < 5):
        await ctx.message.channel.send("Usage: tip <user> <amount>", delete_after=10)
        return
    
    target =  target[2:-1]

    if( not target.isdigit()):
        await ctx.message.channel.send("Invalid user -> Usage: tip <user> <amount>", delete_after=10)
        return
    
    if(not amount):
        await ctx.message.channel.send("Specify a amount -> Usage: tip <user> <amount>", delete_after=10)
        return

    if(not isNumeric(amount) or amount == "0"):
        await ctx.message.channel.send("Invalid amount -> Usage: tip <user> <amount>", delete_after=10)
        return

    if(Decimal(amount) < 0):
        await ctx.message.channel.send("Amount must be higher then 0 -> Usage: tip <user> <amount>", delete_after=10)
        return

    if target == str(user.id):
        await ctx.message.channel.send("You can not tip your self!", delete_after=10)
        return

    balance = stone.getbalance(str(user.id))
    if((not balance) or (balance < Decimal(amount))):
        await ctx.message.channel.send("Not enough funds to tip " + str(amount), delete_after=10)
        return

    """We dont need the address, but we need to know the userid has a address"""
    targetAddress = await getaddress(target, stone)
    if(targetAddress==False):
        await ctx.message.channel.send("Error getting address for user: <@" + str(target) + ">", delete_after=10)
        return

    if stone.move(str(user.id), target, str(amount)):
        embed=discord.Embed()
        embed.footer.text = "\u00A9 "
        embed.title = "**:money_with_wings::moneybag:STONE Transaction Completed!:moneybag::money_with_wings:**"
        embed.color = 1363892
        embed.add_field(name =  "__Sender__",value = "<@" + str(user.id) + ">",inline=True) 
        embed.add_field(name =  "__Receiver__",value = "<@" + target + ">",inline=True)
        embed.add_field(name = '__Amount__',value = '**' + str(amount) + ' STONE**',inline = True)
        await ctx.message.channel.send(embed=embed)
    else:
        await ctx.message.channel.send("Failed to tip " + str(amount), delete_after=10)


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(str(bot.user.id))
    print('------')
    bot.add_cog(ex.ExchangePricing(bot, cfg))
    #setup seem to fail on bot.is_ready()
    setup(bot)


bot.run(cfg.bot_token)

