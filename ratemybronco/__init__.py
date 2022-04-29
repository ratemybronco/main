# from crypt import methods
from flask import Flask, redirect, render_template, request, url_for
import base64
from io import BytesIO
from matplotlib.figure import Figure
from IPython.display import display
import numpy as np
import pandas as pd
import matplotlib as plt
import mysql.connector
from flask_debugtoolbar import DebugToolbarExtension
import os


app = Flask(__name__)


## MySQL connector and set up
# ratemybroncoDB = mysql.connector.connect(option_files="ratemybronco/config.cfg", option_groups="database")
ratemybroncoDB = mysql.connector.connect(user='admin', password='ratemybronco', host='ratemybronco.cckwxul93z9y.us-west-1.rds.amazonaws.com', port=3306, database='ratemybronco')
mycursor = ratemybroncoDB.cursor()


# Landing page routing
@app.route("/")
def landing():
    return render_template("index.html")


# Search page routing and support
names = []  # To be replaced with database access


@app.route("/search", methods=["GET", "POST"])
def search():
  cards = {}
  query = request.args.get("query") # get attribute query, must be named "query"
  instructor = False

  if query:
    # if it has numbers it is a class otherwise prof's name
    instructor = not any(i.isdigit() for i in query)
    instructorid = 0
    courseid = []

    print("searching for instructors") if instructor else print("searching for classes")
    if instructor:
      parsed_query = query.split() # assuming user inputs first and last name correctly
      fname = parsed_query[0]
      lname = parsed_query[1]
    
      mycursor.callproc("searchInstructor", args=(fname, lname))
      for result in mycursor.stored_results():
        res = result.fetchone()
        instructorid = res[0]

      mycursor.callproc("getCourses", args=(instructorid,))
      for result in mycursor.stored_results():
        for res in result:
          courseid.append(res[0])

      print(courseid)
      for id in courseid:
        mycursor.callproc("getOverallRating", args=(id, instructorid))
        for result in mycursor.stored_results():
          print(result.fetchall())

    else:
      mycursor.execute("SELECT * FROM Course c WHERE c.CourseNumber=%s", (query,))

    return render_template("search.html", professors=names)
  
  return render_template("search.html", professors=names)



@app.route("/professor/<fname>-<lname>-<term>-<year>-<course>")
def professor_page(fname, lname, term, year, course):

    mycursor.callproc("getSectionID", (fname, lname, term, year, course))
    for results in mycursor.stored_results():
        sectionID = results.fetchone()[0]

    mycursor.callproc("getGrades", (sectionID,))
    for results in mycursor.stored_results():
        grades = results.fetchone()

    # Place holder template, with example values
    return render_template("professor_page.html")


# add raiting to the database with a SQL
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
    # put in format with commas so we can add it as an sql_command
    user_rating = f'"{ProfessorName}" , "{courseName}", "{Semester}", "{Rating}", "{Comment}"'
    # add a new row into cards table which we will need to create.
    sql_command = f"INSERT INTO cards (ProfessorName, Class, Semester, Rating, Comment) VALUES ({user_rating});"

    # Execute this command, expecting no returns.
    mycursor.execute(sql_command)

# Thank you page or the submitted page


@app.route("/submitted", methods=["GET"])
def submitted():
    return "Thank You"


# Return the grade disbursement for the displaying of the data
@app.route("/grade-disbursements")
def grades():
    # Loading irirs dataset
    data = load_iris()
    df = pd.DataFrame(data.data, columns=data.feature_names)

    # Generate the  matplot figure **without using pyplot**.
    fig = Figure()
    ax = fig.subplots()
    grades = ['A', 'B', 'C', 'D', 'F']
    disbursements = [10, 18, 8, 5, 3]
    ax.bar(grades, disbursements, color=[
           'red', 'orange', 'yellow', 'green', 'blue'])
    ax.set_xlabel("Grade Received")
    ax.set_ylabel("Number of Students")
    ax.set_title(
        "[Prof Name], [Course Number], [Semester], [Year] Grade Disbursement")
    # Save it to a temporary buffer.
    buf = BytesIO()
    fig.savefig(buf, format="png")
    # Embed the result in the html output.
    data = base64.b64encode(buf.getbuffer()).decode("ascii")

    return f"Grade Disbursement Page {display(df)} <img src='data:image/png;base64,{data}'/>"

# Professor card page routing


@app.route("/professorCard")
def card():
    return render_template("professorCard.html")


# Run if main
if __name__ == "__main__":
    app.run(debug=True)
