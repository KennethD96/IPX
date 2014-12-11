import os
from ConfigParser import SafeConfigParser

import bones.bot
import bones.event


class IPXCore(bones.bot.Module):
    _config = None
    _admins = []
    _allow_all_ops = True
    _op_mode = "o"

    def __init__(self, **args):
        bones.bot.Module.__init__(self, **args)

        if not self._config:
            self._config = SafeConfigParser(
                defaults={  # Interpolation
                    "here": os.getcwd(),
                },
                allow_no_value=True,
            )
            self._config_path = self.settings.get(
                section="IPX",
                option="config",
                default=os.path.join(os.getcwd(), "IPX.ini"),
            )
            self._config.read(self._config_path)

        self._admins = self.config("auth", "admins", default="").split("\n")
        self._admins = bones.bot.removeEmptyElementsFromList(self._admins)

        self._allow_all_ops = bool(self.config("auth", "allow_all_ops", default=True))
        self._op_mode = self.config("auth", "op_mode", default="o")
        self._require_op = bool(self.config("auth", "require_op", default=False))

    def config(self, section, option, default=None):
        if not self._config.has_section(section):
            return default

        if not self._config.has_option(section, option):
            return default

        data = self._config.get(section, option)
        return data if data else default

    def authUser(self, event):
        if self._allow_all_ops or len(self._admins) == 0:
            if event.user.nickname in event.channel.modes[self._op_mode]:
                return True
        if event.user.nickname in self._admins:
            if self._require_op:
                if event.user.nickname in event.channel.modes[self._op_mode]:
                    return True
                else:
                    self.log.warning("User is not OP in this channel.")
                    return False
            else:
                return True
        else:
            return False
