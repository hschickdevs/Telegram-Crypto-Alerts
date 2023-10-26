"""
Features Needed:
* taapi.io api key
* Aggregate each symbol and indicator, then pull all available indicators using the taapi.io client
* Allow the user to save indicator templates so that they don't have to enter long ones again
* Message to telegram should be a list of indicators with their documentation hyperlinked:
    - https://stackoverflow.com/questions/45268368/how-to-send-a-hyperlink-in-bot-sendmessage
    - Example:
      ABOVE
      BELOW
      PCTCHG
      MAXINDEX (Index of highest value over a specified period)
      MEDPRICE (Median Price)
      SAR (Parabolic Sar)
      SIN (Vector Trigonometric Sin)
* Need a combination of indicators (AND/OR)
"""
from dataclasses import dataclass
import json
from time import time, sleep
from os import getcwd, mkdir
from os.path import join, isdir, dirname, abspath
from typing import Union
import os
from math import ceil

from .user_configuration import get_whitelist, LocalUserConfiguration, MongoDBUserConfiguration
from .config import *
from ._logger import logger

import requests
from ratelimit import limits, sleep_and_retry


class TADatabaseClient:
    """This client should handle the cross-process operations of the technical analysis indicators database"""
    def build_ta_db(self):
        pass

    def dump_ref(self, data: dict) -> None:
        """Update the technical analysis indicators database"""
        with open(TA_DB_PATH, 'w') as out:
            out.write(json.dumps(data, indent=2))

    def fetch_ref(self) -> dict:
        """Get the location of and return the technical analysis indicators database in JSON format"""
        return json.loads(open(TA_DB_PATH).read())

    def add_indicator(self, indicator_id: str, name: str, endpoint: str, reference_url: str,
                      params: list[tuple[str, str, bool]], output: list[str], indicator_type: str = "t") -> None:
        """
        Add an indicator to the TA database. 
        If the indicator already exists, it will be overwritten with the new data.

        :param indicator_id: The uppercase indicator ID a shown on taapi.io (e.g. 2CROWS)
        :param name: The indicator name as shown on taapi.io (e.g. Two Crows)
        :param endpoint: The endpoint URL following this format:
                         https://api.taapi.io/2crows?secret={api_key}&exchange=binance
        :param reference_url: The link to the indicator's documentation on taapi.io
        :param params: List of tuples containing parameter data
            - param_id: The ID for the parameter as shown on the API parameters documentation (e.g. "symbol")
            - param_description: A docstring that lets the user know what data the parameter expects
            - param_default: The default value for the parameter, or None if the parameter is strictly required
        :param output: List of output variables that are returned by the API so that the user can choose which
                       to use, and so that the bot can know how to process the response.
                       NOTE: All return types for the output_values are considered as FLOAT
        :param indicator_type: "s" for simple indicator, and "t" for technical indicator
        """
        db = self.fetch_ref()
        db[indicator_id.upper()] = {"name": name, "endpoint": endpoint, "ref": reference_url,
                                    "params": params, "output": output, "type": indicator_type}
        self.dump_ref(db)
        print(f"{name} ({indicator_id}) indicator added to TA database.")

    def get_indicator(self, _id: str, key = None):
        """Returns the indicator data from the database"""
        try:
            if key is not None:
                return self.fetch_ref()[_id.upper()][key]
            else:
                return self.fetch_ref()[_id.upper()]
        except KeyError:
            raise ValueError(f"'{_id}' is an invalid indicator ID")

    def validate_indicator(self, indicator: str, args: list = None) -> Union[dict, None]:
        """
        :param indicator: The uppercase indicator symbol
        :param args: Any param or output IDs
        :return: indicator if one is found and valid, None if not valid.
        """
        db = self.fetch_ref()

        try:
            indicator = db[indicator]
        except KeyError:
            return None

        if args is not None:
            params = [param[0] for param in indicator["params"]]
            output_vals = [val[0] for val in indicator["output"]]
            if not any(arg in params or arg in output_vals for arg in args):
                return None

        return indicator


class TAAggregateClient:
    def __init__(self):
        self.indicators_db_cli = TADatabaseClient()
        self.indicators_reference = self.indicators_db_cli.fetch_ref()

    def build_ta_aggregate(self, ta_db: dict = None):
        """
        Build the TA aggregate of all users' alert databases to update the technical analysis reference
        (Simply constructs the aggregate, does not call the API)
        
        :param ta_db: Can optionally be provided if the ta_db is already stored in a higher level function.

        Structure Reference:

        {
            symbol: {
                interval: {
                    [bulk_query_formatted_alert]
                }
            }
        }
        """
        # logger.info("Building TA aggregate...")

        if ta_db is None:
            ta_db = self.indicators_reference

        # Fetch the old aggregate to get previous values
        try:
            old_agg = self.load_agg()
        except FileNotFoundError:
            old_agg = {}
            self.dump_agg(old_agg)
        except Exception as exc:
            logger.exception('Could not load TA aggregate', exc_info=exc)
            raise exc

        # Create the new aggregate to weed out unused indicators:
        agg = {}
        for user in get_whitelist():
            alerts_data = LocalUserConfiguration(user).load_alerts() \
                if not USE_MONGO_DB else MongoDBUserConfiguration(user).load_alerts()

            for symbol, alerts in alerts_data.items():
                if symbol not in agg.keys():
                    agg[symbol] = {}
                for alert in alerts:
                    if alert['type'] == 's':
                        continue
                    if alert['interval'] not in agg[symbol].keys():
                        agg[symbol][alert['interval']] = []

                    # Build the alert to store in the aggregate with format prepared to be sent to the API in bulk call
                    formatted_alert = self.format_alert_for_match(alert)

                    # Attempt to find an existing match to have previous values persist
                    match = None
                    try:
                        for indicator in old_agg[symbol][alert['interval']]:
                            try:
                                if all(indicator[k] == v for k, v in formatted_alert.items()):
                                    match = indicator
                                    break
                            except KeyError:
                                continue
                    except KeyError:
                        pass
                    if match is not None:
                        formatted_alert = match
                    else:
                        formatted_alert["values"] = {var: None for var in ta_db[alert['indicator'].upper()]['output']}
                        formatted_alert["last_update"] = 0

                    # Add the formatted alert to the database
                    agg[symbol][alert['interval']].append(formatted_alert)

        # Update the aggregate with the new data
        self.dump_agg(agg)
        # logger.info("TA aggregate built.")

    def format_alert_for_match(self, alert: dict):
        formatted_alert = {"indicator": alert['indicator'].lower()}
        for param, _, default_value in self.indicators_db_cli.get_indicator(_id=alert['indicator'].upper(), key="params"):
            try:
                formatted_alert[param] = alert["params"][param]
            except KeyError:
                formatted_alert[param] = default_value

        return formatted_alert

    def dump_agg(self, data: dict) -> None:
        if not os.path.isdir(os.path.dirname(AGG_DATA_LOCATION)):
            os.mkdir(os.path.dirname(AGG_DATA_LOCATION))
        with open(AGG_DATA_LOCATION, 'w') as outfile:
            outfile.write(json.dumps(data, indent=2))

    def load_agg(self) -> dict:
        try:
            with open(AGG_DATA_LOCATION, 'r') as infile:
                return json.load(infile)
        except FileNotFoundError:
            self.dump_agg({})
            return self.load_agg()

    def clean_agg(self) -> None:
        """Remove all unused indicators from the aggregate"""
        try:
            agg = self.load_agg()
        except Exception as exc:
            logger.exception('Could not load TA aggregate to clean', exc_info=exc)
            raise exc


class TaapiioProcess:
    """Taapi.io process should be run in a separate thread to allow for sleeping between API calls"""
    def __init__(self, taapiio_apikey: str, telegram_bot_token: str = None):
        self.apikey = taapiio_apikey
        self.last_call = 0  # Implemented instead of the ratelimit package solution to solve the buffer issue
        self.ta_db = TADatabaseClient().fetch_ref()  # TA DB is static and can be loaded once
        self.agg_cli = TAAggregateClient()
        self.tg_bot_token = telegram_bot_token  # Can be left blank, but the process wont be able to report errors

    @sleep_and_retry
    @limits(calls=1, period=round(RATE_LIMITS[1] * (1 + RATE_LIMITS[2]), 1))
    def call_api(self, endpoint: str, params: dict, r_type: str = "POST") -> dict:
        """
        Calls the taapi.io API and returned the response in JSON format
        
        Free API key limit is 1 call every 15 seconds, we use +1 to add a safety buffer
        """
        if r_type == "GET":
            return requests.get(endpoint.format(api_key=self.apikey), params=params).json()
        elif r_type == "POST":
            logger.info(f"Sending bulk query to API: {params}")
            return requests.post(endpoint, json=params).json()

    def mainloop(self):
        """
        Run the process mainloop as fast as possible while respecting the API call limit

        Exceptions should be handled at a higher level than this function
        """
        logger.warn("Taapi.io process started.")
        previous_rates = []  # Store the last 5 values for process time to fetch and update all values in the aggregate
        while True:
            start = time()
            num_indicators = 0

            # 1. Build to aggregate before every cycle
            self.agg_cli.build_ta_aggregate(self.ta_db)

            # 2. Poll all values from the aggregate using bulk queries to the taapi.io API 
            aggregate = self.agg_cli.load_agg()
            if all(len(v) == 0 for v in aggregate.values()):
                sleep(0.1)  # To prevent excessive spamming
                continue

            for symbol, intervals in aggregate.items():
                for interval, indicators in intervals.items():
                    num_indicators += len(indicators)  # For logging

                    # Prepare the bulk query for the API
                    EXCLUDE_INDICATOR_KEYS = ["values", "last_update"]
                    indicators_query = [{k: v for k, v in indicator.items() if k not in EXCLUDE_INDICATOR_KEYS}
                                        for indicator in indicators]
                    query = {"secret": self.apikey, "construct": {"exchange": DEFAULT_EXCHANGE, "symbol": symbol,
                                                                   "interval": interval, "indicators": indicators_query}}
                    r = self.call_api(endpoint=BULK_ENDPOINT, params=query)
                    try:
                        responses = r["mappings"]
                    except KeyError:
                        # if "error" in r.keys():
                        #     logger.warn(f"Taapio error occurred when building aggregate: {r['error']}")
                        raise Exception(f"Error occurred calling taapi.io API - {r}")

                    # Assign returned values and update aggregate:
                    for i, response in enumerate(responses):
                        for output_variable in self.ta_db[indicators[i]["indicator"].upper()]["output"]:
                            indicators[i]["values"][output_variable] = response["result"][output_variable]
                        indicators[i]["last_update"] = int(time())

            # 3. Dump aggregate with updated values so that the alerts client can reference it
            self.agg_cli.dump_agg(aggregate)
            # print("End Aggregate:")
            # print(json.dumps(aggregate, indent=2))

            # Logging
            previous_rates.append(round(time() - start, 1))
            if len(previous_rates) > 3:
                del previous_rates[0]
            logger.info(f"TA Aggregate updated. "
                        f"Average through process rate: {round(sum(previous_rates) / len(previous_rates), 1)} seconds")

    def alert_admins(self, message: str) -> None:
        if self.tg_bot_token is None:
            logger.warn(f"Attempted to alert admins, but no telegram bot token was set: {message}")
            return None

        for user in get_whitelist():
            admin = LocalUserConfiguration(user).admin_status() \
                if not USE_MONGO_DB else MongoDBUserConfiguration(user).admin_status()

            if admin:
                requests.post(url=f'https://api.telegram.org/bot{self.tg_bot_token}/sendMessage',
                              params={'chat_id': user, 'text': message})

    def run(self) -> None:
        restart_period = 15
        try:
            self.mainloop()
        except KeyboardInterrupt:
            return
        except Exception as exc:
            logger.critical(f"An error has occurred in the mainloop - restarting in 5 seconds...", exc_info=exc)
            self.alert_admins(message=f"A critical error has occurred in the TaapiioProcess "
                                      f"(Restarting in {restart_period} seconds) - {exc}")
            sleep(restart_period)
            return self.run()