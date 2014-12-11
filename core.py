import os
from ConfigParser import SafeConfigParser

import bones.bot
import bones.event


class IPXCore(bones.bot.Module):
    # Sometiems Python can be a big fucking pain in the ass. Workaround for
    # not being able to change class attributes when working on an instance.
    _ = {
        "config": None,
    }

    def __init__(self, **args):
        bones.bot.Module.__init__(self, **args)

        if not self._["config"]:
            self._["config"] = SafeConfigParser(
                defaults={  # Interpolation
                    "here": os.getcwd(),
                },
                allow_no_value=True,
            )
            self._["config_path"] = self.settings.get(
                section="IPX",
                option="config",
                default=os.path.join(os.getcwd(), "IPX.ini"),
            )
            self._["config"].read(self._["config_path"])

        self._["admins"] = self.config("auth", "admins", default="").split("\n")
        self._["admins"] = bones.bot.removeEmptyElementsFromList(self._["admins"])

        self._["allow_all_ops"] = bool(self.config("auth", "allow_all_ops", default=True))
        self._["op_mode"] = self.config("auth", "op_mode", default="o")
        self._["require_op"] = bool(self.config("auth", "require_op", default=False))

    def config(self, section, option, default=None):
        if not self._["config"].has_section(section):
            return default

        if not self._["config"].has_option(section, option):
            return default

        data = self._["config"].get(section, option)
        return data if data else default

    def authUser(self, event):
        if self._["allow_all_ops"] or len(self._["admins"]) == 0:
            if event.user.nickname in event.channel.modes[self._["op_mode"]]:
                return True
        if event.user.nickname in self._admins:
            if self._["require_op"]:
                if event.user.nickname in event.channel.modes[self._["op_mode"]]:
                    return True
                else:
                    self.log.warning("User is not OP in this channel.")
                    return False
            else:
                return True
        else:
            return False

