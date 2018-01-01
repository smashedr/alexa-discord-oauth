# Alexa Discord

[![build status](https://git.cssnr.com/shane/alexa-discord-oauth/badges/master/build.svg)](https://git.cssnr.com/shane/alexa-discord-oauth/commits/master) [![coverage report](https://git.cssnr.com/shane/alexa-discord-oauth/badges/master/coverage.svg)](https://git.cssnr.com/shane/alexa-discord-oauth/commits/master)

Oauth endpoint for alexa-discord.

## Overview

Amazon Alexa built-in account linking does not work with all oauth endpoints.


This endpoint negotiates the oauth with Discord, then returns the `access_token` 
to Amazon to store with the account for use with the Skill.

### Documentation

- Alexa: https://developer.amazon.com/docs/custom-skills/link-an-alexa-user-with-a-user-in-your-system.html
- Discord:  https://discordapp.com/developers/docs/topics/oauth2
