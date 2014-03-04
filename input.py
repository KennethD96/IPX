# -*- encoding: utf-8 -*-
from __future__ import division

import time

import bones.bot
import bones.event

from keys import PressKey, ReleaseKey
import emu

class GenericBGBInput(bones.bot.Module):
    keys = {
        # 0x30 - 0x39 == 0 - 9
        "b": 0x31,
        "a": 0x32,
        "start": 0x33,
        "select": 0x34,
        "left": 0x37,
        "down": 0x38,
        "up": 0x39,
        "right": 0x30,
    }
    keyDelay = (1000/59.97)/1000

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
        if emu.input_enabled and event.msg.lower() in self.keys:
            key = event.msg.lower()
            PressKey(self.keys[key])
            time.sleep(self.keyDelay)
            ReleaseKey(self.keys[key])
            PressKey(self.keys[key])
            time.sleep(self.keyDelay)
            ReleaseKey(self.keys[key])
            bones.bot.log.debug("Sent %s, %s" % (key, self.keys[key]))
            self.keyQueue.append(event.msg.lower())

    def keyAgent(self):
        while True:
            if emu.input_enabled and len(self.keyQueue) > 0:
                key = self.keyQueue.pop(0)
                PressKey(self.keys[key])
                time.sleep(self.keyDelay)
                ReleaseKey(self.keys[key])
                bones.bot.log.debug("Sent %s, %s" % (key, self.keys[key]))

