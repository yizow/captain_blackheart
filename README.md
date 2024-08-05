# About

Captain Blackheart is a Discord Bot I wrote to run logistics for my tabletop role-playing sessions. We play in person on Tuesdays: out of a total of 6 Player Characters, 3 was the quorum. Every Thursday, I would send out a poll to get availability for the next few weeks and see when our next session would be.

Invariably, I would forget to send it out on Thursday... And sometimes when enough folks were travelling / sick / busy and we couldn't meet for weeks at a time, I'd get sad looking at the channel where it was just my polls with no responses except chirping crickets.

And so, inspired by an NPC in a previous [Blades in the Dark](https://evilhat.com/product/blades-in-the-dark/) campaign, Captain Blackheart was born! He is the captured ghost of an infamous pirate, and his punishment is to be bound into a "soul crystal" for eternal servitude to Duskvol Management (DM).

![3 messages: The poll itself, the response if no quorum, the result if we have quorum](https://github.com/yizow/captain_blackheart/blob/master/overview.jpg?raw=true)

> There are many like it, but this one is mine.

# Features

## Polling
Captain Blackheart will post a poll to a specified Discord channel once a week.
The message will include the dates of the next 3 sessions, a default "I can't come to any" option, and a corresponding emoji for each selection.
Then, Captain Blackheart will react to his own poll with each emoji to make it easier for players to click on them.

If there is currently a scheduled session, Captain Blackheart will skip polling.

## Quorum
Once a week, Captain Blackheart will check to see if there is quorum on a proposed session date. Captain Blackheart will always choose to schedule a session on the soonest date with quorum.

If there is currently a scheduled session, Captain Blackheart will instead send a reminder message. If the scheduled session is happening this week, Captain Blackheart will include an `@mention`.

## Commands
Captain Blackheart supports some commands to manually trigger polls and quorum. By default, the command prefix is `!`

- `!poll`: Post a new poll. This won't do anything if there is currently a scheduled session.
- `!quorum`: Count for quorum. If there is currently a scheduled session, this will send out a reminder.
- `!reset`: Clear memory of existing polls / scheduled sessions.
- `!remember {message_id}`: Sets the given message_id as the last poll i.e. Captain Blackheart will count emoji reacts on this message.

# Installation

The script expects your [Discord bot token](https://discordgsm.com/guide/how-to-get-a-discord-bot-token) exists in the environment a `CAPTAIN_BLACKHEART_TOKEN`. 
On Linux, I set up the token in my `.bashrc` file: `echo CAPTAIN_BLACKHEART_TOKEN={token}`

Make sure to add this bot to your server from the [Discord applications page](https://discord.com/developers/applications/).

## 24/7 Bot
I run Captain Blackheart on the same Raspberry Pi I use to host [my website](https://github.com/yizow/WebPi/blob/master/www/notes.md).
I use `pm2` to keep the bot running.
This way I never have to remember to do anything.

## Manual
You can run Captain Blackheart and then manually run the `!poll` and `!quorum` commands. You'll need a computer able to run `python3` scripts.

1. Start the bot, run the `!poll`, and wait for your players to respond.
2. (Presumably) A few days later, start the bot again but this time give it the `--poll` flag with the [message id](https://support.discord.com/hc/en-us/articles/206346498-Where-can-I-find-my-User-Server-Message-ID) of the previous poll. Then, run the `!quorum` command.

```
python3 captain_blackheart.py --poll 123456789
```

# Configuration

`captain_blackheart.py` contains a number of configurable values at the top of the file: simply open and edit with your favorite text editor.

- `BLADES_ROLE_NAME`: The name of the role you use to notify players.
- `TEXT_IN_THE_DARK_NAME`: The name of the text channel Captain Blackheart will post to.
- `NUM_PLAYER_QUORUM`: How many players are needed for quorum.
- `SESSION_{DAY,HOUR,MINUTE}`: When your weekly sessions are scheduled for.
- `POLL_{DAY,HOUR,MINUTE}`: When your weekly poll is sent.
- `QUORUM_DAY`: When your weekly poll is conducted. It will happen at the same `HOUR` and `MINUTE` as your poll.
- `POLL_TEXT`: Python formatted string for the message used when creating a poll.
- `EVENT_TEXT`: Python formatted string for the message used when announcing a scheduled session.
- `NO_QUORUM_TEXT`: Python formatted string for the message used when no quorum has been reached for any proposed date.
- `COMMAND_PREFIX`: Command prefix.
- `TOKEN_NAME`: Name of the bot token in the environment.
- `{ONE,TWO,THREE,X}`: Unicode values for emoji reactions.
