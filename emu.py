#encoding: utf-8

# Config

default_emu = "bgb.exe" # The default emulator to use with the bot.
default_rom = "Pokemon Yellow.gb" # The default ROM to load with your emulator.
load_at_startup = True # Start emulator automatically with bot.
input_override = None # Set this to False to disable input on startup (toggleinput will set this to None).

bot_admins = [] # Will allow everyone with +o mode.
allow_all_op = True # Set this to True to allow all +o in addition to bot_admins.
check_if_op = True # Checks if everyone in bot_admins is +o.
op_mode = "o" # Mode equivalent to OP on your network.

active_rom = None
active_emu = None

##########################################

import bones.bot, bones.event, logging
from subprocess import Popen, PIPE
from twisted.internet import reactor
import os.path, time, re
import core

log = logging.getLogger(__name__)
emu_path = os.path.join(os.getcwd(), "emulators")
rom_path = os.path.join(os.getcwd(), "roms")
"""
if not os.path.exists(emu_path):
    os.mkdir(emu_path)
if not os.path.exists(rom_path):
    os.mkdir(rom_path)
"""
input_enabled = False

try:
    import psutil
    psutil_available = True
    log.debug("Found psutil. Will use to manage emulator.")
except ImportError:
    psutil_available = False


class emucontrol(bones.bot.Module):
    def __init__(self, **args):
        global input_enabled, default_emu, default_rom, load_at_startup, input_override, bot_admins, allow_all_op, check_if_op, op_mode, emu_path, rom_path, active_rom, active_emu
        bones.bot.Module.__init__(self, **args)

        self._core = None
        for module in self.factory.modules:
            if isinstance(module, core.IPXCore):
                self._core = module
        if not self._core:
            raise ValueError("IPX.core.IPXCore needs to be loaded before any other IPX module")

        bot_admins = self._core._admins
        default_emu = self._core.config("emulators", "default")
        default_rom = self._core.config("roms", "default")
        load_at_startup = bool(self._core.config("emulators", "load_at_startup"))
        input_override = bool(self._core.config("emulators", "input_override", default=True))
        emu_path = self._core.config("emulators", "path", default=emu_path)
        rom_path = self._core.config("roms", "path", default=rom_path)

        self.active_rom = os.path.join(rom_path, default_rom)
        self.active_emu = [os.path.join(emu_path, default_emu), default_emu]

        self.pid_file = os.path.join(emu_path, "running.pid")
        self.em_pid = []
        self.em = None

        if os.path.exists(self.pid_file) and psutil_available:
            with open(self.pid_file, "r") as pidfile:
                self.em_pid = pidfile.read().split("\n")
                try:
                    self.em = psutil.Process(int(self.em_pid[0]))
                    if not self.em_pid[1] == self.em.name():
                        self.em_pid = []
                        self.em = None
                except psutil.NoSuchProcess:
                        self.em_pid = []
                        self.em = None

        if load_at_startup and not self.isrunning(self.em):
            try:
                self.emustart(self.active_emu, self.active_rom)
            except WindowsError:
                log.warning("Could not find emulator executable!")
        if load_at_startup and self.isrunning(self.em):
            input_enabled = True

    def emustart(self, emu, rom):
        global input_enabled
        if self.isrunning(self.em):
            self.killemu(self.em)
        if psutil_available:
            self.em = psutil.Popen([emu[0], rom])
            self.em_pid = [str(self.em.pid), self.em.name()]
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
        if self._core.authUser(event):
            rom = self.active_rom
            if len(event.args) > 0:
                newpath = os.path.join(rom_path, " ".join(event.args))
                rom = newpath
                if os.path.exists(newpath):
                    try:
                        self.emustart(self.active_emu, rom)
                        event.channel.msg("Emulator loaded with ROM '%s'" %
                        " ".join(event.args))
                    except WindowsError:
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
        if self._core.authUser(event):
            try:
                self.emustart(self.active_emu, self.active_rom)
                event.channel.msg("Emulator restarted")
            except WindowsError:
                event.channel.msg("Could not restart emulator")

    @bones.event.handler(trigger="emustop")
    def emustop(self, event):
        global input_enabled
        if self._core.authUser(event):
            if self.isrunning(self.em):
                self.killemu(self.em)
                event.channel.msg("Emulator killed")
            else:
                event.channel.msg("Emulator not running")
                input_enabled = False

    @bones.event.handler(trigger="emudebug")
    def emudebug(self, event):
        if self._core.authUser(event):
            if self.isrunning(self.em):
                event.channel.msg("Emulator running as PID " + self.em_pid[0])
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
        if self._core.authUser(event):
            success = False
            if len(event.args) > 0:

                default_options = {
                    "emu":[os.path.join(emu_path, default_emu), default_emu],
                    "rom":os.path.join(rom_path, default_rom),
                }

                if event.args[0].lower() == "emu":
                    if event.args[1].lower() == "reset":
                        emucontrol.active_emu = default_options["emu"]
                    else:
                        newemu = " ".join(event.args[1:])
                        newpath = os.path.join(emu_path, newemu)
                        if os.path.exists(newpath):
                            emucontrol.active_emu = [newpath, newemu]
                            success = True
                        else:
                            event.channel.msg("Emulator does not exist, changes ignored")

                elif event.args[0].lower() == "rom":
                    if event.args[1].lower() == "reset":
                        emucontrol.active_rom = default_options["rom"]
                    else:
                        newpath = os.path.join(rom_path, " ".join(event.args[1:]))
                        if os.path.exists(newpath):
                            emucontrol.active_rom = newpath
                            success = True
                        else:
                            event.channel.msg("ROM does not exist, changes ignored")

                elif event.args[0].lower() == "input":
                    success = True
                    if event.args[1].lower() in ["true", "on"]:
                        input_enabled = True
                    elif event.args[1].lower() in ["false", "off"]:
                        input_enabled = False
                    else:
                        event.channel.msg("Must be \"On\" or \"Off\"")
                        success = False

                else:
                	event.channel.msg("Warning: Unknown Option.")

            if success == True:
                event.channel.msg("Changes applied successfully")

    @bones.event.handler(trigger="toggleinput")
    def toggleinput(self, event):
        global input_enabled, input_override
        if self._core.authUser(event):
            if input_enabled == False or input_override == False:
                input_enabled = True
                input_override = None
                event.channel.msg("Input enabled")
            elif input_enabled == True or input_enabled == None:
                input_enabled = False
                input_override = False
                event.channel.msg("Input disabled")
