# Quadradius Preservation Project
[![version](https://img.shields.io/badge/version-beta%201.0-green)](https://github.com/Fruktus/QuadradiusPreservationProject/releases)
[![platform](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/downloads/)
[![python-ci](https://github.com/Fruktus/QuadradiusPreservationProject/actions/workflows/python.yml/badge.svg)](https://github.com/Fruktus/QuadradiusPreservationProject/actions/workflows/python.yml)
[![GitHub all releases](https://img.shields.io/github/downloads/Fruktus/QuadradiusPreservationProject/total)](https://github.com/Fruktus/QuadradiusPreservationProject/releases)
[![Subreddit subscribers](https://img.shields.io/reddit/subreddit-subscribers/quadradius?style=social)](https://www.reddit.com/r/quadradius/)

The goal of this project is to keep this game alive.
The software contained in this repository is a reimplementation of the original server, which was written in Java.
Some functionalities may be missing, if so, please report them using the [Issues](https://github.com/Fruktus/QuadradiusPreservationProject/issues) page.

The website [Quadradius](http://classic.quadradius.com) is no longer available and the only way to obtain the client files is through archives or in our [Quadradius Classic Backup](https://github.com/Fruktus/QuadradiusClassic) repo.
The project is non-profit.
All of the rights belong to the original authors, Jimmi Heiserman and Brad Kayal with whom we are not affiliated.
The provided software does not represent the quality of the original,
and the original authors should in no way be held accountable for any liabilities.


## Requirements

The client requires Flash Projector to work, which is currently only available from third party websites.
The [Ruffle](https://ruffle.rs/) Desktop app mostly works correctly and is preffered way of running the software.
The server is compatible with Python 3.8 or higher.


## Installation and running
The installation can be done in three ways:
1. Via Launcher (which is provided in the [Releases](https://github.com/Fruktus/QuadradiusPreservationProject/releases) page, this is the most user-friendly way
2. Manually from source (by installing Python and dependencies, downloading Ruffle and configuring everything)
3. Via Docker

### Launcher installation
Download the platform-specific zip of launcher from [Releases](https://github.com/Fruktus/QuadradiusPreservationProject/releases) and run the ```quadradius-launcher.exe``` within.
The window that opens has manual on how to use it.
When setting up a server, a port forwarding may be required, but due to the complexity of the topic it will not be covered here.

Alternatively, you can set the launcher up manually by following the steps from [Manual](https://github.com/Fruktus/QuadradiusPreservationProject/tree/master/launcher)


### Manual installation
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


### Docker and Compose

This repository also contains a `Dockerfile` which creates an image with an HTTP server (serving the client SWF files), and the QR server itself.
There is a Compose configuration which makes setting up the server easy, just run:

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

#### Persisting data

Data is stored in directory `/data` in the container.
In order to persist the data between containers, just bind this directory
or create a volume.
