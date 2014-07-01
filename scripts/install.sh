#! /bin/bash

BASE_PATH='/usr/local/'

# Installing requirements.
apt-get update
apt-get install -y python2.7 python-dev python-virtualenv build-essential 

# Cloning the repo.
cd $BASE_PATH
git clone https://github.com/indradhanush/LeapBot.git


# Setting up virtualenv
virtualenv $BASE_PATH/logbot
source $BASE_PATH/logbot/bin/activate
pip install -r $BASE_PATH/LeapBot/requirements.txt


# Install crons
crontab -l > cron_back
echo | cat /usr/local/LeapBot/scripts/cron_jobs >> cron_back
crontab cron_back

echo "Starting bot..."
/usr/local/logbot/bin/python /usr/local/LeapBot/runner.py &
