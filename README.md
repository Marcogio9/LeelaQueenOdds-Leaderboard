# LeelaQueenOdds Leaderboard

This repository contains two Python scripts designed to manage and update the leaderboard for LeelaQueenOdds games.

## Files

1. **`leaderboard.py`** - Processes a PGN file to generate an offline JSON leaderboard for LeelaQueenOdds. The script reads each game from the provided PGN file, extracts relevant data, and compiles it into a ranking format for offline analysis.

2. **`leaderboard_online.py`** - Updates the online version of the LeelaQueenOdds leaderboard every minute. This script is intended to sync the local leaderboard with the online platform.


## Viewing the Leaderboard on a Web Page
To view the leaderboard locally in your browser, start a simple HTTP server in the folder containing the leaderboard files:

`python -m http.server`

Then, open the following URL in your browser:

`http://localhost:8000/`
