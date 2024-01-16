import dal
from datetime import date, timedelta
from exceptions import BusinessLogicException, DalException
from logging_config import get_logger
import models

"""
This module contains several methods for getting satellite data from Celestrak.org, then passing that data into 
Satellite and Event class objects. 

Methods:
--------
    sat_tle_data_to_list() -> list:
        either reads satellite TLE data from satellites.db, or, if the date on the first line of satellites.db does
        not match today's date, loads new satellite data.
    get_sat_names_list():
        generates a list of all satellite names in the database, so they can be printed to the gui, or so a searched
        for satellite name can be validated. 
    get_data_for_one_sat(sat_name: str, forecast, latitude, longitude):
        takes a satellite name, list of forecast objects, latitude and longitude from the gui, and turns that into a
        list of satellite Event objects using the get_events method from the Satellite class. 
    get_lat_long(address: str):
        calls on the get_lat_long function in the dal to return a latitude and longitude from Open Street Maps for a 
        given address. 
    write_results_to_txt(results):
        calls the dal.write_results_to_txt method to write results from the gui to results_export.txt
    
Constants:
----------
    MOST_POPULAR_SATELLITES: a list of the names of 20 or so of the most popular satellites. 
"""

logger = get_logger(__name__)
MOST_POPULAR_SATELLITES = ["ISS (ZARYA)", "NORSAT 1", "NOAA 18", "AISSAT 2", "CENTAURI-1", "ITASAT",
                           "CENTAURI-3 (TYVAK-0210)", "AISSAT 1", "NORSAT 2", "NOAA 15", "METOP-B", "NOAA 19",
                           "KKS-1 (KISEKI)", "ZHUHAI-1 02 (CAS-4B)", "PROXIMA II", "PROXIMA I",
                           "NORSAT 3", "KHAYYAM", "CSS (TIANHE)"]


def sat_tle_data_to_list() -> list:
    """
    Either reads satellite TLE data from satellites.db, or, if the date on the first line of satellites.db does
        not match today's date, loads new satellite data.
    :return: a list of Satellite objects.
    """
    # get today's date
    todays_date = date.today()
    # check if the date on my data matches today's date
    file_date = dal.check_sat_tle_data_date()
    # I'm going to have to download the data once per day, so I will not get my IP banned again... :)
    if todays_date != file_date:  # need to download new data if the data is not from today.
        try:
            logger.info("Date on satellite.db did not match today's date, Getting new satellite data from Celestrak.org")
            # generate the new data
            dal.sat_tle_data_to_txt()
            # now I can use this method to read it from the txt.
            results = dal.read_tle_data_from_txt()
            satellite_list = []
            i = 1
            while i < (len(results) - 1):
                # each satellite is represented by 3 lines, the first is the name, and the next two are the "TLE" data
                name = results[i].strip()
                i += 1
                line_one = results[i].strip()
                i += 1
                line_two = results[i].strip()
                i += 1
                # create a new instance of the satellite class.
                new_sat = models.Satellite(name, line_one, line_two)
                # append that to the satellite list.
                satellite_list.append(new_sat)
            logger.info('Generated new satellite list.')
            return satellite_list
        except (DalException, Exception):  # want to catch any & all other exceptions here...
            logger.error('Unable to generate new satellite list!')
            raise BusinessLogicException
    else:
        try:
            # for the most part this is identical to the above if clause.
            results = dal.read_tle_data_from_txt()
            satellite_list = []
            i = 1
            while i < (len(results) - 1):
                name = results[i].strip()
                i += 1
                line_one = results[i].strip()
                i += 1
                line_two = results[i].strip()
                i += 1
                new_sat = models.Satellite(name, line_one, line_two)
                satellite_list.append(new_sat)
            return satellite_list
        except (DalException, Exception):
            logger.error('unable to get satellite data from database.')
            raise BusinessLogicException


def get_sat_names_list():
    """
    generates a list of all satellite names in the database, so they can be printed to the gui, or so a searched
        for satellite name can be validated.
    :return: a list of all satellite names in the database.
    """
    try:
        sat_list = sat_tle_data_to_list()
        sat_names_list = []
        for satellite in sat_list:
            sat_names_list.append(satellite.name)
        return sat_names_list
    except BusinessLogicException:
        logger.error('Unable to get satellite names list. Probably not good...')
        raise


def get_data_for_one_sat(sat_name: str, forecast, latitude, longitude):
    """
    takes a satellite name, list of forecast objects, latitude and longitude from the gui, and turns that into a
        list of satellite Event objects using the get_events method from the Satellite class.
    :param sat_name: the name of the satellite in question, from the gui
    :param forecast: a list of forecast objects, generated from forecast_service.py
    :param latitude: the user's latitude, generated by calling the get_lat_long method.
    :param longitude: the user's longitude, generated by calling the get_lat_long method.
    :return: a list of satellite events (Event objects).
    """
    try:
        # get a list of Satellite objects from the above method.
        sat_list = sat_tle_data_to_list()
        # I add one day to the current date below, due to the time difference between us and UTC, it was generating
        # day old data before I made this decision. I am aware we are only 5 hours behind UTC,
        # so that doesn't make much sense to me, all I know is this fixed it.
        current_day = date.today() + timedelta(days=1)
        # I don't think 9 is a magic number below, because the parameter name clearly indicates what it means.
        final_day = current_day + timedelta(days=9)
        # Grab the timezone data from a forecast, here I arbitrarily chose the first index.
        # I had to pick one since they're in a list, but any Forecast in the list would work here.
        timezone = forecast[0].timezone_offset
        for item in sat_list:
            if item.name == sat_name:
                # if the name of the satellite matches the name from the gui, generate an event
                result = item.get_events(latitude, longitude, current_day.strftime('%Y-%m-%d'),
                                         final_day.strftime('%Y-%m-%d'), timezone)
                # so this returns a list of Event objects
                return result
    except (DalException, Exception):
        logger.error('Unable to get data for one satellite')
        raise BusinessLogicException


def get_lat_long(address: str):
    """
    calls on the get_lat_long function in the dal to return a latitude and longitude from Open Street Maps for a
        given address.
    :param address: the user's address they enter into the gui form
    :return: the results of dal.get_lat_long()
    """
    try:
        return dal.get_lat_long(address)
    except DalException:
        logger.error('unable to get lat & long from open street maps')
        raise BusinessLogicException


def write_results_to_txt(results):
    """
    calls the dal.write_results_to_txt method to write results from the gui to results_export.txt
    :param results: the results from the gui results_text field.
    :return: really nothing, calls a method from the dal to write data to a text file...
    """
    try:
        return dal.write_results_to_txt(results)
    except DalException:
        raise BusinessLogicException
