#!/bin/bash

# Install Chrome
apt-get update && apt-get install -y wget unzip
wget -q -O /tmp/google-chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
dpkg -i /tmp/google-chrome.deb || apt-get -f install -y

# Install ChromeDriver
CHROME_DRIVER_VERSION=$(wget -qO- https://chromedriver.storage.googleapis.com/LATEST_RELEASE)
wget -q -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/$CHROME_DRIVER_VERSION/chromedriver_linux64.zip"
unzip /tmp/chromedriver.zip -d /usr/local/bin/
