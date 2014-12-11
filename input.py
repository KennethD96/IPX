# -*- encoding: utf-8 -*-
from __future__ import division

import logging
import time

import bones.bot
import bones.event

from keys import PressKey, ReleaseKey
import emu


class InputBase(bones.bot.Module):
    keys = {"a":None}
    keyDelay = 0

    def __init__(self, *args, **kwargs):
        bones.bot.Module.__init__(self, *args, **kwargs)
        self.emuControl = None
        self.log = logging.getLogger(__name__+"."+self.__class__.__name__)
        for module in self.factory.modules:
            if isinstance(module, InputBase):
                raise ValueError("You can only load one InputBase-derived module per factory")
            elif isinstance(module, emu.emucontrol):
                self.emuControl = module
                self.log.debug("Hooked emu.emucontrol (init)")

    @bones.event.handler(event=bones.event.BotModuleLoaded)
    def checkForEmuModule(self, event):
        if isinstance(event.module, emu.emucontrol):
            self.emuControl = event.module
            self.log.debug("Hooked emu.emucontrol (post-init)")

    @bones.event.handler(event=bones.event.ChannelMessageEvent)
    def parseMessage(self, event):
        if self.emuControl and not self.emuControl.inputDriverEnabled():
            return

        key = event.message.lower()
        if key in self.keys:
            self.receivedKeyFromIRC(key)

    def receivedKeyFromIRC(self, key):
        raise NotImplementedError("Input module does not override the receivedKeyFromIRC method.")


class GenericBGBInput(InputBase):
    keys = {
        "down": 0x28,
        "right": 0x27,
        "up": 0x26,
        "left": 0x25,
        "a": 0x53,
        "b": 0x41,
        "start": 0x0D,
        "select": 0x08,
    }
    keyDelay = (1000/59.97)/1000

    @bones.event.handler(event=bones.event.BotModuleLoaded)
    def checkForEmuModule(self, event):
        InputBase.checkForEmuModule(self, event)

    @bones.event.handler(event=bones.event.ChannelMessageEvent)
    def parseMessage(self, event):
        InputBase.parseMessage(self, event)

    def receivedKeyFromIRC(self, key):
        print bones.event.eventHandlers
        PressKey(self.keys[key])
        time.sleep(self.keyDelay)
        ReleaseKey(self.keys[key])
        PressKey(self.keys[key])
        time.sleep(self.keyDelay)
        ReleaseKey(self.keys[key])
        self.log.debug("Sent %s, %s" % (key, self.keys[key]))
