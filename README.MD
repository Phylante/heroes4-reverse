# Heroes4-reverse

Tools to extract and convert resource files from your heroes4 game.

# Usage :
- Set the absolute or relative path to the game in settings.py
- Create a venv with `python3 -m venv myvenv` then activate it with `source ./myvenv/bin/activate` (or accordingly if under macOs/Windows).
- Install the requirements with `pip install -r requirements.txt`
- Run `python main.py --help` for help
- Run `python main.py extractall` to get a full extract and conversion of audio files.
- `cd` to `h4r_files/Music` :
```bash
  (myvenv) phylante@Neptuna-666:/h4r_files/Music$ ls -s
 112 sound.combat.lose.mp3      3336 sound.combat.music.4.mp3     88 sound.combat.win.mp3   2256 sound.terrain.Dirt.mp3    2188 sound.terrain.Snow.mp3           2160 sound.terrain.Water.mp3   2988 sound.town.might.mp3
4604 sound.combat.music.1.mp3   3992 sound.combat.music.5.mp3   1964 sound.credits.mp3     13932 sound.terrain.grass.mp3   2316 sound.terrain.Subterranean.mp3   2464 sound.town.chaos.mp3      3088 sound.town.nature.mp3
3764 sound.combat.music.2.mp3   3928 sound.combat.music.6.mp3   3060 sound.end_turn.mp3     2412 sound.terrain.Rough.mp3   2152 sound.terrain.Swamp.mp3          3188 sound.town.death.mp3      2112 sound.town.order.mp3

  ```
- Enjoy listening to the music (for example ;) ).

# Note:
Sound conversion is done through ffmpeg. You may need to install it.