from __future__ import division

import bones.bot
import bones.event
from twisted.internet import reactor

import time
from IPX.keys import PressKey, ReleaseKey

keys = {
    "down": 0x28,
    "right": 0x27,
    "up": 0x26,
    "left": 0x25,
    "a": 0x53,
    "b": 0x41,
#    "a": 0x5A,
#    "b": 0x58,
    "start": 0x0D,
    "select": 0x08,
}
keyDelay = (1000/59.97)/1000
    
class IRCPlaysPokemon(bones.bot.Module):
    def __init__(self, *args, **kwargs):
        bones.bot.Module.__init__(self, *args, **kwargs)
        self.mutedUsers = {}
        self.keyQueue = []
        #reactor.callLater(0.0, reactor.callInThread, self.keyAgent)

    @bones.event.handler(event=bones.event.UserJoinEvent)
    def voiceUser(self, event):
        if ("%s@%s" % (event.user.username, event.user.hostname)) not in self.mutedUsers:
            event.client.mode(event.channel.name, True, "v", user=event.user.nickname)
    
    @bones.event.handler(event=bones.event.PrivmsgEvent)
    def parseMessage(self, event):
        if event.msg.lower() in ["select", "start", "down", "up", "left", "right", "a", "b"]:
            key = event.msg.lower()
            PressKey(keys[key])
            time.sleep(keyDelay)
            ReleaseKey(keys[key])
            PressKey(keys[key])
            time.sleep(keyDelay)
            ReleaseKey(keys[key])
            bones.bot.log.debug("Sent %s, %s" % (key, keys[key]))
            self.keyQueue.append(event.msg.lower())
     
    def keyAgent(self):
        while True:
            if len(self.keyQueue) > 0:
                key = self.keyQueue.pop(0)
                PressKey(keys[key])
                time.sleep(keyDelay)
                ReleaseKey(keys[key])
                bones.bot.log.debug("Sent %s, %s" % (key, keys[key]))
                
