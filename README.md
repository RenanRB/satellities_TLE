# Satellite TLE Data Generator

The Satellite TLE Data Generator is a Python script that retrieves satellite information from Celestrak website and generates JSON files for easy usage. By simply calling the `data/gps_tles.json` file provided in this project, users will have access to all available GPS TLEs (Two-Line Elements) at the given moment. This project automatically updates the satellite data on a daily basis.

## Features

- Retrieves satellite information from Celestrak website.
- Generates JSON files containing TLE data for GPS satellites.
- Daily automatic updates to ensure data accuracy.

## Use case

I currently use this project to feed the data used in my application: https://droneweather.xyz/, I use the library: https://github.com/jhermsmeier/node-tle to read the data and build the necessary information for presentation.
