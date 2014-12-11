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
    active_rom = None
    active_emu = None

    _load_at_startup = None
    _input_override = None
    _input_enabled = None
    _default_emu = None
    _default_rom = None

    _emu_path = None
    _rom_path = None

    _core = None

    def __init__(self, **args):
        bones.bot.Module.__init__(self, **args)

        if not self._core:
            for module in self.factory.modules:
                if isinstance(module, core.IPXCore):
                    self.__class__._core = module
        if not self._core:
            raise ValueError("IPX.core.IPXCore needs to be loaded before any other IPX module")

        cls = self.__class__
        cls._default_emu = self._core.config("emulators", "default")
        cls._default_rom = self._core.config("roms", "default")
        cls._load_at_startup = bool(self._core.config("emulators", "load_at_startup"))
        cls._input_override = bool(self._core.config("emulators", "input_override", default=True))
        cls._emu_path = self._core.config("emulators", "path")
        cls._rom_path = self._core.config("roms", "path")

        cls.active_rom = os.path.join(self._rom_path, self._default_rom)
        cls.active_emu = [os.path.join(self._emu_path, self._default_emu), self._default_emu]

        self.pid_file = os.path.join(self._emu_path, "running.pid")
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

        if self._load_at_startup and not self.isrunning(self.em):
            try:
                self.emustart(self.active_emu, self.active_rom)
            except WindowsError:
                log.warning("Could not find emulator executable!")
        if self._load_at_startup and self.isrunning(self.em):
            cls._input_enabled = True

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
        self.__class__._input_enabled = True

    def killemu(self, proc):
        proc.terminate()
        self.__class__._input_enabled = False

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
                newpath = os.path.join(self._rom_path, " ".join(event.args))
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
        if self._core.authUser(event):
            if self.isrunning(self.em):
                self.killemu(self.em)
                event.channel.msg("Emulator killed")
            else:
                event.channel.msg("Emulator not running")
                self.__class__._input_enabled = False

    @bones.event.handler(trigger="emudebug")
    def emudebug(self, event):
        if self._core.authUser(event):
            if self.isrunning(self.em):
                event.channel.msg("Emulator running as PID " + self.em_pid[0])
            else:
                event.channel.msg("Emulator not running")

    def inputDriverEnabled(self):
        return (self._input_override == None or self._input_override == True) and self._input_enabled


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
                    "emu":[os.path.join(EmuControl._emu_path, EmuControl._default_emu), EmuControl._default_emu],
                    "rom":os.path.join(EmuControl._rom_path, EmuControl._default_rom),
                }

                if event.args[0].lower() == "emu":
                    if event.args[1].lower() == "reset":
                        EmuControl.active_emu = default_options["emu"]
                    else:
                        newemu = " ".join(event.args[1:])
                        newpath = os.path.join(EmuControl._emu_path, newemu)
                        if os.path.exists(newpath):
                            EmuControl.active_emu = [newpath, newemu]
                            success = True
                        else:
                            event.channel.msg("Emulator does not exist, changes ignored")

                elif event.args[0].lower() == "rom":
                    if event.args[1].lower() == "reset":
                        EmuControl.active_rom = default_options["rom"]
                    else:
                        newpath = os.path.join(EmuControl._rom_path, " ".join(event.args[1:]))
                        if os.path.exists(newpath):
                            EmuControl.active_rom = newpath
                            success = True
                        else:
                            event.channel.msg("ROM does not exist, changes ignored")

                elif event.args[0].lower() == "input":
                    success = True
                    if event.args[1].lower() in ["true", "on"]:
                        EmuControl._input_enabled = True
                    elif event.args[1].lower() in ["false", "off"]:
                        EmuControl._input_enabled = False
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
            if EmuControl._input_enabled == False or EmuControl._input_override == False:
                EmuControl._input_enabled = True
                EmuControl._input_override = None
                event.channel.msg("Input enabled")
            elif EmuControl._input_enabled == True or EmuControl._input_enabled == None:
                EmuControl._input_enabled = False
                EmuControl._input_override = False
                event.channel.msg("Input disabled")
