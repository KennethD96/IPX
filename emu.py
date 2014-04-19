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
input_override = None

class emucontrol(bones.bot.Module):

    active_rom = path.join(rom_path, default_rom)
    active_emu = [path.join(emu_path, default_emu), default_emu]

    def __init__(self, *args, **kwargs):
        bones.bot.Module.__init__(self, *args, **kwargs)
        self.pid_file = path.join(emu_path, "running.pid")
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
        if load_at_startup:
            input_enabled = True

    def emustart(self, emu, rom):
        global input_enabled
        if self.isrunning(self.em):
            self.killemu(self.em)
        if psutil_available:
            self.em = psutil.Popen([emu[0], rom])
            self.em_pid = [str(self.em.pid), self.em.name]
        else:
            self.em = Popen([emu[0], rom])
            self.em_pid = [str(self.em.pid), emu[1]]

        with open(self.pid_file, "w") as pidfile:
            pidfile.write("\n".join(self.em_pid))
        input_enabled = True

    def killemu(self, proc):
        global input_enabled
        proc.terminate()
        input_enabled = False

    def isrunning(self, proc):
        try:
            if psutil_available:
                return proc.is_running()
            else:
                return True if proc.poll() == None else False
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
        global input_enabled
        if event.user.nickname in mod_admins:
            if self.isrunning(self.em):
                self.killemu(self.em)
                event.channel.msg("Emulator killed")
            else:
                event.channel.msg("Emulator not running")
                input_enabled = False

    @bones.event.handler(trigger="emudebug")
    def emudebug(self, event):
        if event.user.nickname in mod_admins:
            if self.isrunning(self.em):
                event.channel.msg("Emulator running on PID " + self.em_pid[0])
            else:
                event.channel.msg("Emulator not running")

    def inputDriverEnabled(self):
        return (input_override == None or input_override == True) and input_enabled

class emuset(bones.bot.Module):
    def __init__(self, *args, **kwargs):
        bones.bot.Module.__init__(self, *args, **kwargs)

    @bones.event.handler(trigger="emuset")
    def emuset(self, event):
        global input_enabled
        if event.user.nickname in mod_admins:
            success = True
            if len(event.args) > 0:

                default_options = {
                    "emu":[path.join(emu_path, default_emu), default_emu],
                    "rom":path.join(rom_path, default_rom),
                }

                if event.args[0].lower() == "emu":
                    if event.args[1].lower() == "reset":
                        emucontrol.active_emu = default_options["emu"]
                    else:
                        newemu = " ".join(event.args[1:])
                        newpath = path.join(emu_path, newemu)
                        if path.exists(newpath):
                            emucontrol.active_emu = [newpath, newemu]
                        else:
                            event.channel.msg("Emulator does not exist, changes ignored")
                            success = False

                if event.args[0].lower() == "rom":
                    if event.args[1].lower() == "reset":
                        emucontrol.active_rom = default_options["rom"]
                    else:
                        newpath = path.join(rom_path, " ".join(event.args[1:]))
                        if path.exists(newpath):
                            emucontrol.active_rom = newpath
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

    @bones.event.handler(trigger="toggleinput")
    def toggleinput(self, event):
        global input_override
        if event.user.nickname in mod_admins:
            if input_override == False:
                input_override = True
                event.channel.msg("Input enabled")
            elif input_override == True or input_override == None:
                input_override = False
                event.channel.msg("Input disabled")
