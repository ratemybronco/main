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


# MySQL connector and set up
# ratemybroncoDB = mysql.connector.connect(option_files="ratemybronco/config.cfg", option_groups="database")
ratemybroncoDB = mysql.connector.connect(user='admin', password='ratemybronco',
                                         host='ratemybronco.cckwxul93z9y.us-west-1.rds.amazonaws.com', port=3306, database='ratemybronco')
mycursor = ratemybroncoDB.cursor()


# Landing page routing
@app.route("/")
def landing():
    return render_template("index.html")


# Search page routing
@app.route("/search", methods=["GET", "POST"])
def search():
    cards = {}
    # get attribute query, must be named "query"
    query = request.args.get("query")
    instructor = False

    if query:
        # if it has numbers it is a class otherwise prof's name
        instructor = not any(i.isdigit() for i in query)

        print("searching for instructors") if instructor else print("searching for classes")
        if instructor:
            parsed_query = query.split()  
            fname, lname = "%" + parsed_query[0] + "%" , "%".join(parsed_query[1:]) if len(parsed_query)>1 else '%'
            
            print(fname, lname)

            # returns id of the instructor to look up the courses
            # assumes there is only one prof with this name
            mycursor.callproc("searchInstructor", args=(fname, lname))
            for result in mycursor.stored_results():
              for i, res in enumerate(result.fetchall()):
                  if not res:
                    print("No results found")

                  name, courseName, courseDesc, overallrating = " ".join(res[0:2]), res[2], res[3], None
                  cards[i] = {'ProfessorName': name, 'CourseName': courseName, 'CourseDesc': courseDesc, 'OverallRating': overallrating}

        else:

            # note when user searches for a course name this the Course.idCourse will be the same for all the returned values
            # this is how the sql is set up!
            mycursor.callproc("returnAllClasses", args=(query,))
            for result in mycursor.stored_results():
                for i, res in enumerate(result):
                    name, courseName, courseDesc, overallrating = " ".join(res[0:2]), res[2], res[3], None
                    cards[i] = {
                        'ProfessorName': name, 'CourseName': courseName,'CourseDesc': courseDesc ,  'OverallRating': overallrating}

        return render_template("search.html", cards=cards)

    return render_template("search.html")


@app.route("/professor")
def professor_page():
    name = request.args.get("name").split(" ")
    course = request.args.get("course")
    term = request.args.get("term")
    year = request.args.get("year")
    print(f"{name} {course} {term} {year}")

    if year and term:
        print("Year and term submitted")
        mycursor.callproc("getSectionID", (name[0], name[1], term, year, course))
        for results in mycursor.stored_results():
            sectionID = results.fetchone()

        mycursor.callproc("getGrades", (sectionID,))
        for results in mycursor.stored_results():
            grades = results.fetchone()[0]

        # Place holder template, with example values
        return render_template("professor_page.html")

    mycursor.callproc("getGradesByCourse", (course, name[0], name[1]))
    for results in mycursor.stored_results():
        grades = results.fetchone()
    
    return render_template('professorCard.html',
                            professor=name[0]+name[1],
                            course=course,
                            values=grades, 
                            labels=['A', 'B', 'C', 'D', 'F'],
                            legend='Grade Disbursements',
                            rating='-.-')


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
    ratemybroncoDB.commit()

    redirect(url_for('submitted'))


# Thank you page or the submitted page
@app.route("/submitted", methods=["GET"])
def submitted():
    return render_template("thankYou.html")


# Professor card page routing
@app.route("/professorCard")
def card():
    legend = 'Grade Disbursements'
    labels = ['A', 'B', 'C', 'D', 'F']
    values = [10, 18, 8, 5, 3]
    return render_template('professorCard.html', values=values, labels=labels, legend=legend)


@app.route("/aboutUs")
def aboutus():
    return render_template("aboutUs.html")


# Run if main
if __name__ == "__main__":
    app.run(debug=True)
