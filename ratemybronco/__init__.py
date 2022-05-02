# from crypt import methods
from xml.etree.ElementTree import tostring
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
    instructorid = []

    print("searching for instructors") if instructor else print("searching for classes")
    if instructor:
      parsed_query = query.split() # assuming user inputs first and last name correctly
      fname = parsed_query[0]
      lname = parsed_query[1]

      # returns id of the instructor to look up the courses
      # assumes there is only one prof with this name
      mycursor.callproc("searchInstructor", args=(fname, lname))
      for result in mycursor.stored_results():
        res = result.fetchone()
        instructorid = res[0]

      # get courses only requires instructor id.
      mycursor.callproc("getCourses", args=(instructorid,))
      for result in mycursor.stored_results():
        for res in result:
          # name every card with the course ID
          cards[str(res[0])] = {'ProfessorName': query, 'CourseName': res[1], 'CourseDesc': res[2]}

      # Look up every id in the cards and append the overal rating to it
      for id in cards:
        mycursor.callproc("getOverallRating", args=(id, instructorid))
        for result in mycursor.stored_results():
          cards[id]['OverallRating'] = result.fetchall()[0][0]
    
    else:
      
      # note when user searches for a course name this the Course.idCourse will be the same for all the returned values
      # this is how the sql is set up!
      mycursor.callproc("returnAllClasses", args=(query,))
      for result in mycursor.stored_results():
        for i, res in enumerate(result):
          name = " ".join(res[0:2]) # joins the first and last name
          courseName = res[2]
          overallrating = None # res[3] later be replaced by this 
          cards[i] = {'ProfessorName': name, 'CourseName': courseName, 'OverallRating': overallrating}

      print(cards)
    
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
  legend = 'Grade Disbursements'
  labels = ['A', 'B', 'C', 'D', 'F']
  values = [10, 18, 8, 5, 3]
  return render_template('professorCard.html', values=values, labels=labels, legend=legend)


# Run if main
if __name__ == "__main__":
    app.run(debug=True)
