#encoding: utf-8
from __future__ import division

from bones.bot import Module
import bones.bot
import bones.event
from keys import PressKey, ReleaseKey

from subprocess import Popen, PIPE
from twisted.internet import reactor
from os import path
import time
import re

# Config

default_emu = "bgb.exe"
default_rom = "Pokemon Yellow.gb"
load_at_startup = False
input_enabled = True

mod_admins = ["KennethD", "_404`d"]

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

##########################################

module_path = path.dirname(__file__)
emu_path = path.join(module_path, "emulators")
rom_path = path.join(module_path, "roms")
active_emu = default_emu
active_rom = default_rom

def isrunning(proc):
    try:
        return proc.poll()
    except:
        return 0

class emucontrol(Module):
    def __init__(self, *args, **kwargs):
        Module.__init__(self, *args, **kwargs)
        self.active_emu = path.join(emu_path, active_emu)
        self.active_rom = path.join(rom_path, active_rom)
        if load_at_startup:
            self.em = Popen([self.active_emu, self.active_rom])
        self.em = None

    @bones.event.handler(trigger="emustart")
    def emustart(self, event):
        if event.user.nickname in mod_admins:
            rom = self.active_rom
            if len(event.args) > 0:
                newpath = path.join(rom_path, " ".join(event.args))
                if path.exists(newpath):
                    rom = newpath
                    self.em.kill()
                    self.em = Popen([self.active_emu, rom])
                    event.channel.msg("Emulator started with rom " + rom)
                else:
                    event.channel.msg("ROM does not exist")
            else:
                if isrunning(self.em) != None:
                    self.em = Popen([self.active_emu, rom])
                    event.channel.msg("Emulator initiated")
                else:
                    event.channel.msg("Emulator already running")

    @bones.event.handler(trigger="emurestart")
    def emurestart(self, event):
        if event.user.nickname in mod_admins:
            if isrunning(self.em) == None:
                self.em.kill()
            self.em = Popen([self.active_emu, self.active_rom])
            event.channel.msg("Emulator restarted")

    @bones.event.handler(trigger="emustop")
    def emustop(self, event):
        if event.user.nickname in mod_admins:
            if isrunning(self.em) == None:
                self.em.kill()
                event.channel.msg("Emulator killed")
            else:
                event.channel.msg("Emulator not running")

    @bones.event.handler(trigger="emudebug")
    def emudebug(self, event):
        if event.user.nickname in mod_admins:
            if isrunning(self.em) == None:
                event.channel.msg("Emulator running on PID " + str(self.em.pid))
            else:
                event.channel.msg("Emulator not running")

    @bones.event.handler(trigger="emuset")
    def emuset(self, event):
        global active_emu, active_rom, input_enabled
        if event.user.nickname in mod_admins:
            success = True
            if len(event.args) > 0:
                
                if event.args[0].lower() == "emu":
                    if path.exists(path.join(emu_path, " ".join(event.args[1:]))):
                        active_emu = event.args[1]
                    else:
                        event.channel.msg("Emulator does not exist, changes ignored")
                        success = False

                if event.args[0].lower() == "rom":
                    if path.exists(path.join(rom_path, " ".join(event.args[1:]))):
                        active_rom = event.args[1]
                    else:
                        event.channel.msg("ROM does not exist, changes ignored")
                        success = False

                if event.args[0].lower() == "input":
                    if event.args[1].lower() == "true":
                        input_enabled = True
                    elif event.args[1].lower() == "false":
                        input_enabled = False
            
            if success == True:
                event.channel.msg("Changes applied successfully")

class emuinput(Module):
    def __init__(self, *args, **kwargs):
        bones.bot.Module.__init__(self, *args, **kwargs)
        global input_enabled
        self.mutedUsers = {}
        self.keyQueue = []
        #reactor.callLater(0.0, reactor.callInThread, self.keyAgent)

    @bones.event.handler(event=bones.event.UserJoinEvent)
    def voiceUser(self, event):
        if ("%s@%s" % (event.user.username, event.user.hostname)) not in self.mutedUsers:
            event.client.mode(event.channel.name, True, "v", user=event.user.nickname)
    
    @bones.event.handler(event=bones.event.PrivmsgEvent)
    def parseMessage(self, event):
        if input_enabled == True and event.msg.lower() in ["select", "start", "down", "up", "left", "right", "a", "b"]:
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