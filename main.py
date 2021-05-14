__author__ = "Jose Arturo Ramirez Perez"
__credits__ = ["Jose Arturo Ramirez Perez"]
__license__ = "GPL"
__version__ = "1.0.2"
__maintainer__ = "Jose Arturo Ramirez Perez"
__email__ = "arturor19@gmail.com"
__status__ = "Staging"


from fastapi import FastAPI
import os
from fastapi.responses import JSONResponse
from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
import json
import time
import pickle
import requests
import portolan
import numpy as np
from beaufort_scale import beaufort_scale_ms
import datetime

app = FastAPI()


if os.name == 'nt':
    cache_folder = "\__pycache__\\"
else:
    cache_folder = "/__pycache__/"

cwd = os.getcwd()
cache_dir = (cwd + cache_folder)


# Class to collect the information and transform it in human readable
class GetWeather(object):
    """
        Transform the JSON data weather to human readable through functions

            Parameters:
                    city (str): String with city value
                    country (str): String with country value
    """
    def __init__(self, city: str, country: str):
        self.weather_dict_source = {}
        self.city = city
        self.country = country.lower()
        self.api_source = "http://api.openweathermap.org/data/2.5/weather"
        self.params = {
            'q': f'{self.city},{self.country}',
            'appid': '1508a9a4840a5574c822d70ca2132032'
        }
        self.headers = {'Accept': '*/*',
                        'Content-Type': 'application/json'}


    def get_api_dict(self):
        """
        Get the json data from the API source and convert in dict
        :return:
        Dictionary : Source api JSON to dict info
        """
        response = requests.get(self.api_source, headers=self.headers, params=self.params, verify=False)
        self.weather_dict_source = (json.loads(response.text))
        return self.weather_dict_source


    @staticmethod
    def get_cloudiness_status(value: int):
        """
        Retrieve the corresponding key as string matching the arrays
        :return
        String : cloudiness status """
        cloud_val = {
            "No clouds": [0],
            "Few clouds": np.arange(1, 10, 1),
            "Isolated clouds": np.arange(10, 25, 1),
            "Scattered clouds": np.arange(25, 50, 1),
            "Broken clouds": np.arange(50, 91, 1),
            "Overcast": np.arange(91, 101, 1)
        }

        return "".join(key_cloud for key_cloud, value_cloud in cloud_val.items() if value in value_cloud)


    def human_readable_dict(self):
        """
        Transforming the source dictionary to another with the corresponding values and conversions
        :return:
        Dictionary : Human readable dictionary with conversions details
        """
        wa_dict = self.get_api_dict() # Calling the function to get the source dictionary
        city = wa_dict["name"].replace(" City", "")
        country = wa_dict["sys"]["country"]
        temperature = int(wa_dict["main"]["temp"] / 10)
        wind_deg = wa_dict["wind"]["deg"]
        wind_speed = round(wa_dict["wind"]["speed"], 1)
        wind_str_speed = beaufort_scale_ms(wind_speed)
        wind_compass = portolan.point(wind_deg)
        cloudiness = self.get_cloudiness_status(wa_dict["clouds"]["all"])
        pressure = wa_dict["main"]["pressure"]
        humidity = wa_dict["main"]["humidity"]
        sunrise = datetime.datetime.fromtimestamp(wa_dict["sys"]["sunrise"]).strftime('%H:%M')
        sunset = datetime.datetime.fromtimestamp(wa_dict["sys"]["sunset"]).strftime('%H:%M')
        geo_coordinates = [round(wa_dict["coord"]["lat"], 2), round(wa_dict["coord"]["lon"], 2)]
        forecast = {'description': wa_dict["weather"][0]['description']}
        now = datetime.datetime.now()
        dt_string = now.strftime("%Y-%m-%d %H:%M:%S")
        self.hr_dict = {
            "location_name": f"{city}, {country}",
            "temperature": f"{temperature} °C",
            "wind": f"{wind_str_speed}, {wind_speed}m/s, {wind_compass}",
            "cloudiness": f"{cloudiness}",
            "pressure": f"{pressure} hpa",
            "humidity": f"{humidity}%",
            "sunrise" : f"{sunrise}",
            "sunset": f"{sunset}",
            "geo_coordinates": f"{geo_coordinates}",
            "requested_time": f"{dt_string}",
            "forecast": forecast
        }
        return self.hr_dict


@app.get('/weather')
async def get_weather(country: str, city: str):
    """
    Get method to return the corresponding information for country through the object GetWeather
    :return:
    JSON : JSON with human readable weather details
    """
    try:
        dict_file = (city + "_" + country + ".pkl")
        if os.path.isfile(cache_dir + dict_file):
            st = os.stat(cache_dir + dict_file)
            cache_time = time.time() - 120
            min_time = st.st_mtime
            if min_time < cache_time:  ## Validate older than cache_time
                os.remove(cache_dir + dict_file)
                dict_weather = GetWeather(city, country).human_readable_dict()
                temp_file = open(cache_dir + city + "_" + country + ".pkl", "wb")
                pickle.dump(dict_weather, temp_file)
                temp_file.close()
            else:
                with open(cache_dir + dict_file, 'rb') as handle:
                    dict_weather = pickle.load(handle)
        else:
            dict_weather = GetWeather(city, country).human_readable_dict()
            temp_file = open(cache_dir + city + "_" + country + ".pkl", "wb")
            pickle.dump(dict_weather, temp_file)
        json_compatible_item_data = jsonable_encoder(dict_weather)
        resp = JSONResponse(content=json_compatible_item_data)
    except:
        dict_weather = {"id_code": 404, "description": "Please validate your entries"}
        json_compatible_item_data = jsonable_encoder(dict_weather)
        resp = JSONResponse(content=json_compatible_item_data)
        raise HTTPException(status_code=404, detail="Item not found")
    return resp


