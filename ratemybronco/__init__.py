# from crypt import methods
from flask import Flask, render_template, request
from flaskext.mysql import MySQL


app = Flask(__name__)
app.config['MYSQL_DATABASE_HOST'] = 'mysql_host'
app.config['MYSQL_DATABASE_USER'] = 'mysql_user'
app.config['MYSQL_DATABASE_DB'] = 'mysql_db'
app.config['MYSQL_DATABASE_PASSWORD'] = 'mysql_pass'


# MySQL set up
mysql = MySQL()
mysql.init_app(app)


# Landing page routing
@app.route("/")
def landing():
    return render_template("index.html")


# Search page routing
@app.route("/search", methods=["GET", "POST"])
def search():
    mycursor = mysql.get_db().cursor()
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
            
            for i, res in enumerate(mycursor.fetchall()):
                if not res:
                    print("No results found")

                name, courseName, courseDesc, overallrating = " ".join(res[0:2]), res[2], res[3], None
                cards[i] = {'ProfessorName': name, 'CourseName': courseName, 'CourseDesc': courseDesc, 'OverallRating': overallrating}

        else:

            # note when user searches for a course name this the Course.idCourse will be the same for all the returned values
            # this is how the sql is set up!
            mycursor.callproc("returnAllClasses", args=(query,))
            for i, res in enumerate(mycursor.fetchall()):
                name, courseName, courseDesc, overallrating = " ".join(res[0:2]), res[2], res[3], None
                cards[i] = {
                    'ProfessorName': name, 'CourseName': courseName,'CourseDesc': courseDesc ,  'OverallRating': overallrating}

        return render_template("search.html", cards=cards)

    return render_template("search.html")


@app.route("/professor")
def professor_page():
    mycursor = mysql.get_db().cursor()
    name = request.args.get("name").split(" ")
    course = request.args.get("course")
    term = request.args.get("term")
    year = request.args.get("year")
    print(f"{name} {course} {term} {year}")

    if len(name) > 2:
        name[1] = f"{name[1]} {name[2]}"

    if year and term:
        print("Year and term submitted")
        mycursor.callproc("getSectionID", (name[0], name[1], term, year, course))
        sectionID = mycursor.fetchone()

        mycursor.callproc("getGrades", (sectionID,))
        grades = mycursor.fetchone()[0]

        # Place holder template, with example values
        return render_template("professor_page.html")

    mycursor.callproc("getGradesByCourse", (course, name[0], name[1]))
    grades = mycursor.fetchone()
    
    return render_template('professorCard.html',
                            professor=f"{name[0]} {name[1]}",
                            course=course,
                            values=grades, 
                            labels=['A', 'B', 'C', 'D', 'F'],
                            legend='Grade Disbursements',
                            rating='-.-')


# add raiting to the database with a SQL
@app.route("/review", methods=["POST", "GET"])
def add_rating():
    
    if request.method == "GET":
        print("Get request inside the add_rating method")
        return render_template("addRating.html")

    # Add server side checking
    # get all the data from the field
    ProfessorFName = request.form.get("firstName")
    ProfessorLName = request.form.get("lastName")
    courseName = request.form.get("courseName")
    Rating = request.form.get("selected_rating")
    Comment = request.form.get("comment")

    # no need to call an html or redirect
    # compile it into a csv
    # put in format with commas so we can add it as an sql_command
    user_rating = f'"{ProfessorFName}", "{ProfessorLName}", "{courseName}", "{Rating}", "{Comment}"'
    print(user_rating)
    # add a new row into cards table which we will need to create.
    # mycursor.callproc("addRating", (ProfessorFName, ProfessorLName, courseName, Rating, Comment))
    # ratemybroncoDB.commit()
    return render_template("thankYou.html")


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


# @app.errorhandler(mysql.connector.errors.InterfaceError)
# def database_connection_error():
#     print("Lost connection to MySQL Database")
#     global ratemybroncoDB
#     global mycursor
#     ratemybroncoDB = mysql.connector.connect(user='admin', password='ratemybronco',
#                                          host='ratemybronco.cckwxul93z9y.us-west-1.rds.amazonaws.com', port=3306, database='ratemybronco')
#     mycursor = ratemybroncoDB.cursor()
#     return redirect(request.referrer)


# Run if main
if __name__ == "__main__":
    app.run(debug=True)
