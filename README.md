# Reverse Engineering Scorcher
An attempt to reverse engineer all assets from the game [Scorcher](https://www.mobygames.com/game/2935/scorcher/) released in 1996 for *DOS*, *Windows* and *Sega Saturn*. This repository doesn't contain any of the released material for the game. Only the scripts needed to extracts some of the assets.

## Extracting assets
The Python script `rr_scorcher.py` will extract all resources and convert `.r0v` files to images.

To run the Python script, you need some dependencies. These are specified in the file `requirements.txt`. Install dependencies with the following `PIP` command:

```bash
pip install -r requirements.txt
```

You need a copy of *Scorcher*, specifically the file `TAGDEN.BIN` which contains most, if not all assets for the game.

> [!tip]
> Scorcher is considered [Abandonware](https://en.wikipedia.org/wiki/Abandonware) and you can download a copy of the game from [My Abandonware](https://www.myabandonware.com/game/scorcher-7r5). The DOS "RIP Version" will do fine 👍

When you have extracted the game and located the file `TAGDEN.BIN`, run the following command. Use your local path to the file:

```bash
python rr_scorcher.py /path/to/TAGDEN.BIN
```

The script will run for a for a few seconds, then you should have some of the content in a output directory called `output/`.

## Formats
All formats seams to be build as in house formats.

| Ext. | Count | Description | Status |
|---:|---:|:---|:---|
| `.bin` | `1` | Assets content archive | 🟢 Decodes to files |
| `.bin` | `184` | ??? | 🔴 Not decoded |
| `.r0v` | `91` | Image 15-bit | 🟢 Decodes to `.png` |
| `.wl3` | `64` | 3D model |  🔴 Not decoded |
| `.0` | `51` | ??? | 🔴 Not decoded |
| `.ld` | `31` | ??? | 🔴 Not decoded |
| `.fzp` | `25` | ??? | 🔴 Not decoded |
| `.fmz` | `25` | ??? | 🔴 Not decoded |
| `.txt` | `15` | ??? | 🔴 Not decoded |
| `.1` | `20` | ??? | 🔴 Not decoded |
| `.pal` | `10` | Color palette | 🔴 Not decoded |
| `.cmp` | `10` | ??? | 🔴 Not decoded |
| `.joy` | `7` | ??? | 🔴 Not decoded |
| `.hmp` | `6` | Level heightmap | 🔴 Not decoded |
| `.ddd` | `1` | ??? | 🔴 Not decoded |
| `.asc` | `1` | ??? | 🔴 Not decoded |

By default all data types are stored with big endian.

All decoding has been done with the help of tools like [Radare2](https://www.radare.org/n/), [Jupyter Lab](https://jupyter.org/) and [Visidata](https://www.visidata.org/).
