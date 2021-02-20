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
from constants import BASE_URL, FORBIDDEN_CITY
matplotlib.use('Agg')
import os
import glob
import logging

load_dotenv()


app = Flask(__name__)
app.config.from_object(Config)

class CitySearch(FlaskForm):
    city = StringField('City')
    submit = SubmitField('Search')

def return_weather_info(city:str) -> json:
    '''

    :param city: Name of the city to return weather information
    :return: Weather information of the cty in json format
    '''
    url = f'{BASE_URL}{city}&appid={Config.SECRET_KEY}&units=metric'
    response = requests.get(url)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print('Wrong City?')

    return response.json()



@app.route('/', methods=['GET', 'POST'])
def index():
    form = CitySearch()
    if form.validate_on_submit():
        weather_info = return_weather_info(form.city.data)
        if form.city.data.upper() == FORBIDDEN_CITY.upper():
            return redirect(url_for('forbidden'))
        return redirect(url_for('weather_display', weather_info = weather_info))

    return render_template('home.html', title = 'Home', form=form)


@app.route('/weather/<weather_info>')
def weather_display(weather_info:json):
    weather_info = weather_info.replace("\'", "\"")
    weather_info = json.loads(weather_info)
    image = generate_image(weather_info.get('coord').get('lon'), weather_info.get('coord').get('lat'))
    resp = make_response(render_template('weather.html', weather_info = weather_info, user_image = image))
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



