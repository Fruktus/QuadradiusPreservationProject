# Quadradius Preservation Project
[![version](https://img.shields.io/badge/version-beta%201.0-green)](https://github.com/Fruktus/QuadradiusPreservationProject/releases)
[![platform](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/downloads/)
[![python-ci](https://github.com/Fruktus/QuadradiusPreservationProject/actions/workflows/python.yml/badge.svg)](https://github.com/Fruktus/QuadradiusPreservationProject/actions/workflows/python.yml)
[![GitHub all releases](https://img.shields.io/github/downloads/Fruktus/QuadradiusPreservationProject/total)](https://github.com/Fruktus/QuadradiusPreservationProject/releases)
[![Subreddit subscribers](https://img.shields.io/reddit/subreddit-subscribers/quadradius?style=social)](https://www.reddit.com/r/quadradius/)

The goal of this project is to keep this fantastic game alive by recreating core functionality of the server, which at this moment is limited (original available at [Quadradius](http://classic.quadradius.com)).
The project is completely non-profit and should be considered as educational.
All of the rights belong to the original authors, Jimmi Heiserman and Brad Kayal.
The provided software does not represent the quality of the original,
and the original authors should in no way be held accountable for any liabilities.

## Progress

The current version contains most of the features and should be playable. Some bugs may occasionally happen.
Detailed progress is available [here](https://github.com/Fruktus/QuadradiusPreservationProject/projects/1).

## Requirements

The client requires
[Flash Player](https://www.adobe.com/support/flashplayer/debug_downloads.html)
to work.
The server runs on Python 3.8 or higher.

## Installation and running

Clone or download the repository from GitHub and run
```bash
python -m QRServer
```

You can configure the server by passing the following CLI parameters:
* `-b`/`--bind` — bind address (default `127.0.0.1`),
* `-p`/`--lobby-port` — lobby port (default `3000`),
* `-q`/`--game-port` — game port (default `3001`).

You can also run `python -m QRServer -h` to display help.
You can play as a member by typing in username and any password (it is not checked at the moment).

## Docker and Compose

This repository also contains a `Dockerfile` which creates an image with
an HTTP server (serving the client SWF files), and the QR server itself.

There is a Compose configuration which makes setting up the server easy,
just run:

```bash
docker compose up
```

However, when you want to run the Docker image without Compose:

1. Build the image
   ```bash
   docker build . -t quadradius-server
   ```

2. Run the image
   ```bash
   docker run -it \
     -p 3000:3000 \
     -p 3001:3001 \
     -p 8000:8000 \
     quadradius-server
   ```

You can define the following environment variables to configure the server:
* `ADDRESS` — the address which the server will be hosted at,
  by default it's `127.0.0.1`
* `LOBBY_PORT` and `GAME_PORT` — the ports of the application,
  they are used by the client to connect to the server

When the image is running, you can start the game by executing
```bash
./flashplayer http://<address>:<http port>/quadradius_lobby.swf
```
by default, it will be
```bash
./flashplayer http://127.0.0.1:8000/quadradius_lobby.swf
```

### Persisting data

Data is stored in directory `/data` in the container.
In order to persist the data between containers, just bind this directory
or create a volume.
