# zepp-extractor

Program to automatically extract workout data from Zepp bypassing the mobile application.

## Overview

`zepp-extractor` is designed to automatically retrieve workout data from Zepp without using the mobile application. This project allows you to extract your exercise statistics by leveraging your authentication token from Huami's GDPR page.

## Setup

Before running the project, you need to obtain your **Authentication Token**. Although there are several methods to capture this token (e.g., by monitoring the requests sent from the Zepp app), the simplest method is to retrieve it from the Huami GDPR page.

### Steps

1. Go to the [GDPR page](https://user.huami.com/privacy2/index.html?loginPlatform=web&platform_app=com.xiaomi.hm.health#/)
2. Click on *Export Data*
3. Log in
4. Open the *Developers Tools* (F12)
5. Select the *Network* tab
6. Click on *Export Data* again
7. Search through the network calls to find the *Apptoken* (often hidden inside the cookie data)
8. Copy the *Apptoken* and store it securely. This token acts as your API key.

## Credits

This project is inspired by [Mi-Fit-and-Zepp-workout-exporter](https://github.com/rolandsz/Mi-Fit-and-Zepp-workout-exporter) by rolandsz.
