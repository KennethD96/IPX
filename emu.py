#encoding: utf-8
import bones.bot, bones.event, logging
from subprocess import Popen, PIPE
from twisted.internet import reactor
import os.path, time, re
import core

log = logging.getLogger(__name__)

try:
    import psutil
    psutil_available = True
    log.debug("Found psutil. Will use to manage emulator.")
except ImportError:
    psutil_available = False


class EmuControl(bones.bot.Module):
    _core = None

    def __init__(self, **args):
        bones.bot.Module.__init__(self, **args)

        if not self._core:
            for module in self.factory.modules:
                if isinstance(module, core.IPXCore):
                    self.__class__._core = module
        if not self._core:
            raise ValueError("IPX.core.IPXCore needs to be loaded before any other IPX module")

        self._core._["default_emu"] = self._core.config("emulators", "default")
        self._core._["default_rom"] = self._core.config("roms", "default")
        self._core._["load_at_startup"] = bool(self._core.config("emulators", "load_at_startup"))
        self._core._["input_override"] = bool(self._core.config("emulators", "input_override", default=True))
        self._core._["emu_path"] = self._core.config("emulators", "path")
        self._core._["rom_path"] = self._core.config("roms", "path")

        self._core._["active_rom"] = os.path.join(self._core._["rom_path"], self._core._["default_rom"])
        self._core._["active_emu"] = [os.path.join(self._core._["emu_path"], self._core._["default_emu"]), self._core._["default_emu"]]

        self.pid_file = os.path.join(self._core._["emu_path"], "running.pid")
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

        if self._core._["load_at_startup"] and not self.isrunning(self.em):
            try:
                self.emustart(self._core._["active_emu"], self._core._["active_rom"])
            except WindowsError:
                log.warning("Could not find emulator executable!")
        if self._core._["load_at_startup"] and self.isrunning(self.em):
            self._core._["input_enabled"] = True

    def emustart(self, emu, rom):
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
        self._core._["input_enabled"] = True

    def killemu(self, proc):
        proc.terminate()
        self._core._["input_enabled"] = False

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
            rom = self._core._["active_rom"]
            if len(event.args) > 0:
                newpath = os.path.join(self._core._["rom_path"], " ".join(event.args))
                rom = newpath
                if os.path.exists(newpath):
                    try:
                        self.emustart(self._core._["active_emu"], rom)
                        event.channel.msg("Emulator loaded with ROM '%s'" %
                        " ".join(event.args))
                    except WindowsError:
                        event.channel.msg("Could not load emulator")
                else:
                    event.channel.msg("ROM does not exist")
            else:
                if not self.isrunning(self.em):
                    try:
                        self.emustart(self._core._["active_emu"], rom)
                        event.channel.msg("Emulator initiated")
                    except:
                        event.channel.msg("Could not load emulator")
                else:
                    event.channel.msg("Emulator already running")

    @bones.event.handler(trigger="emurestart")
    def emurestart(self, event):
        if self._core.authUser(event):
            try:
                self.emustart(self._core._["active_emu"], self._core._["active_rom"])
                event.channel.msg("Emulator restarted")
            except WindowsError:
                event.channel.msg("Could not restart emulator")

    @bones.event.handler(trigger="emustop")
    def emustop(self, event):
        if self._core.authUser(event):
            if self.isrunning(self.em):
                self.killemu(self.em)
                event.channel.msg("Emulator killed")
            else:
                event.channel.msg("Emulator not running")
                self._core._["input_enabled"] = False

    @bones.event.handler(trigger="emudebug")
    def emudebug(self, event):
        if self._core.authUser(event):
            if self.isrunning(self.em):
                event.channel.msg("Emulator running as PID " + self.em_pid[0])
            else:
                event.channel.msg("Emulator not running")

    def inputDriverEnabled(self):
        return (self._core._["input_override"] == None or self._core._["input_override"] == True) and self._core._["input_enabled"]


class EmuSet(bones.bot.Module):
    _core = None
    def __init__(self, **args):
        bones.bot.Module.__init__(self, **args)
        self.log = logging.getLogger(__name__+"."+self.__class__.__name__)

        if not self._core:
            for module in self.factory.modules:
                if isinstance(module, core.IPXCore):
                    self.__class__._core = module
        if not self._core:
            raise ValueError("IPX.core.IPXCore needs to be loaded before any other IPX module")

    @bones.event.handler(trigger="emuset")
    def emuset(self, event):
        if self._core.authUser(event):
            success = False
            if len(event.args) > 0:

                default_options = {
                    "emu":[os.path.join(self._core._["emu_path"], self._core._["default_emu"]), self._core._["default_emu"]],
                    "rom":os.path.join(self._core._["rom_path"], self._core._["default_rom"]),
                }

                if event.args[0].lower() == "emu":
                    if event.args[1].lower() == "reset":
                        self._core._["active_emu"] = default_options["emu"]
                    else:
                        newemu = " ".join(event.args[1:])
                        newpath = os.path.join(self._core._["emu_path"], newemu)
                        if os.path.exists(newpath):
                            self._core._["active_emu"] = [newpath, newemu]
                            success = True
                        else:
                            event.channel.msg("Emulator does not exist, changes ignored")

                elif event.args[0].lower() == "rom":
                    if event.args[1].lower() == "reset":
                        self._core._["active_rom"] = default_options["rom"]
                    else:
                        newpath = os.path.join(self._core._["rom_path"], " ".join(event.args[1:]))
                        if os.path.exists(newpath):
                            self._core._["active_rom"] = newpath
                            success = True
                        else:
                            event.channel.msg("ROM does not exist, changes ignored")

                elif event.args[0].lower() == "input":
                    success = True
                    if event.args[1].lower() in ["true", "on"]:
                        self._core._["input_enabled"] = True
                    elif event.args[1].lower() in ["false", "off"]:
                        self._core._["input_enabled"] = False
                    else:
                        event.channel.msg("Must be \"On\" or \"Off\"")
                        success = False

                else:
                	event.channel.msg("Warning: Unknown Option.")

            if success == True:
                event.channel.msg("Changes applied successfully")

    @bones.event.handler(trigger="toggleinput")
    def toggleinput(self, event):
        if self._core.authUser(event):
            if self._core._["input_enabled"] == False or self._core._["input_override"] == False:
                self._core._["input_enabled"] = True
                self._core._["input_override"] = None
                event.channel.msg("Input enabled")
            elif self._core._["input_enabled"] == True or self._core._["input_enabled"] == None:
                self._core._["input_enabled"] = False
                self._core._["input_override"] = False
                event.channel.msg("Input disabled")
