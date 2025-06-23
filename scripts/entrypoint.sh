#!/bin/sh
python -m bot.database --init && exec python -m bot.main
