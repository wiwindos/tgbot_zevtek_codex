#!/bin/sh
python scripts/migrate.py
python -m bot.database --init && exec python -m bot.main
