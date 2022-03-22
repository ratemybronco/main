# from crypt import methods
from flask import Flask, redirect, render_template, request
import base64
from io import BytesIO
from matplotlib.figure import Figure
from IPython.display import display
from pymongo import MongoClient
import numpy as np
from sklearn.datasets import load_iris
import pandas as pd
import matplotlib as plt
# import mysql.connector
from flask_debugtoolbar import DebugToolbarExtension
import os



app = Flask(__name__)


### MySQL connector and set up
# ratemybroncoDB = mysql.connector.connect(host="localhost", user="root", database="ratemybronco")
# mycursor = ratemybroncoDB.cursor()


### Landing page routing
@app.route("/")
def landing():
  return render_template("index.html")




### Search page routing and support
names = [] # To be replaced with database access
@app.route("/search", methods=["GET","POST"]) 
def search():
  if request.method == "GET":
    return render_template("search.html", professors=names)
  
  # check the if there is a number in the query then search the courses
  professor = request.form.get("professor")
  if not professor:
    return "output blank"

  names.append(professor)

  return redirect("/search")

@app.route("/professor/<professor>")
def professor_page (name, course):
  pass


### add raiting to the database with a SQL
@app.route("/review", methods=["POST", "GET"])
def add_rating():

  if request.method == "GET":
    return render_template("addRating.html")

  # Add server side checking
  # get all the data from the field
  ProfessorName = request.form.get("ProfessorName")
  courseName = request.form.get("courseName")
  Semester = request.form.get("Semester")
  Rating = request.form.get("Rating")
  Comment = request.form.get("Comment")
  
  # no need to call an html or redirect
  # compile it into a csv
  user_rating = f'"{ProfessorName}" , "{courseName}", "{Semester}", "{Rating}", "{Comment}"' # put in format with commas so we can add it as an sql_command
  sql_command  = f"INSERT INTO cards (ProfessorName, Class, Semester, Rating, Comment) VALUES ({user_rating});" # add a new row into cards table which we will need to create.

  # Execute this command, expecting no returns.
  mycursor.execute(sql_command)

### Thank you page or the submitted page
@app.route("/submitted", methods=["GET"])
def submitted():
  return "Thank You" 



### Return the grade disbursement for the displaying of the data
@app.route("/grade-disbursements")
def grades():
  # Loading irirs dataset
  data = load_iris()
  df = pd.DataFrame(data.data,columns = data.feature_names)

  # Generate the  matplot figure **without using pyplot**.
  fig = Figure()
  ax = fig.subplots()
  grades = ['A', 'B', 'C', 'D', 'F']
  disbursements = [10, 18, 8, 5, 3]
  ax.bar(grades, disbursements, color=['red', 'orange', 'yellow', 'green', 'blue'])
  ax.set_xlabel("Grade Received")
  ax.set_ylabel("Number of Students")
  ax.set_title("[Prof Name], [Course Number], [Semester], [Year] Grade Disbursement")
  # Save it to a temporary buffer.
  buf = BytesIO()
  fig.savefig(buf, format="png")
  # Embed the result in the html output.
  data = base64.b64encode(buf.getbuffer()).decode("ascii")

  return f"Grade Disbursement Page {display(df)} <img src='data:image/png;base64,{data}'/>"


### Run if main
if __name__ == "__main__":
  app.run(debug=True)
