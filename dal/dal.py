import requests
from exceptions import DalException
from datetime import date, datetime
from config import DATABASE_PATH
from logging_config import get_logger

"""
This module contains methods for gathering data from various sources and passing that data off to other modules in 
this program.

Methods:
--------
    get_sat_tle_data():
        retrieves satellite TLE data from celestrak.org. 
    sat_tle_data_to_txt():
        writes the satellite TLE data to a text file (called satellites.db). I had to implement this because celestrak
        suspended my access for 2 hours on two separate occasions... the data is only updated once per day on their end 
        anyway. 
    read_tle_data_from_txt() -> list:
        reads satellite TLE data from satellites.db, returns it as a list (one line from data = one list item)
    check_sat_tle_data_date():
        checks the date on the first line of satellites.db, returns that date (as datetime.date object)
    get_lat_long(address: str) -> tuple:
        gets latitude and longitude for a given address from Open Street Maps api. 
    get_sunset_sunrise(latitude, longitude, start_date, end_date):
        gets hourly forecast data for given dates and location from VisualCrossing api. 
    write_results_to_txt(results):
        writes results from the gui to a text file called results_export.txt
        
Constants:
----------
    GOOD_RESPONSE_CODE: the response code we want from an api. 
"""

logger = get_logger(__name__)
GOOD_RESPONSE_CODE = 200


def get_sat_tle_data():
    """
    retrieves satellite TLE data from celestrak.org.
    :return: the results from celestrak.org (20+ thousand lines of satellite TLE data).
    """
    url = f"https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle"
    try:
        results = requests.get(url)
        if results.status_code == GOOD_RESPONSE_CODE:
            logger.info('successfully grabbed TLE data from celestrak.org')
            return results.text
        else:
            logger.error('not successful in grabbing TLE data from celestrak.org')
            raise DalException
    except Exception:
        logger.error('not successful in grabbing TLE data from celestrak.org')
        raise DalException


def sat_tle_data_to_txt():
    """
    writes the satellite TLE data to a text file (called satellites.db). I had to implement this because celestrak
        suspended my access for 2 hours on two separate occasions... the data is only updated once per day on their end
        anyway.
    :return: no return, writes data to satellites.db
    """
    logger.info('attempting to write TLE data to satellites.db')
    try:
        results = get_sat_tle_data()
        if results:
            today = date.today()
            today = datetime.strftime(today, "%Y-%m-%d")
            with open(DATABASE_PATH, 'w', newline='') as file:
                file.write(f"{today}\n")  # so I can check the last time the data was downloaded.
                for line in results:
                    file.write(line)
            logger.info('successfull wrote TLE data to satellites.db')
        else:
            logger.error('unable to load data from celestrak.org to satellites.db')
            raise DalException
    except Exception:
        logger.error('unable to load data from celestrak.org to satellites.db')
        raise DalException


def read_tle_data_from_txt() -> list:
    """
    reads satellite TLE data from satellites.db, returns it as a list (one line from data = one list item)
    :return: a list of satellite TLE data. (one line from data = one list item)
    """
    try:
        logger.info('reading info from satellites.db')
        data_list = []
        with open(DATABASE_PATH, 'r') as file:
            for line in file:
                if line != '':  # pycharm likes to add a blank line at the end of files...
                    data_list.append(line.rstrip('\n'))
        logger.info('successfully read data from satellites.db')
        return data_list
    except Exception:
        logger.error('unable to read data from satellites.db')
        raise DalException


def check_sat_tle_data_date() -> date:
    """
    checks the date on the first line of satellites.db, returns that date (as datetime.date object)
    :return: date from satellites.db (as datetime.date object)
    """
    try:
        with open(DATABASE_PATH, 'r') as file:
            last_update_date = file.readline()
            last_update_date = last_update_date.strip()
            last_update_date = datetime.strptime(last_update_date, "%Y-%m-%d").date()
        logger.info('checking date for satellites.db')
        return last_update_date
    except Exception:
        logger.error('unable to check date for satellites.db')
        raise DalException


def get_lat_long(address: str) -> tuple:
    """
    gets latitude and longitude for a given address from Open Street Maps api.
    :param address: user's address they entered into the gui
    :return: latitude and longitude for the user, in the form of a tuple.
    """
    url = 'https://nominatim.openstreetmap.org/search'
    params = {
        'format': 'json',
        'q': address
    }
    logger.info('grabbing latitude and longitude from openstreetmap')
    coords_response = requests.get(url, params=params)
    if coords_response.status_code == GOOD_RESPONSE_CODE:
        coords_response = coords_response.json()
        try:
            lat_long = (coords_response[0]['lat'], coords_response[0]['lon'])
            return lat_long
        except Exception:
            logger.error(f'unable to get coords for address {address}')
            raise DalException
    else:
        logger.error(f'unable to get coords for address {address}, bad response code')
        raise DalException


def get_sunset_sunrise(latitude, longitude, start_date, end_date):
    """
    gets hourly forecast data for given dates and location from VisualCrossing api.
    :param latitude: the user's latitude
    :param longitude: the user's longitude
    :param start_date: the start date you would like to forecast
    :param end_date: the last day you want the forecast for
    :return: weather data from VisualCrossing in JSON format
    """
    url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{latitude},{longitude}/{start_date}/{end_date}"
    params = {
        'key': '7VGGR8GZQBVWFMPQ276TFHMKM',
        'elements': "datetime,moonphase,sunrise,sunset,moonrise,moonset,conditions"
    }
    logger.info('attempting to get sunrise/sunset times from visualcrossing')
    response = requests.get(url, params=params)
    if response.status_code == GOOD_RESPONSE_CODE:
        response = response.json()
        if response:
            logger.info('succesffuly retireved sunrise/sunset times')
            return response
        else:
            logger.error('unable to retrieve sunrise/sunset times')
            raise DalException
    else:
        logger.error('unable to retrieve sunrise/sunset times, bad response code')
        raise DalException


def write_results_to_txt(results):
    """
    writes results from the gui to a text file called results_export.txt
    :param results: results from the results field in the gui
    :return: nothing, writes to file
    """
    try:
        with open('results_export.txt', 'w', newline='', encoding='UTF 8') as file:
            for line in results:
                file.write(line)
        logger.info('exported results to csv')
    except Exception:
        logger.error('unable to export results to csv')
        raise DalException
