import discord
import os
import asyncio
import traceback
import keep_alive
import asyncer
from flask import Flask
from threading import Thread
import ast
import time
import base64
from findTime import findTime
from encryption_tools import encode, decode
from rw import read, write
from cmdDict import cmdDict
from commands import data_tweaking
from ignoredChars import ignoredChars
from phrase_spam import is_repeating
from json_store_client import *
jsonclient = AsyncClient(os.environ.get('JSON_LINK'))

key = os.environ.get('KEY')
thing = encode(key, '{}')

keyList = [
    'banWords',
    'banEmojis'
]

client = discord.Client()
@client.event
async def on_ready():
    await write('bot_prefix', '?')
    await write('spamChart', {})
    for a in keyList:
        await write(a, {}, False)

    bot_prefix = await read('bot_prefix', False)
    game = discord.Game(name='The bot prefix is: ' + bot_prefix)

    await client.change_presence(activity=game)
    print("I'm in")
    print(client.user)

@client.event
async def on_message(message):
    user = message.author



    safe = False
    guild = message.guild
    try:
        banWords = (await read('banWords', True, False))[guild.id]
    except:
        banWords = await read('banWords', True, False)

        banWords[guild.id] = []

        await write('banWords', banWords, False)
        banWords = []
    try:
        banEmojis = (await read('banEmojis', True, False))[guild.id]
    except:
        banEmojis = await read('banEmojis', True, False)
        banEmojis[guild.id] = []
        await write('banEmojis', banEmojis, False)
        banEmojis = []
    bot_prefix = await read('bot_prefix', False)
    
    channel = message.channel
    
    prefix_length = len(bot_prefix)
    if message.author != client.user:
        try:
            base_duration = (await read('duration'))[guild.id]
        except:
    
            bd = await read('duration')
            bd[guild.id] = 5
            await write('duration', bd)
            base_duration = 5

        try:
            offenseDuration = (await read('od'))[guild.id]
        except KeyError:
            od = await read('od')
            od[guild.id] = 5
            await write('od', od)
            offenseDuration = (await read('od'))[guild.id]
        moderator = discord.utils.get(message.guild.roles, id=525677521430118411)
        content = message.content
        user = message.author
        try:
            mri = (await read('mute-role-id'))[guild.id]
        except:
            await channel.send('No muted role set!')
            pass
        
        
        if guild.id == 437048931827056642and user.guild_permissions.administrator or user.id == 487258918465306634:
            if content.startswith(bot_prefix):
                if content[prefix_length:].startswith('eval'):
                    content = content.replace(' ', '|', 1).split('|')
                    try:
                        await channel.send(eval(content[1]))
                    except discord.errors.HTTPException:
                        await channel.send('Task completed')
        if guild.id == 437048931827056642 and user.guild_permissions.administrator:
            
            if content.startswith(bot_prefix):
                if content[prefix_length:].startswith('prefix'):
                    await write('bot_prefix', str(content[prefix_length+7:]))
                    await channel.send('The Bot prefix is now ' + str(content[prefix_length+7:]))
                    bot_prefix = await read('bot_prefix', False)
                    game = discord.Game(name='The bot prefix is: ' + bot_prefix)
                    await client.change_presence(activity=game)
        content = message.content

        if user.guild_permissions.administrator or moderator in user.roles:

                
            if content.startswith(bot_prefix):
                cmd = content[prefix_length:].lower().split(' ')[0].lower()
                if cmd in cmdDict:
                    args = content[prefix_length+len(cmd)+1:].split(' ')
                    print(content[prefix_length+len(cmd)+1:].split(' '))
                    await cmdDict[cmd](args, message)
                if content[prefix_length:].lower().startswith('muteid'):
                    content = content.split(' ')
                    muteIds = await read('mute-role-id')
                    muteIds[guild.id] = int(content[1])
                    await write('mute-role-id', muteIds)
                
                elif content[prefix_length:].startswith('permamute'):
                    content = content.replace(' ', '|||||', 2)
                    content = content.split('|||||')
                    if len(content) == 3:
                        if content[1][:3] != '<@!':
                            userId = int(content[1][2:][:-1])
                        else:
                            userId = int(content[1][3:][:-1])
                        muted = discord.utils.get(guild.roles, id=mri)
                        muteUser = guild.get_member(userId)
                        await muteUser.add_roles(muted, reason=content[2])
                        await channel.send(muteUser.display_name + ' has been muted')
                    elif len(content)==2:
                        if content[1][:3] != '<@!':
                            userId = int(content[1][2:][:-1])
                        else:
                            userId = int(content[1][3:][:-1])
                        muted = discord.utils.get(guild.roles, id=mri)
                        muteUser = guild.get_member(userId)
                        await muteUser.add_roles(muted, reason=user.display_name + ' muted him/her')
                        await channel.send(muteUser.display_name + ' has been muted')
                    else:
                        await channel.send(f'Invalid syntax. Example: {bot_prefix}mute @jon bc i can lol')
                elif content[prefix_length:].lower().startswith('banlist'):
                    msg = '```fix\nWords:\n' + '\n'.join(banWords) + '\n' + 'Reactions:\n' + '\n'.join(banEmojis) + '\n```'
                    await channel.send(msg)
                elif content[prefix_length:].lower().startswith('banword'):
                    content = content.replace(' ', '|\||\``\|', 1).split('|\||\``\|')
                    banWords.append(content[1].lower())
                    fullBanWords = await read('banWords')
                    fullBanWords[guild.id] = banWords
                    await write('banWords', fullBanWords)
                    await channel.send('`' + content[1] + '` Has been banned')
                    safe = True
                elif content[prefix_length:].lower().startswith('unbanword'):
                    content = content.replace(' ', '|\||\``\|', 1).split('|\||\``\|')
                    try:
                        banWords.remove(content[1].lower())
                        fullBanWords = await read('banWords')
                        fullBanWords[guild.id] = banWords
                        await write('banWords', fullBanWords)
                        await channel.send('`' + content[1] + '` Has been unbanned')   
                    except:
                        await channel.send(content[1].lower() + ' is not in the banlist.')
                    safe = True
                elif content[prefix_length:].lower().startswith('banreaction'):
                    content = content.replace(' ', '|\||\``\|', 1).split('|\||\``\|')
                    banEmojis.append(content[1])
                    fullBanEmojis = await read('banEmojis', True, False)
                    fullBanEmojis[guild.id] = banEmojis
                    await write('banEmojis', fullBanEmojis, False)
                    await channel.send('`' + content[1] + '` reaction been banned')
                elif content[prefix_length:].lower().startswith('unbanreaction'):
                    content = content.replace(' ', '|\||\``\|', 1).split('|\||\``\|')
                    try:
                        banEmojis.remove(content[1])
                        fullBanEmojis = await read('banEmojis', True, False)
                        fullBanEmojis[guild.id] = banEmojis
                        await write('banEmojis', fullBanEmojis, False)
                        await channel.send('`' + content[1] + '` reaction been unbanned')
                    except ValueError:
                        await channel.send('`' + content[1] + '` is not in the reaction list!')
                    except:
                        await channel.send('An unknown error occured.')
                elif content[prefix_length:].split(' ')[0] == 'mute':
                    content = content.replace(' ', '|||||', 3)
                    content = content.split('|||||')
                    if len(content) == 4:
                        if content[1][:3] != '<@!':
                            userId = int(content[1][2:][:-1])
                        else:
                            userId = int(content[1][3:][:-1])
                        muted = discord.utils.get(guild.roles, id=mri)
                        muteUser = guild.get_member(userId)
                        await muteUser.add_roles(muted, reason=content[3])
                        await channel.send(muteUser.display_name + ' has been muted')
                        
                        await asyncio.sleep(findTime(content[2]))

                        await muteUser.remove_roles(muted, reason='Mute time has ended')
                        await channel.send('<@!' + str(muteUser.id) + '>  has been unmuted, because his/her time is up.')
                    elif len(content)==3:
                        if content[1][:3] != '<@!':
                            userId = int(content[1][2:][:-1])
                        else:
                            userId = int(content[1][3:][:-1])
                        muted = discord.utils.get(guild.roles, id=mri)
                        muteUser = guild.get_member(userId)
                        await muteUser.add_roles(muted, reason=user.display_name + ' muted him/her')
                        await channel.send(muteUser.display_name + ' has been muted')
                        await asyncio.sleep(findTime(content[2]))

                        await muteUser.remove_roles(muted, reason='Mute time has ended')
                        await channel.send('<@!' + str(muteUser.id) + '>  has been unmuted, because his/her time is up.')
                    else:
                        await channel.send(f'Invalid syntax. Example: {bot_prefix}mute @jon 1 bc i can lol')
                elif content[prefix_length:].startswith('unmute'):
                    content = content.replace(' ', '|||||', 2)
                    content = content.split('|||||')
                    if len(content) == 3:
                        if content[1][:3] != '<@!':
                            userId = int(content[1][2:][:-1])
                        else:
                            userId = int(content[1][3:][:-1])
                        muted = discord.utils.get(guild.roles, id=mri)
                        muteUser = guild.get_member(userId)
                        await muteUser.remove_roles(muted, reason=content[2])
                        await channel.send('<@!' + str(muteUser.id) + '> has been unmuted')
                    elif len(content) == 2:
                        if content[1][:3] != '<@!':
                            userId = int(content[1][2:][:-1])
                        else:
                            userId = int(content[1][3:][:-1])
                        muted = discord.utils.get(guild.roles, id=mri)
                        muteUser = guild.get_member(userId)
                        await muteUser.remove_roles(muted, reason=user.display_name + ' unmuted him/her')
                        await channel.send('<@!' + str(muteUser.id) + '> has been unmuted')
                    else:
                        await channel.send(f'Invalid syntax. Example: {bot_prefix}unmute @jon bc i can lol')
        content = message.content.lower()
        for char in ignoredChars:
                content = content.replace(char, '')

        if not safe:

            for a in banWords:
                a = a.lower()
                if ' ' + a + ' ' in content or content.startswith(a) or content.endswith(a):
                    await message.delete()
                    await channel.send('That word is not allowed!')
        guildId = guild.id
        userId = user.id
        offenseLimit = 5
        mute_duration = base_duration
        try:
            mri = (await read('mute-role-id'))[guild.id]
        except:
            pass
        spamChart = await read('spamChart')

        if guildId not in spamChart:
            spamChart[guildId] = {}
        if userId not in spamChart[guildId]:
            spamChart[guildId][userId] = 1
        else:
            spamChart[guildId][userId] += 1
        if offenseLimit - 1 == spamChart[guildId][userId]:
            await channel.send(f'<@!{str(userId)}> please stop spamming. You have been warned')
        if offenseLimit == spamChart[guildId][userId]:
            muted = discord.utils.get(guild.roles, id=mri)
            await user.add_roles(muted, reason='User was spamming')
            await message.delete()
            await asyncio.sleep(mute_duration)
           
            if mri in [y.id for y in user.roles]:
                await channel.send(str(user.display_name + ' has been  unmuted'))
            await user.remove_roles(muted, reason='Mute duration has ended')
            spamChart = await read('spamChart')
            try:
                if spamChart[guildId][userId] >= offenseLimit:
                    await message.delete()
            except KeyError:
                pass
            spamChart[guildId][userId] -= 1
            if spamChart[guildId][userId] == 0:
                del spamChart[guildId][userId]
            await write('spamChart', spamChart)
        else:
            await write('spamChart', spamChart)
            await asyncio.sleep(offenseDuration)
            spamChart = await read('spamChart')
            if mri in [y.id for y in message.author.roles]:
                await message.delete()
            spamChart[guildId][userId] -= 1
            if spamChart[guildId][userId] == 0:
                del spamChart[guildId][userId]
            await write('spamChart', spamChart)

        delete = False
        newline = '''
'''
        def check(m):
            return m.content == 'hello' and m.channel == channel

        try:
            
            yesAnnotherThing = str(repr(content).encode('ascii'))

            if not content.replace(newline, '\n') in (yesAnnotherThing).replace('\\n', '\n'):
                await message.delete()
                await channel.send(f'Illegal character detected in <@!{user.id}>\'s message.')
        except UnicodeEncodeError:
            pass
        
        nextMsg = await client.wait_for('message', check=lambda message: message.author == user)

        msgList = [message]
        count = 0
        done = False
        unusedWords = []
        content = str(content+nextMsg.content)
        for char in ignoredChars:
                content = content.replace(char, '')
        for a in banWords:
            a = a.lower()
            if ' ' + a + ' ' in content or content.startswith(a) or content.endswith(a):
                await message.delete()
                await nextMsg.delete()
                await channel.send('That word is not allowed!')
        
                    
        
@client.event
async def on_reaction_add(reaction, user):
    banEmojis = await read('banEmojis', True, False)
    guild = reaction.message.guild
    if str(reaction) in banEmojis[guild.id]:
        await reaction.remove(user)
        await reaction.message.channel.send(f'<@!{str(user.id)}> That reaction is banned!')
    


keep_alive.keep_alive()


token = os.environ.get("DISCORD_BOT_SECRET")
client.run(token)