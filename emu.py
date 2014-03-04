#encoding: utf-8
import bones.bot
import bones.event

from subprocess import Popen, PIPE
from twisted.internet import reactor
from os import path

try:
    import psutil
    psutil_available = True
except ImportError:
    psutil_available = False

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

class emucontrol(bones.bot.Module):
    def __init__(self, *args, **kwargs):
        bones.bot.Module.__init__(self, *args, **kwargs)
        self.active_emu = default_emu
        self.active_rom = default_rom
        self.pid_file = path.join(emu_path, "emu.pid")
        self.em_pid = []
        self.em = None

        if path.exists(self.pid_file) and psutil_available:
            with open(self.pid_file, "r") as pidfile:
                self.em_pid = pidfile.read().split("\n")
                try:
                    self.em = psutil.Process(int(self.em_pid[0]))
                    if len(self.em_pid) > 1:
                        if not self.em_pid[1] == self.em.name:
                            self.em_pid = []
                            self.em = None
                except:
                        self.em_pid = []
                        self.em = None
        
        if load_at_startup and not self.isrunning(self.em):
            self.emustart(self.active_emu, self.active_rom)

    def emustart(self, emu, rom):
        global input_enabled
        if self.isrunning(self.em):
            self.killemu(self.em)
        self.em = Popen([
            path.join(emu_path, default_emu),
            path.join(rom_path, default_rom)
        ])

        if psutil_available:
            self.em = psutil.Process(self.em.pid)
            self.em_pid = [str(self.em.pid), self.em.name]
        else:
            self.em_pid = [str(self.em.pid), self.active_emu]
        
        with open(self.pid_file, "w") as pidfile:
            pidfile.write("\n".join(self.em_pid))
        input_enabled = True

    def killemu(self, proc):
        global input_enabled
        if psutil_available:
            proc.terminate()
        else:
            proc.kill()
        input_enabled = False

    def isrunning(self, proc):
        try:
            if psutil_available:
                proc.status
                return True
            else:
                if proc.poll() == None:
                    return True
                else:
                    return False
        except:
            return False

    @bones.event.handler(trigger="emustart")
    def cmdemustart(self, event):
        if event.user.nickname in mod_admins:
            rom = self.active_rom
            if len(event.args) > 0:
                newpath = path.join(rom_path, " ".join(event.args))
                rom = newpath
                if path.exists(newpath):
                    try:
                        self.emustart(self.active_emu, rom)
                        event.channel.msg("Emulator loaded with ROM '%s'" %
                        " ".join(event.args))
                    except:
                        event.channel.msg("Could not load emulator")
                else:
                    event.channel.msg("ROM does not exist")
            else:
                if not self.isrunning(self.em):
                    try:
                        self.emustart(self.active_emu, rom)
                        event.channel.msg("Emulator initiated")
                    except:
                        event.channel.msg("Could not load emulator")
                else:
                    event.channel.msg("Emulator already running")

    @bones.event.handler(trigger="emurestart")
    def emurestart(self, event):
        if event.user.nickname in mod_admins:
            try:
                self.emustart(self.active_emu, self.active_rom)
                event.channel.msg("Emulator restarted")
            except:
                event.channel.msg("Could not restart emulator")

    @bones.event.handler(trigger="emustop")
    def emustop(self, event):
        if event.user.nickname in mod_admins:
            if self.isrunning(self.em):
                self.killemu(self.em)
                event.channel.msg("Emulator killed")
            else:
                event.channel.msg("Emulator not running")

    @bones.event.handler(trigger="emudebug")
    def emudebug(self, event):
        if event.user.nickname in mod_admins:
            if self.isrunning(self.em):
                event.channel.msg("Emulator running on PID " + self.em_pid[0])
            else:
                event.channel.msg("Emulator not running")

    @bones.event.handler(trigger="emuset")
    def emuset(self, event):
        global active_emu, active_rom, input_enabled
        if event.user.nickname in mod_admins:
            success = True
            if len(event.args) > 0:
                
                default_options = {
                    "emu":path.join(emu_path, default_emu),
                    "rom":path.join(rom_path, default_rom),
                }

                if event.args[0].lower() == "emu":
                    if event.args[1].lower() == "reset":
                        self.active_emu = default_options["emu"]
                    else:
                        newpath = path.join(emu_path, " ".join(event.args[1:]))
                        if path.exists(newpath):
                            self.active_emu = newpath
                        else:
                            event.channel.msg("Emulator does not exist, changes ignored")
                            success = False

                if event.args[0].lower() == "rom":
                    if event.args[1].lower() == "reset":
                        self.active_rom = default_options["rom"]
                    else:
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