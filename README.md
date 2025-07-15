# Randoglobin
Randoglobin is a randomizer for Mario and Luigi: Bowser's Inside Story.

![Screenshot of Randoglobin](docs/screenshot.png)

This program is still in development, and will likely see far more features in the future.

Dataglobin icon created by MiiK: https://bsky.app/profile/miikheaven.bsky.social

# Running the Program
There are 4 ways to run this program, from easiest to most complicated:

1. Download the binary from [Releases](https://github.com/MnL-Modding/Randoglobin/releases) and run it. (Use the `.exe` for Windows, and the `.bin` for Linux)

2. Install the package with
```bash
python3 -m pip install --force-reinstall git+https://github.com/MnL-Modding/Dataglobin
```
and run it with `dataglobin` or `python3 -m dataglobin`.

3. Clone the repository, install the dependencies with Poetry (assuming you already have Poetry installed with `python3 -m pip install poetry`):
```bash
poetry install
```
and run the program through Poetry:
```bash
poetry run dataglobin
```

4. Clone the repository, install the dependencies through `pip` with:
```bash
python3 -m pip install -r requirements.txt
```
and run it from the current directory with `python3 -m dataglobin`. Alternatively, it can be run through the `run.bat` if you use Windows.
