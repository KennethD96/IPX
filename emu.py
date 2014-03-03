#encoding: utf-8
from __future__ import division

import bones.bot
import bones.event

from subprocess import Popen, PIPE
from twisted.internet import reactor
from os import path
import time
import re

# Config

default_emu = "bgb.exe"
default_rom = "Pokemon Yellow.gb"
load_at_startup = True

mod_admins = ["KennethD", "_404`d"]

##########################################

module_path = path.dirname(__file__)
emu_path = path.join(module_path, "emulators")
rom_path = path.join(module_path, "roms")

if not path.exists(emu_path):
    path.mkdir(emu_path)
if not path.exists(rom_path):
    path.mkdir(rom_path)

input_enabled = False
if load_at_startup:
    input_enabled = True

def isrunning(proc):
    try:
        return proc.poll()
    except:
        return 0

class emucontrol(bones.bot.Module):
    def __init__(self, *args, **kwargs):
        bones.bot.Module.__init__(self, *args, **kwargs)
        self.active_emu = path.join(emu_path, default_emu)
        self.active_rom = path.join(rom_path, default_rom)
        self.em = None
        if load_at_startup:
            self.emustart(self.active_emu, self.active_rom)

    def emustart(self, emu, rom):
        self.em = Popen([emu, rom])
        with open(path.join(emu_path, "emu.pid"), "w") as pidfile:
            pidfile.write(str(self.em.pid))

    @bones.event.handler(trigger="emustart")
    def cmdemustart(self, event):
        global input_enabled
        if event.user.nickname in mod_admins:
            rom = self.active_rom
            if len(event.args) > 0:
                newpath = path.join(rom_path, " ".join(event.args))
                rom = newpath
                if path.exists(newpath):
                    if isrunning(self.em) == None:
                        self.em.kill()
                    try:
                        self.emustart(self.active_emu, rom)
                        event.channel.msg("Emulator loaded with ROM '%s'" %
                        " ".join(event.args))
                        input_enabled = True
                    except:
                        event.channel.msg("Could not load emulator")
                else:
                    event.channel.msg("ROM does not exist")
            else:
                if isrunning(self.em) != None:
                    try:
                        self.emustart(self.active_emu, rom)
                        input_enabled = True
                        event.channel.msg("Emulator initiated")
                    except:
                        event.channel.msg("Could not load emulator")
                else:
                    event.channel.msg("Emulator already running")

    @bones.event.handler(trigger="emurestart")
    def emurestart(self, event):
        if event.user.nickname in mod_admins:
            if isrunning(self.em) == None:
                self.em.kill()
            try:
                self.emustart(self.active_emu, self.active_rom)
                event.channel.msg("Emulator restarted")
            except:
                event.channel.msg("Could not restart emulator")

    @bones.event.handler(trigger="emustop")
    def emustop(self, event):
        global input_enabled
        if event.user.nickname in mod_admins:
            if isrunning(self.em) == None:
                input_enabled = False
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
                    newpath = path.join(emu_path, " ".join(event.args[1:]))
                    if path.exists(newpath):
                        self.active_emu = newpath
                    else:
                        event.channel.msg("Emulator does not exist, changes ignored")
                        success = False

                if event.args[0].lower() == "rom":
                    newpath = path.join(rom_path, " ".join(event.args[1:]))
                    if path.exists(newpath):
                        self.active_rom = newpath
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