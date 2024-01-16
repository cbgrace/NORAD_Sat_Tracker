import dal
from datetime import date, timedelta
from exceptions import BusinessLogicException, DalException
import models
from logging_config import get_logger

"""
This module contains a single method for parsing forecast data from the VisualCrossing weather API into a list of 
Forecast class objects. 

Method(s):
---------
    get_forecast_data(latitude, longitude):
        Uses dal.get_sunset_sunrise() to retrieve data from VisualCrossing API, then parses that data into a list of 
        usable Forecast objects. 
        
Constants:
----------
    TODAYS_DATE: a datetime object containing the current date
    TEN_DAYS_LATER: a datetime object containing the current date + 9.
"""

logger = get_logger(__name__)
TODAYS_DATE = date.today()
TEN_DAYS_LATER = TODAYS_DATE + timedelta(days=9)


def get_forecast_data(latitude, longitude):
    """
    Uses dal.get_sunset_sunrise() to retrieve data from VisualCrossing API, then parses that data into a list of
        usable Forecast objects.
    :param latitude: the user's latitude
    :param longitude: the user's longitude
    :return: a list of Forecast objects.
    """
    try:
        logger.info('attempting to get forecast data')
        # get today's date and the date for ten days from now
        start_date = TODAYS_DATE
        end_date = TEN_DAYS_LATER
        # get forecast data from the dal
        response = dal.get_sunset_sunrise(latitude, longitude, start_date, end_date)
        relevant_data = []
        i = 0
        # grab the timezone offset from the forecast data, because it is not contained in the same level of the json
        # as the other data.
        timezone = response['tzoffset']
        # then go through each day in the response and grab all other needed data.
        for day in response['days']:
            forecast_date = day['datetime']
            sunrise = day['sunrise']
            sunset = day['sunset']
            moonphase = day['moonphase']
            # I ran into an error where the moonset was not included one day...
            if 'moonrise' in day:
                moonrise = day['moonrise']
            else:
                moonrise = 0
            if 'moonset' in day:
                moonset = day['moonset']
            else:
                moonset = 0
            hour_and_conditions_dict = {}
            for hour in response['days'][i]['hours']:
                hour_and_conditions_dict[hour['datetime']] = hour['conditions']
            i += 1
            # create a Forecast object with the data
            new_forecast = models.Forecast(forecast_date, sunrise, sunset, moonphase, moonrise, moonset, timezone,
                                           hour_and_conditions_dict)
            # append it to my list to be returned.
            relevant_data.append(new_forecast)
        logger.info('Successfully gathered relevant forecast data.')
        return relevant_data
    except (DalException, Exception):
        logger.error('Unable to gather forecast data...')
        raise BusinessLogicException


