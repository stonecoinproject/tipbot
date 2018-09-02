from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import json
import requests
import asyncio
from decimal import Decimal
import discord
from discord.ext import commands


class Exchange:
    global config
    def __init__(self, config):
        Exchange.config = config

    async def getaddress(self,userid, coin):
        
        address = coin.getaddressesbyaccount(userid)

        #if address dont exist create it
        if len(address) == 0:
            address = coin.getnewaddress(userid)
            if(len(address) == 0):
                return False
            else:
                address = address
        return address

    async def getDepositAdresses(self, user,coins,addresses,rate,embed, ctx):
        retval = ""
        fee = "0.00%"
        for coin in Exchange.config.coins:
            if( coin.deposit and coin.enabled):
                d = AuthServiceProxy("http://%s:%s@%s"%(coin.user, coin.password, coin.host))
                address = await self.getaddress(str(user.id), d)
                if(address):
                    coins += "\n" + coin.token
                    addresses += "\n" + str(address[0])
                    if(coin.token == "BTC"):
                        rate += "\n" + "1.00000000 BTC"
                    else:    
                        rate += "\n" + str(round(Decimal(coin.last),8)) + " BTC"
                    
                    fee += "\n" + str(coin.exfee) + "%"

        embed.add_field(name =  "__Coin__",value = "**" + coins + "**",inline=True) 
        embed.add_field(name =  "__Address__",value = "**" + addresses + "**",inline=True) 
        await ctx.message.channel.send(embed = embed)           

        embed=discord.Embed()
        embed.footer.text = "\u00A9 "
        embed.title = "**:bank::moyai: **STONE Exchange Rate!** :moyai::bank:**"
        embed.color = 1363892
        embed.add_field(name =  "__Coin__",value = "**" + coins + "**",inline=True) 
        embed.add_field(name =  "__Rate__",value = "**" + str(rate) + "**",inline=True) 
        embed.add_field(name =  "__Fee__",value = "**" + str(fee) + "**",inline=True)
        await ctx.message.channel.send(embed = embed)           

        #dummy return for await
        return True

    async def exchange(self, userid, stonedaemon, ctx):
        
        for coin in Exchange.config.coins:
            if(coin.enabled and coin.deposit):
                d = AuthServiceProxy("http://%s:%s@%s"%(coin.user, coin.password, coin.host))
                
                #get addresses and current balances to make sure we have the coins needed to complete the exchange
                #main address is the address to store all coins on, this is the exchange address
                user_adr = await self.getaddress(userid,d)
                main_adr = await self.getaddress("main",d)
                user_amount = d.getbalance(userid)
                stone_main_balance = stonedaemon.getbalance("main")
                
                if(user_amount > 0):
                    if(coin.token == "BTC"):
                        total_btc = user_amount
                    else:
                        total_btc = user_amount * coin.last

                    #withdraw the exchange fee
                    fee = Decimal(total_btc) * Decimal(coin.exfee)
                    total_btc = Decimal(total_btc) - fee
                    stone_needed = Decimal(total_btc) / Decimal(Exchange.config.stone.last)
                    stone_fee = Decimal(fee) / Decimal(Exchange.config.stone.last)
                    if(stone_needed > stone_main_balance):
                        #we may still have enough to exchange other coins so continue the loop
                        await ctx.message.channel.send("Notify admin, Exchange is low on STONE")
                        continue
                    else:
                        #move deposited coins to main exchange address and move stone to the users address
                        if(d.move(userid,"main", user_amount)):
                            if(stonedaemon.move("main", userid, stone_needed) == False):
                                #exchange failed so move deposited coins back to the user address so we can try again later
                                d.move("main",userid, user_amount)
                                
                                await ctx.message.channel.send("Notify admin, Exchange failed to transfer STONE")
                            else:
                                embed=discord.Embed()
                                embed.footer.text = "\u00A9 "
                                embed.title = "**:moyai::moneybag: **STONE Exchange!** :moneybag::moyai:**"
                                embed.color = 1363892
                                embed.add_field(name="__From__",value=coin.token,inline=True) 
                                embed.add_field(name =  "__Amount__",value = " **" + str(round(user_amount,8)) + " " + coin.token + "**",inline=True)
                                embed.add_field(name =  "__Fee__",value = " **" + str(coin.exfee) + "%**",inline=True)
                                
                                embed.add_field(name="__To__",value="STONE",inline=True) 
                                embed.add_field(name =  "__Amount__",value = " **" + str(round(stone_needed,8)) + "**",inline=True)
                                embed.add_field(name =  "__Fee__",value = " **" + str(round(stone_fee,8)) + " STONE**",inline=True)
                                await ctx.message.channel.send(embed=embed)


    #Update coin prices from CB
    class ExchangePricing:
        """Handles interactions with the discordbots.org API"""

        def __init__(self, bot, config):
            self.bot = bot
            self.updating = bot.loop.create_task(self.price_loop())
        
        async def price_loop(self):
           
            while True:
                try:
                    # Get all pairs from CryptoBridge exchange
                    tok_response = requests.get(url='https://api.crypto-bridge.org/api/v1/ticker')
                    tok_response.close()
                    tok_data = tok_response.json()

                    for line in tok_data:
                        if line["id"] == Exchange.config.stone.token + "_BTC":
                            
                            Exchange.config.stone.ask = line["ask"]
                            Exchange.config.stone.bid = line["bid"]
                            Exchange.config.stone.last = line["last"]
                            print("Updated market price: " + Exchange.config.stone.token + " ask: " +Exchange.config.stone.ask + " bid: " + Exchange.config.stone.bid + " last: " + Exchange.config.stone.last + "\n")
                         
                        for i in range(len(Exchange.config.coins)):
                            if line["id"] == Exchange.config.coins[i].token + "_BTC":
                                Exchange.config.coins[i].ask = line["ask"]
                                Exchange.config.coins[i].bid = line["bid"]
                                Exchange.config.coins[i].last = line["last"]
                                print("Updated market price: " + Exchange.config.coins[i].token + " ask: " + Exchange.config.coins[i].ask + " bid: " + Exchange.config.coins[i].bid + " last: " + Exchange.config.coins[i].last + "\n")
                        
                except Exception as e:
                    logger.exception('Failed to get market price\n{}: {}'.format(type(e).__name__, e))
                
                #update every 1 hour
                await asyncio.sleep(60*60)