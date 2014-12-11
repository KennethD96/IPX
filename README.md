IPX (IRC Plays X)
===

A set of modules for the [Bones IRC Bot][bones] allowing input to be sent from an IRC channel to a game emulator and (optionally) streamed.
Inspired by "twitchplayspokemon" on [twitch.tv][twitch/twitchplayspokemon].

## Requirements
- [Bones IRC Bot][bones] from the `feature/docs-and-cleanup` branch
- For `input.GenericBGBInput`: Windows
- An emulator; We recommend [BGB][bgb]

### Optional
- [psutil][psutil] for resumed emulator-control between sessions

### Installation
- Copy everything from this repository to a folder named `ipx` in your [Bones IRC Bot][bones] directory.
- Add the following lines to the `modules` section of your [Bones IRC Bot][bones] configuration:
```
ipx.input.GenericBGBInput
ipx.emu.emucontrol
ipx.emu.emuset
```
- Place the emulator excecutable in your `{Bones}\ipx\emulators` directory.
- Place your ROM's in the `{Bones}\ipx\roms` directory.
- Edit the config section of `{Bones}\ipx\emu.py` to your preference.

[bones]: https://github.com/404d/Bones-IRCBot
[bgb]: http://bgb.bircd.org/
[psutil]:https://github.com/giampaolo/psutil
[twitch/twitchplayspokemon]:http://www.twitch.tv/twitchplayspokemon
