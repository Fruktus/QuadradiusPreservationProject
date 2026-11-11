from QRServer.achievements.challenge import Challenge

# This is the place to configure all active challenges, both permanent and temporary

# Event (timed) challenges go here. Meant to be removed after the completion
_EVENT_CHALLENGES: list[type[Challenge]] = [
]

# Challenges (achievements) which can be done at any time
_PERPETUAL_CHALLENGES: list[type[Challenge]] = [
]

# Re-exported sum of challenges
CHALLENGES = _EVENT_CHALLENGES + _PERPETUAL_CHALLENGES
