import numpy as np

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, desc

import datetime as dt
from datetime import date, timedelta

from flask import Flask, jsonify


#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)

# Save reference to the table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################

# Home page route
@app.route("/")
def welcome():
    """List all available api routes."""
    return (f"Welcome to the home page!<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/start<br/>"
        f"/api/v1.0/startend"  
    )

# Precipitation route
@app.route("/api/v1.0/precipitation")
def precipitation():
  end_date = session.query(Measurement).order_by(desc('date')).first()
  recent = end_date.date
  format_str = '%Y-%m-%d'
  datetime_recent = dt.datetime.strptime(recent, format_str)
  year_ago = datetime_recent - dt.timedelta(days=365)
  results = session.query(Measurement.date, Measurement.prcp).\
  filter(Measurement.date >= year_ago).all()

  # Create dictionary from the results data and append to a list
  prcp_dict = {}
  for measurement in results:
      prcp_dict[f"{measurement.date}"] = measurement.prcp
  return jsonify(prcp_dict)

# Stations route
@app.route("/api/v1.0/stations")
def stations():
  """Return a list of all station names"""
  # Query all stations
  stats = session.query(Station.name).all()

  # Put all station names into list
  station_names = []
  for each in stats:
    station_names.append(each)

  return jsonify(station_names)

# Temperature route
@app.route("/api/v1.0/tobs")
def temperature():
  end_date = session.query(Measurement).order_by(desc('date')).first()
  recent = end_date.date
  format_str = '%Y-%m-%d'
  datetime_recent = dt.datetime.strptime(recent, format_str)
  year_ago = datetime_recent - dt.timedelta(days=365)

  results = session.query(Measurement.tobs, Measurement.date).\
    filter(Measurement.date >= year_ago).all()
  
  all_temps = list(np.ravel(results))

  return jsonify(all_temps)

# Define function to take min, avg, and max temperatures on or after a designated day
def start_temp(day):
    sel = [func.min(Measurement.tobs),
          func.avg(Measurement.tobs),
          func.max(Measurement.tobs)]
    
    summary = session.query(*sel).filter(func.strftime(Measurement.date)>=day).all()
    return summary

# Start date route
@app.route("/api/v1.0/start")
def start():
  results = start_temp('2016-05-21')
  starttemps = list(np.ravel(results))
  return jsonify(starttemps)

def daily_normals(date):
  sel = (func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs))
  return session.query(*sel).filter(func.strftime("%m-%d", Measurement.date) == date).all()

# Start/end route
@app.route("/api/v1.0/startend")
def startend():
  # Set the start and end date of the trip
  start_date = "2017-06-01"
  end_date = "2017-06-08"

  # Use the start and end date to create a range of dates
  start = dt.datetime.strptime(start_date, '%Y-%m-%d').date()
  end = dt.datetime.strptime(end_date, '%Y-%m-%d').date()
  diff = end - start
  dates = []
  for day in range(diff.days + 1):
    dates.append(start + timedelta(day))
  # Stip off the year and save a list of %m-%d strings
  string_dates = []
  for date in dates:
    d = date
    string_dates.append(d.strftime("%m-%d"))
  # Loop through the list of %m-%d strings and calculate the normals for each date
  normals = []
  for each in string_dates:
    a = []
    entry = daily_normals(each)
    a.append(entry)
    for each in a:
      x = a.pop()[0]
      normals.append(x)
  return jsonify(normals)

if __name__ == '__main__':
    app.run(debug=True)