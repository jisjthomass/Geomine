#!/bin/bash
sudo systemctl start postgresql
sudo -u postgres psql -c "CREATE DATABASE nwis_wells_db;"
sudo -u postgres psql -d nwis_wells_db -f historical_drilling_events.sql
