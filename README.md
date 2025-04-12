# zepp-extractor

Program to automatically extract workout data from Zepp, bypassing the mobile application.

## Overview

`zepp-extractor` automatically retrieves your workout data from Zepp without the need for the mobile app. The tool leverages your authentication token obtained from Huami's GDPR page to access your exercise statistics. It processes your workout data (for example, swimming workouts) and exports it into a structured CSV file, making the data easy to review and further process (for example, with ChatGPT).

## How It Works

1. **API Retrieval:**  
   The script uses your authentication token to access two Mi Fit API endpoints:
   - **Workout History:** Retrieves a summary of your workouts.
   - **Workout Details:** Retrieves detailed data for each workout.
   
2. **Data Parsing:**  
   The script parses raw strings (for time, heart rate, pace) into Python lists. For example:
   - The **Heart Rate (HR)** string is divided into segments where the first value is absolute and subsequent values represent cumulative differences.
   - The **Pace** and **Time** strings are standardized to ensure consistency.

3. **Metric Computation:**  
   Various metrics are computed from the parsed data:
   - **Total Distance, Average Pace, and Movement Percentages:** Calculated based on the exercise data.
   - **Heart Rate Metrics:** Maximum, minimum, variance, and derived HR zones.
   - **Effort/Rest Durations:** Calculated using pace values.

4. **CSV Export:**  
   The processed data is exported to a CSV file with clear sections:
   - **Basic Workout Info:** A summary including total distance, laps, calories, exercise load, run time (calculated from elapsed time), workout start time, average heart rate, swolf, percentage moving, percentage idle, and additional details.
   - Additional sections include Global Metrics, HR Metrics, Effort/Rest Durations, and Time Series Data.

## Setup

### Obtaining the Authentication Token

Before running the project, you need to obtain your **Authentication Token**. Although there are several methods to capture this token (e.g., by monitoring network requests from the Zepp app), the simplest method is to retrieve it from the Huami GDPR page.

#### Steps

1. Go to the [Huami GDPR page](https://user.huami.com/privacy2/index.html?loginPlatform=web&platform_app=com.xiaomi.hm.health#/).
2. Click on **Export Data**.
3. Log in with your credentials.
4. Open your browser's Developer Tools (typically with F12).
5. Select the **Network** tab.
6. Click on **Export Data** again.
7. Look for the **Apptoken** in the network calls (it may be hidden in the cookie data).
8. Copy the **Apptoken** and store it securely (this token acts as your API key).

### Variables to Change

- **token:**  
  The script retrieves your API token from the environment variable `ZEPP_TOKEN`. Set this variable in your shell or via a configuration file before running the script.

- **hr_max_theoretical:**  
  This variable represents your theoretical maximum heart rate (e.g., `220 - age`). The default value is set to `196`. Change this value according to your preference.

- **output_dir:**  
  This is the directory where CSV files will be saved. By default, it is set to the `workouts` folder in the project directory. Modify this if you wish to save the output elsewhere.

## Citation

If you use `zepp-extractor` in your work, research, or any publicly distributed project, please consider giving credit. You can use the following template as a starting point for your citation:

> **Author:** Yann Roubeau  
> **Year:** 2025
> **Title:** *zepp-extractor: Program to automatically extract workout data from Zepp*
> **Source:** [https://github.com/Tilodry/zepp-extractor](https://github.com/Tilodry/zepp-extractor)
> **Access Date:** April 2025