import json
import sys

from werkzeug.utils import redirect
from wtforms import StringField, PasswordField, BooleanField, SubmitField
import requests
from flask_wtf import FlaskForm
from flask import Flask, render_template, url_for
from dotenv import load_dotenv
from config import Config
from constants import BASE_URL, FORBIDDEN_CITY
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
    url = f'{BASE_URL}{city}&appid={Config.SECRET_KEY}'
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
            sys.exit()
        return redirect(url_for('weather_display', weather_info = weather_info))

    return render_template('home.html', title = 'Home', form=form)


@app.route('/weather/<weather_info>')
def weather_display(weather_info:json):
  return render_template('weather.html', weather_info =weather_info)