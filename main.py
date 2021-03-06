import json
import sys
import geopandas
import geopandas as gpd
import matplotlib
import matplotlib.pyplot as plt
import requests
from dotenv import load_dotenv
from flask import Flask, render_template, url_for, make_response
from flask_wtf import FlaskForm
from shapely.geometry import Point
from werkzeug.utils import redirect
from wtforms import StringField, SubmitField
from config import Config
from constants import BASE_URL, FORBIDDEN_CITY, BASE_FUTURE_URL

import datetime
import timezonefinder, pytz



matplotlib.use('Agg')
import os
import glob
import logging

load_dotenv()


app = Flask(__name__)
app.config.from_object(Config)
tf = timezonefinder.TimezoneFinder()

class CitySearch(FlaskForm):
    city = StringField('City')
    submit = SubmitField('Search')

def return_current_time(latitude:float, longitude:float):
    # From the lat/long, get the tz-database-style time zone name (e.g. 'America/Vancouver') or None
    timezone_str = tf.certain_timezone_at(lat=latitude, lng=longitude)

    if timezone_str is None:
        print("Could not determine the time zone")
    else:
        # Display the current time in that time zone
        timezone = pytz.timezone(timezone_str)
        dt = datetime.datetime.utcnow()
        '%Y-%m-%d %h:%m:%s'
        current_time = dt + timezone.utcoffset(dt)

        return current_time.strftime("%Y-%m-%d %H:00")

def return_weather_info(city:str) -> json:
    '''

    :param city: Name of the city to return weather information
    :return: Weather information of the cty in jsocn format
    '''
    url = f'{BASE_URL}{city}&appid={Config.SECRET_KEY}&units=metric'
    response = requests.get(url)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print('Wrong City?')

    return response.json()


def return_future_weather_info(city:str) -> json:
    '''

    :param city: Name of the city to return weather information
    :return: Weather information of the cty in json format
    '''
    url = f'{BASE_FUTURE_URL}{city}&appid={Config.SECRET_KEY}&units=metric&cnt=16'
    response = requests.get(url)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print('Wrong City?')
    print(response.json())

    return response.json()


@app.route('/', methods=['GET', 'POST'])
def index():
    form = CitySearch()
    if form.validate_on_submit():
        weather_info = return_weather_info(form.city.data)
        future_info = return_future_weather_info(form.city.data)
        if form.city.data.upper() == FORBIDDEN_CITY.upper():
            return redirect(url_for('forbidden'))
        return redirect(url_for('weather_display', weather_info = weather_info, future_info =future_info))

    return render_template('home.html', title = 'Home', form=form)


def send_future_times(future_info, current_time):
    dates = future_info.get('list')
    current_time = datetime.datetime.strptime(current_time, "%Y-%m-%d %H:00")
    for i,j in enumerate(dates):
        stated_time = datetime.datetime.strptime(j.get('dt_txt'), "%Y-%m-%d %H:%M:%S")
        if stated_time > current_time:
            dates.pop(0)
            return future_info
        else:
            dates.pop(i)




@app.route('/weather/<weather_info>/<future_info>')
def weather_display(weather_info:json, future_info):
    weather_info = weather_info.replace("\'", "\"")
    weather_info = json.loads(weather_info)
    future_info = future_info.replace("\'", "\"")
    future_info = json.loads(future_info)
    latitude = weather_info.get('coord').get('lat')
    longitude =weather_info.get('coord').get('lon')
    image = generate_image(longitude, latitude)
    current_time = return_current_time(float(latitude),float(longitude))
    future_info = send_future_times(future_info, current_time)

    resp = make_response(render_template('weather.html', weather_info = weather_info,
                                         user_image = image, future_info =future_info, current_time = current_time))
    return resp

def generate_image(longitude, latidude):
    delete_files('./static/map/')
    d = {'col1': ['name1'], 'geometry': [Point(longitude, latidude)]}
    gdf = gpd.GeoDataFrame(d, crs="EPSG:4326")

    world = geopandas.read_file(geopandas.datasets.get_path('naturalearth_lowres'))

    # We restrict to South America.
    ax = world.plot(
        color='white', edgecolor='black')

    # We can now plot our ``GeoDataFrame``.
    gdf.plot(ax=ax, color='red')

    plt.savefig(f'./static/map/{longitude}_{latidude}.png')
    return f'/static/map/{longitude}_{latidude}.png'



@app.route('/forbidden')
def forbidden():

    return render_template('forbidden_city.html')


def delete_files(final_directory: str):
    """
    Deletes all files within a specified directory

    :param: final directory: The directory to remove the files from
    """
    if os.path.exists(final_directory):
        files = glob.glob(f"{final_directory}/*")
        for f in files:
            try:
                os.remove(f)
            except FileNotFoundError:
                logging.warning(f"File: {f} could not be found")
        if len(os.listdir(final_directory)) > 0:
            logging.error(f"The directory {final_directory} was not empty - exiting")
            sys.exit()
    else:
        logging.error(f"The directory {final_directory} does not exist - exiting")
        raise AssertionError



