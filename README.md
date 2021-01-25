# Quadradius Preservation Project
The goal of this project is to keep this fantastic game alive by recreating core functionality of the server, which at this moment is limited (original available at [Quadradius](http://classic.quadradius.com)).
The project is completely non-profit and should be considered as educational.
All of the rights belong to the original authors, Jimmi Heiserman and Brad Kayal.
The provided software does not represent the quality of the original and the original authors should in no way be held accountable for any liabilites.

## Progress
Current version can be considered early alpha. It is playable, although buggy and prone to crashes.
Detailed progress is available [here](https://github.com/Fruktus/QuadradiusPreservationProject/projects/1).

## Installation and Running
Project should work with Python3.7 or higher.
Configuration is still WIP, if you need to change anything, modify ```confiquration.py``` file for now.

Clone or download the repository from GitHub and run
```python3 -m QRServer```
By default it uses ports ```3000``` and ```3001``` (like in original) and listens on local IP. To make it available to others, change the host in configuration to desired IP, such as ```0.0.0.0```.
