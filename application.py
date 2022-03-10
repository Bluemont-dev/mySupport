from calendar import c
import imghdr
from logging.config import dictConfig
import os
import csv
import copy
import bleach
import psycopg2
import psycopg2.extras
from psycopg2 import sql, errors
from psycopg2.extensions import AsIs
import urllib.parse
from urllib.parse import urlparse
from urllib.request import urlopen
from bs4 import BeautifulSoup
from errors import errorView, flashStyling
from helpers import email_required, login_required
from datetime import datetime, date
from operator import itemgetter
# from cs50 import SQL
from flask import Flask, abort, flash, redirect, render_template, request, session, url_for, jsonify
from flask_session import Session
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from dotenv import load_dotenv
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

# load the environment variables
load_dotenv()

# Configure application
app = Flask(__name__)

# Configure Mail
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

#enable token generation for email confirmation and password reset
s = URLSafeTimedSerializer(os.getenv('TOKEN_SECRET'))

# manage file uploads by users
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.jpeg', '.png', '.gif']
app.config['UPLOAD_PATH'] = 'static/avatars'

# check image file header data to make sure it's an image file; uses imghdr library
def validate_image(stream):
    header = stream.read(512)
    stream.seek(0)
    format = imghdr.what(None, header)
    if not format:
        return None
    return '.' + (format if format != 'jpeg' else 'jpg')

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# # Configure CS50 Library to use SQLite database
# db = SQL("sqlite:///mySupport.db")

# # Enable foreign key constraints in SQLite
# db.execute ("PRAGMA foreign_keys=ON")

# get db settings from env
db = {}
db['host'] = os.getenv('DATABASE_HOST')
db['database'] = os.getenv('DATABASE')
db['user'] = os.getenv('DATABASE_USER')
db['password'] = os.getenv('DATABASE_PASSWORD')

# connect to the db
print('Connecting to the PostgreSQL database...')
conn = psycopg2.connect(
    host=db['host'],
    database=db['database'],
    user=db['user'],
    password=db['password'])

# set default so that every query is committed unless a transaction block is explicitly used
conn.autocommit = True

# # create a cursor
# cur = conn.cursor()
# # close a cursor
# cur.close()

# or do them both in one function
# with conn.cursor() as curs:
#     curs.execute(SQL)
# the cursor is now closed as a result of exiting the block


# ===== BEGIN ROUTES ========

@app.route("/", methods = ["GET"])
@email_required
def index():
    # call a function that checks for authentication and sends correct object to the template
    userDict = buildUserDict()
    retrieveLimit = 50
    allDiscussionsList = []
    commentCount = 0
    # # retrieve  recent discussions from db
    # allDiscussionIDs = db.execute("""
    # SELECT id FROM discussions
    # ORDER BY dateCreated DESC
    # LIMIT ?;
    # """, retrieveLimit)
    dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    dict_cur.execute("""SELECT id FROM discussions ORDER BY date_created DESC LIMIT (%s)""",[retrieveLimit])
    allDiscussionIDs = [dict(row) for row in dict_cur.fetchall()]
    # loop thru discussions and prep each one for display
    for item in allDiscussionIDs:
        commentCount = 0
        discussionRow = getDiscussionRowsForDisplay(item['id'])
        # count number of comments for each, add it to the dict
        # commentCount = db.execute("SELECT COUNT(*) FROM comments WHERE discussionID = ?", item['id'])
        dict_cur.execute("""SELECT COUNT(*) FROM comments WHERE discussion_id = (%s)""",[item['id']])
        commentCount = [dict(row) for row in dict_cur.fetchall()]
        discussionRow[0]['commentCount'] = commentCount[0]['count']
        # get textContent from HTML for each discussion; add it to the dict
        textContent = getTextContentFromHTML(discussionRow[0]['text'])
        discussionRow[0]['textContent'] = textContent
        # check for images in the HTML; grab code for the first one
        imageTagCode = getFirstImageFromHTML(discussionRow[0]['text'])
        discussionRow[0]['imageTagCode'] = imageTagCode
        allDiscussionsList.append(discussionRow[0])
    allArticlesList = []
    commentCount = 0
    # retrieve most recent articles from db
    # allArticleIDs = db.execute("""
    # SELECT id FROM articles
    # ORDER BY dateCreated DESC
    # LIMIT ?;
    # """, retrieveLimit)
    dict_cur.execute("""SELECT id FROM articles
    ORDER BY date_created DESC
    LIMIT (%s)""",[retrieveLimit])
    allArticleIDs = [dict(row) for row in dict_cur.fetchall()]
    # print(f"allArticleIDs: {allArticleIDs}")
    # loop thru articles and prep each one for display
    for item in allArticleIDs:
        commentCount = 0
        articleRow = getArticleRowsForDisplay(item['id'])
        # count number of comments for each, add it to the dict
        # commentCount = db.execute("SELECT COUNT(*) FROM comments WHERE articleID = ?", item['id'])
        dict_cur.execute("""SELECT COUNT(*) FROM comments WHERE article_id = (%s)""",[item['id']])
        commentCount = [dict(row) for row in dict_cur.fetchall()]
        # print(f"commentCount: {commentCount}")
        articleRow[0]['commentCount'] = commentCount[0]['count']
        articleRow[0]['publishedDateTimeString'] = articleRow[0]['publishedDateTimeString'][:articleRow[0]['publishedDateTimeString'].find('-')-1]
        articleRow[0]['website'] = urlparse(articleRow[0]['url']).netloc
        allArticlesList.append(articleRow[0])
    # peopleRows = db.execute("SELECT id, firstName, lastName, username, displayNameOption, dateJoined, city, county, state, profileImage FROM users ORDER BY dateJoined DESC LIMIT ?", retrieveLimit)
    dict_cur.execute("""SELECT id, first_name, last_name, username, display_name_option, date_joined, city, county, state, profile_image FROM users ORDER BY date_joined DESC LIMIT (%s)""",[retrieveLimit])
    peopleRows = [dict(row) for row in dict_cur.fetchall()]
    dict_cur.close()
    # print(peopleRows)
    for row in peopleRows:
        personDisplayName = buildDisplayName(row)
        row['displayName'] = personDisplayName
        row['joinedDateString'] = buildDateTimeString(row['date_joined'])
        # truncate the dateJoined because the time is irrelevant
        row['joinedDateString'] = row['joinedDateString'][:row['joinedDateString'].find('-')-1]
    return render_template ("index.html", userDict = userDict, allDiscussionsList = allDiscussionsList, allArticlesList = allArticlesList, peopleRows = peopleRows)

@app.route("/article/<articleID>")
def article(articleID):
    # make sure article exists
    dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    dict_cur.execute("""SELECT * FROM articles WHERE id = %s""", [int(articleID)])
    articleRowPresence = [dict(row) for row in dict_cur.fetchall()]
    if not articleRowPresence:
        flash("We cannot find the article you're looking for.", flashStyling("warning"))
        return redirect("/articles")
    userDict = buildUserDict()
    articleRows = getArticleRowsForDisplay(articleID)
    # truncate the datePublished because the time of 00:00:00 was just a data placeholder
    articleRows[0]['publishedDateTimeString'] = articleRows[0]['publishedDateTimeString'][:articleRows[0]['publishedDateTimeString'].find('-')-1]
    articleRows[0]['website'] = urlparse(articleRows[0]['url']).netloc
    # print(f"articleRows[0] = {articleRows[0]}")
    commentRows = getArticleCommentRowsForDisplay(articleID)
    commentEditMode = "create"
    return render_template("articleView.html", userDict = userDict, articleRow = articleRows[0], commentRows = commentRows, commentEditMode = commentEditMode)
    # return "Your article would show up here"

@app.route("/article/comment/<articleID>", methods = ["POST"])
@login_required
@email_required
def articleComment(articleID):
    # get text content from form
    commentText = request.form.get('commentTextContent')
    dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    dict_cur.execute("""BEGIN""")
    try:
        # create new comment
        dict_cur.execute("""INSERT INTO comments (sender_id, text, article_id) VALUES (%s,%s,%s) RETURNING id""",[int(session.get('id')), commentText, int(articleID)])
        newCommentID = [dict(row) for row in dict_cur.fetchall()]
        newCommentID = newCommentID[0]['id']
    except Exception as error:
        print ("Oops! An exception has occurred:", error)
        print ("Exception TYPE:", type(error))
        dict_cur.execute("""ROLLBACK""")
        abort(500)
    else:
        dict_cur.execute("""COMMIT""")
    dict_cur.close()
    # redirect to that same article view, jumping to the anchor of the new comment
    return redirect("/article/" + articleID + "#commentItemTextDiv" + str(newCommentID))

@app.route("/article/<articleID>/comment/<commentID>/edit", methods = ["GET", "POST"])
@login_required
@email_required
def articleCommentEdit(articleID, commentID):
    # in both GET and POST, make sure the items both exist and the logged-in user is the owner of the comment being edited
    # make sure article exists
    dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    dict_cur.execute("""SELECT * FROM articles WHERE id = %s""", [int(articleID)])
    articleRowPresence = [dict(row) for row in dict_cur.fetchall()]
    if len(articleRowPresence) == 0:
        flash("We cannot find the article you're looking for.", flashStyling("warning"))
        return redirect("/articles")
    # make sure comment exists AND is associated with that article
    dict_cur.execute("""SELECT * FROM comments WHERE id = %s""", [int(commentID)])
    commentRowPresence = [dict(row) for row in dict_cur.fetchall()]
    if not (len(commentRowPresence)>0 and commentRowPresence[0]['article_id'] == articleRowPresence[0]['id']):
        flash("We cannot find the comment you're looking for.", flashStyling("warning"))
        return redirect("/")
    # make sure the comment to be edited belongs to the logged-in user
    dict_cur.execute("""SELECT sender_id FROM comments WHERE id = %s""", [int(commentID)])
    senderIDList = [dict(row) for row in dict_cur.fetchall()]
    if senderIDList[0]['sender_id'] != int(session.get('id')):
        flash("You are not authorized to edit this comment.", flashStyling("warning"))
        return redirect("/article/" + articleID)
    if request.method == "GET":
        userDict = buildUserDict()
        articleRows = getArticleRowsForDisplay(articleID)
        # truncate the datePublished because the time of 00:00:00 was just a data placeholder
        articleRows[0]['publishedDateTimeString'] = articleRows[0]['publishedDateTimeString'][:articleRows[0]['publishedDateTimeString'].find('-')-1]
        articleRows[0]['website'] = urlparse(articleRows[0]['url']).netloc
        # print(f"articleRows[0] = {articleRows[0]}")
        commentRows = getArticleCommentRowsForDisplay(articleID)
        commentEditMode = "edit"
        commentEditID = commentID
        return render_template("articleView.html", userDict = userDict, articleRow = articleRows[0], commentRows = commentRows, commentEditMode = commentEditMode, commentEditID = commentEditID)
    else:
        # we have a post request
        textContent = request.form.get('commentEditTextContent')

        dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        dict_cur.execute("""BEGIN""")
        try:
            # update the comment
            dict_cur.execute("""UPDATE comments SET text = %s WHERE id = %s""", [textContent, int(commentID)])
        except Exception as error:
            print ("Oops! An exception has occurred:", error)
            print ("Exception TYPE:", type(error))
            dict_cur.execute("""ROLLBACK""")
            abort(500)
        else:
            dict_cur.execute("""COMMIT""")
        dict_cur.close()
        # redirect to that same article view, jumping to the anchor of the updated comment
        return redirect("/article/" + articleID + "#commentItemTextDiv" + str(commentID))

@app.route("/article/<articleID>/comment/<commentID>/delete", methods = ["GET"])
@login_required
@email_required
def articleCommentDelete(articleID, commentID):
    # make sure the items both exist and the logged-in user is the owner of the comment being deleted
    # make sure article exists
    dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    dict_cur.execute("""SELECT * FROM articles WHERE id = %s""", [int(articleID)])
    articleRowPresence = [dict(row) for row in dict_cur.fetchall()]
    if len(articleRowPresence) == 0:
        flash("We cannot find the article you're looking for.", flashStyling("warning"))
        return redirect("/articles")
    # make sure comment exists AND is associated with that article
    dict_cur.execute("""SELECT * FROM comments WHERE id = %s""", [int(commentID)])
    commentRowPresence = [dict(row) for row in dict_cur.fetchall()]
    if not (len(commentRowPresence)>0 and commentRowPresence[0]['article_id'] == articleRowPresence[0]['id']):
        flash("We cannot find the comment you're looking for.", flashStyling("warning"))
        return redirect("/")
    # make sure the comment to be edited belongs to the logged-in user
    dict_cur.execute("""SELECT sender_id FROM comments WHERE id = %s""", [int(commentID)])
    senderIDList = [dict(row) for row in dict_cur.fetchall()]
    if senderIDList[0]['sender_id'] != int(session.get('id')):
        flash("You are not authorized to delete this comment.", flashStyling("warning"))
        return redirect("/article/" + articleID)
    dict_cur.execute("""BEGIN""")
    try:
        # delete the comment
        dict_cur.execute("""DELETE FROM comments WHERE id = %s""", [int(commentID)])
    except Exception as error:
        print ("Oops! An exception has occurred:", error)
        print ("Exception TYPE:", type(error))
        dict_cur.execute("""ROLLBACK""")
        abort(500)
    else:
        dict_cur.execute("""COMMIT""")
    dict_cur.close()
    return redirect("/article/" + articleID)

@app.route("/article/edit/<articleID>", methods = ["GET","POST"])
@login_required
@email_required
def articleEdit(articleID):
    if request.method == "GET":
        userDict = buildUserDict()
        userRows = getUserRows(session.get("id"))
        selectsDict = dbSimpleDictBuilder('relationships+id+ASC','genders+id+ASC','ages+id+ASC','challenges+challenge+ASC')
        # make sure the item exists
        dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        dict_cur.execute("""SELECT * FROM articles WHERE id = %s""", [int(articleID)])
        articleRowPresence = len(dict_cur.fetchall())
        if articleRowPresence == 0:
            flash("We cannot find the article you're looking for.", flashStyling("warning"))
            return redirect("/articles")
        # make sure the item to be edited belongs to the logged-in user
        dict_cur.execute("""SELECT sender_id FROM articles WHERE id = %s""", [int(articleID)])
        senderIDList = [dict(row) for row in dict_cur.fetchall()]
        dict_cur.close()
        if senderIDList[0]['sender_id'] != int(session.get('id')):
            flash("You are not authorized to edit this content.", flashStyling("warning"))
            return redirect("/article/" + articleID)
        articleRows = getArticleRowsForDisplay(articleID)
        articleRows[0]['date_published'] = str(articleRows[0]['date_published'])[:10]
        editMode = "edit"
        print(articleRows[0])
        return render_template("articleThread.html", userDict = userDict, selectsDict = selectsDict, articleRow = articleRows[0], editMode = editMode)
    else:
        # post request
        newChallengeList = request.form.getlist('challenge')
        newAgeList = request.form.getlist('age')
        newGenderList = request.form.getlist('gender')
        # capture the content of other form values
        title = request.form.get('title')
        description = request.form.get('description')
        url = request.form.get('articleURL')
        datePublished = request.form.get('date_published') + " 00:00:00"
        if request.form.get('useOGImage') == 'yes':
            ogImage = request.form.get('ogImagePath')
        else:
            ogImage = None
        # if URL is changed from the value stored in db, we need to prompt the user to choose between creating a new article (deleting the current one) or just cancel
        dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        dict_cur.execute("""SELECT url FROM articles WHERE id = %s""", [int(articleID)])
        existingURLList = dict_cur.fetchall()
        existingURL = existingURLList[0]['url']
        # print(f"Existing URL is: {existingURL}")
        # print(f"submitted url is: {url}")
        if url != existingURL:
            flash("You cannot change the URL of an existing article, but you can create a new article with the new URL.", flashStyling("warning"))
            return redirect("/article/edit/" + articleID)
        # begin transaction
        # write new rows to ArticleToChallenge, etc.
        passedDict = {}
        passedDict['title'] = title
        passedDict['description'] = description
        passedDict['url'] = url
        passedDict['date_published'] = datePublished
        passedDict['og_image'] = ogImage
        # print(f"Passed dictionary is {passedDict}")
        keysList = list(passedDict.keys())
        keysString = ",".join(keysList)
        valuesList = list(passedDict.values())
        valuesString = ""
        for i in range(len(valuesList)):
            if type(valuesList[i]) == str:
                valuesString += "'" + valuesList[i] + "'"
            else:
                valuesString += str(valuesList[i])
            if i < len(valuesList)-1:
                valuesString += ","
        # print(f"keysString is {keysString} and valuesString is {valuesString}")
        if len(passedDict.keys()) > 1:
            update_str = sql.SQL("UPDATE articles SET (%s) = (%s) WHERE id = %s")
        else:
            update_str = sql.SQL("UPDATE articles SET %s = %s WHERE id = %s")
        dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        dict_cur.execute("""BEGIN""")
        try:
            # update article row
            dict_cur.execute(update_str,[AsIs(keysString),AsIs(valuesString),int(articleID)])
            # remove all challenges, ages, genders from their article join tables
            dict_cur.execute("""DELETE FROM article_challenge WHERE article_id = %s""",[int(articleID)])
            dict_cur.execute("""DELETE FROM article_age WHERE article_id = %s""",[int(articleID)])
            dict_cur.execute("""DELETE FROM article_gender WHERE article_id = %s""",[int(articleID)])
            # insert new challenges, ages, genders into their article join tables
            if len(newChallengeList) > 0:
                for challenge in newChallengeList:
                    dict_cur.execute("""INSERT INTO article_challenge (article_id, challenge_id) VALUES (%s,%s)""", [int(articleID), challenge])
            if len(newAgeList) > 0:
                for age in newAgeList:
                    dict_cur.execute("""INSERT INTO article_age (article_id, age_id) VALUES (%s,%s)""", [int(articleID), age])
            if len(newGenderList) > 0:
                for gender in newGenderList:
                    dict_cur.execute("""INSERT INTO article_gender (article_id, gender_id) VALUES (%s,%s)""", [int(articleID), gender])
        except Exception as error:
            print ("Oops! An exception has occurred:", error)
            print ("Exception TYPE:", type(error))
            dict_cur.execute("""ROLLBACK""")
            abort(500)
        else:
            dict_cur.execute("""COMMIT""")
        dict_cur.close()
        # redirect the user to the view version of this article that was just edited
        return redirect("/article/" + articleID)

@app.route("/article/getArticleDetails/", methods = ["POST"])
@login_required
@email_required
def getArticleDetails():
    userDict = buildUserDict()
    userRows = getUserRows(session.get("id"))
    selectsDict = dbSimpleDictBuilder('relationships+id+ASC','genders+id+ASC','ages+id+ASC','challenges+challenge+ASC')
    editMode = "edit"
    # create empty list for articleRow so the jinja template logic will be happy
    url = request.form.get('url')
    articleRow = [{
        'id':"",
        'title':None,
        'url':url,
        'og_image':None,
        'description':None,
        'date_published':None,
        'challenge_ids':"",
        'age_ids':"",
        'gender_ids':""
    }]
    publishedMetaItems = []
    publishedTagString = ""
    publisheTagAttributesList = []
    datePublishedTestString = ""
    try:
        request_page = urlopen(url)
    except:
        # print(f"despite error, articleRow[0] = {articleRow[0]}")
        return render_template("articleThread.html", userDict = userDict, userRows = userRows, selectsDict = selectsDict, articleRow = articleRow[0], editMode = editMode)
    page_html = request_page.read()
    request_page.close()
    soup = BeautifulSoup(page_html, 'html.parser')
    articleRow[0]['url'] = url
    articleRow[0]['title'] = soup.h1.get_text()
    if soup.find("meta", property="og:image"):
        articleRow[0]['og_image'] = soup.find("meta", property="og:image")['content']
    if soup.find("meta", property="og:url"):
        articleRow[0]['url'] = soup.find("meta", property="og:url")['content']
    if soup.find("meta", property="og:description"):
        articleRow[0]['description'] = soup.find("meta", property="og:description")['content']
    elif soup.find("meta", property="description"):
        articleRow[0]['description'] = soup.find("meta", property="description")['content']
    if articleRow[0]['description'] == articleRow[0]['title']:
        articleRow[0]['description'] = None
        # this prevents a redundant description from being stored in db and displayed
    # allMetaItems = soup.find_all("meta")
    if soup.select("meta[property*=ublished]"):
        publishedMetaItems = soup.select("meta[property*=ublished]")
    if len(publishedMetaItems) == 1:
        publishedTagString = str(publishedMetaItems[0])
        publishedTagAttributesList = publishedTagString.split(" ")
        for item in publishedTagAttributesList:
            if item [:8] == "content=":
                datePublishedTestString = item [8:]
                datePublishedTestString = datePublishedTestString.strip('\"\'')
                # print(f"dataPublishedTestString: {datePublishedTestString}")
    if checkDateFormat (datePublishedTestString):
        articleRow[0]['date_published'] = datePublishedTestString
    else:
        articleRow[0]['date_published'] = None
    # print(f"articleRow[0] = {articleRow[0]}")
    return render_template("articleThread.html", userDict = userDict, userRows = userRows, selectsDict = selectsDict, articleRow = articleRow[0], editMode = editMode)

@app.route("/article/thread/", methods = ["GET","POST"])
@login_required
@email_required
def articleThreadBlank():
    if request.method == "GET":
        userDict = buildUserDict()
        userRows = getUserRows(session.get("id"))
        selectsDict = dbSimpleDictBuilder('relationships+id+ASC','genders+id+ASC','ages+id+ASC','challenges+challenge+ASC')
        editMode = "create"
        # create empty list for articleRow so the jinja template logic will be happy
        articleRow = [{
            'id':"",
            'title':"",
            'url':"",
            'og_image':"",
            'description':"",
            'date_published':"",
            'challenge_ids':"",
            'age_ids':"",
            'gender_ids':""
        }]
        return render_template("articleThread.html", userDict = userDict, userRows = userRows, selectsDict = selectsDict, articleRow = articleRow, editMode = editMode)
    else:
        # method was POST
        myDict = dict(request.form)
        # print(f"myDict: {myDict}")
        # note that request.form returns an "ImmutableMultidict", so the dict() method turns it into a regular dict
        # to write a new article, take the following steps
        # get the selections from each of the selects and condense them into lists/arrays
        passedDict = {}
        newChallengeList = request.form.getlist('challenge')
        newAgeList = request.form.getlist('age')
        newGenderList = request.form.getlist('gender')
        # capture the content of other form values
        passedDict['title'] = request.form.get('title')
        passedDict['description'] = request.form.get('description')
        passedDict['url'] = request.form.get('articleURL')
        passedDict['date_published'] = request.form.get('date_published') + " 00:00:00"
        if request.form.get('useOGImage') == 'yes':
            passedDict['og_image'] = request.form.get('ogImagePath')
        else:
            passedDict['og_image'] = None
        passedDict['sender_id'] = session.get('id')
        # print(f"Passed dictionary is {passedDict}")
        insert_flds = [fld_name for fld_name in passedDict.keys()]
        # print(f"Insert fields: {insert_flds}")
        insert_str = sql.SQL("INSERT INTO articles ({}) VALUES ({}) RETURNING id").format(
        sql.SQL(",").join(map(sql.Identifier, insert_flds)),
        sql.SQL(",").join(map(sql.Placeholder, insert_flds)))
        # print(f"Insert string is: {insert_str}")
        # begin transaction
        dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        dict_cur.execute("""BEGIN""")
        try:
            # create new article and capture its id
            dict_cur.execute(insert_str,passedDict)
            newID = [dict(row) for row in dict_cur.fetchall()]
            newID = newID[0]['id']
            # populate the other tables as needed (challenges, ages, genders)
            if len(newChallengeList) > 0:
                for challenge in newChallengeList:
                    dict_cur.execute("""INSERT INTO article_challenge (article_id, challenge_id) VALUES (%s,%s)""", [newID, challenge])
            if len(newAgeList) > 0:
                for age in newAgeList:
                    dict_cur.execute("""INSERT INTO article_age (article_id, age_id) VALUES (%s,%s)""", [newID, age])
            if len(newGenderList) > 0:
                for gender in newGenderList:
                    dict_cur.execute("""INSERT INTO article_gender (article_id, gender_id) VALUES (%s,%s)""", [newID, gender])
        except Exception as error:
            print ("Oops! An exception has occurred:", error)
            print ("Exception TYPE:", type(error))
            dict_cur.execute("""ROLLBACK""")
            abort(500)
        else:
            dict_cur.execute("""COMMIT""")
        dict_cur.close()
        # redirect the user to the view version of this discussion that was just created
        return redirect("/article/" + str(newID))

@app.route("/article/delete/<articleID>", methods = ["GET"])
@login_required
@email_required
def articleDelete(articleID):
    # make sure article exists
    dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    dict_cur.execute("""SELECT * FROM articles WHERE id = %s""", [int(articleID)])
    articleRowPresence = [dict(row) for row in dict_cur.fetchall()]
    if len(articleRowPresence) == 0:
        flash("We cannot find the article you're looking for.", flashStyling("warning"))
        return redirect("/articles")
    # make sure the article to be deleted belongs to the logged-in user
    dict_cur.execute("""SELECT sender_id FROM articles WHERE id = %s""", [int(articleID)])
    senderIDList = [dict(row) for row in dict_cur.fetchall()]
    if senderIDList[0]['sender_id'] != int(session.get('id')):
        flash("You are not authorized to delete this article.", flashStyling("warning"))
        return redirect("/article/" + articleID)
    dict_cur.execute("""BEGIN""")
    try:
        # delete the article
        dict_cur.execute("""DELETE FROM articles WHERE id = %s""", [int(articleID)])
    except Exception as error:
        print ("Oops! An exception has occurred:", error)
        print ("Exception TYPE:", type(error))
        dict_cur.execute("""ROLLBACK""")
        abort(500)
    else:
        dict_cur.execute("""COMMIT""")
    dict_cur.close()
    return redirect("/articles")

@app.route("/articles", methods = ["GET"])
def articles():
    userDict = buildUserDict()
    retrieveLimit = 50
    allArticlesList = []
    commentCount = 0
    # retrieve 50 most recent articles from db
    dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    dict_cur.execute("""
    SELECT id FROM articles
    ORDER BY date_created DESC
    LIMIT %s;
    """, [retrieveLimit])
    allArticleIDs = [dict(row) for row in dict_cur.fetchall()]
    # print(allArticleIDs)
    # loop thru articles and prep each one for display
    for item in allArticleIDs:
        commentCount = 0
        articleRow = getArticleRowsForDisplay(item['id'])
        # count number of comments for each, add it to the dict
        dict_cur.execute("SELECT COUNT(*) FROM comments WHERE article_id = %s", [item['id']])
        commentCount = [dict(row) for row in dict_cur.fetchall()]
        articleRow[0]['commentCount'] = commentCount[0]['count']
        articleRow[0]['publishedDateTimeString'] = articleRow[0]['publishedDateTimeString'][:articleRow[0]['publishedDateTimeString'].find('-')-1]
        articleRow[0]['website'] = urlparse(articleRow[0]['url']).netloc
        allArticlesList.append(articleRow[0])
    # print(allArticlesList)
    return render_template ("articlesView.html", userDict = userDict, allArticlesList = allArticlesList)
    # return("Here we would list 50 articles")

@app.route("/discussion/<discussionID>")
def discussion(discussionID):
    # make sure discussion exists
    dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    dict_cur.execute("""SELECT * FROM discussions WHERE id = %s""", [int(discussionID)])
    discussionRowPresence = [dict(row) for row in dict_cur.fetchall()]
    if len(discussionRowPresence) == 0:
        flash("We cannot find the discussion you're looking for.", flashStyling("warning"))
        return redirect("/discussions")
    userDict = buildUserDict()
    discussionRows = getDiscussionRowsForDisplay(discussionID)
    commentRows = getDiscussionCommentRowsForDisplay(discussionID)
    commentEditMode = "create"
    return render_template("discussionView.html", userDict = userDict, discussionRow = discussionRows[0], commentRows = commentRows, commentEditMode = commentEditMode)

@app.route("/contact", methods = ["GET","POST"])
def contact():
    if request.method == "GET":
        userDict = buildUserDict()
        return render_template("contact.html", userDict = userDict)
    else:
        # we have a post request
        mailDict = dict(request.form)
        # print(mailDict)
        msg = Message("MySupport contact form submission", sender=("MySupport", "info@bluemontcommunications.com"), recipients=["info@bluemontcommunications.com"])
        msg.body = "Name: " + mailDict['name'] + "\nEmail: " + mailDict['email'] + "\nMessage: " + mailDict['message']
        mail.send(msg)
        return redirect ("/contact2")

@app.route("/contact2", methods = ["GET"])
def contact2():
    userDict = buildUserDict()
    return render_template("contact2.html", userDict = userDict)

@app.route("/discussion/comment/<discussionID>", methods = ["POST"])
@login_required
@email_required
def discussionComment(discussionID):
    # get text content from form
    commentText = request.form.get('commentTextContent')
    dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    dict_cur.execute("""BEGIN""")
    try:
        # create new comment
        dict_cur.execute("""INSERT INTO comments (sender_id, text, discussion_id) VALUES (%s,%s,%s) RETURNING id""",[int(session.get('id')), commentText, int(discussionID)])
        newCommentID = [dict(row) for row in dict_cur.fetchall()]
        newCommentID = newCommentID[0]['id']
    except Exception as error:
        print ("Oops! An exception has occurred:", error)
        print ("Exception TYPE:", type(error))
        dict_cur.execute("""ROLLBACK""")
        abort(500)
    else:
        dict_cur.execute("""COMMIT""")
    dict_cur.close()
    # redirect to that same discussion view, jumping to the anchor of the new comment
    return redirect("/discussion/" + discussionID + "#commentItemTextDiv" + str(newCommentID))

@app.route("/discussion/<discussionID>/comment/<commentID>/edit", methods = ["GET", "POST"])
@login_required
@email_required
def discussionCommentEdit(discussionID, commentID):
    # in both GET and POST, make sure the items both exist and the logged-in user is the owner of the comment being edited
    # make sure discussion exists
    dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    dict_cur.execute("""SELECT * FROM discussions WHERE id = %s""", [int(discussionID)])
    discussionRowPresence = [dict(row) for row in dict_cur.fetchall()]
    if len(discussionRowPresence) == 0:
        flash("We cannot find the discussion you're looking for.", flashStyling("warning"))
        return redirect("/")
    # make sure comment exists AND is associated with that discussion
    dict_cur.execute("""SELECT * FROM comments WHERE id = %s""", [int(commentID)])
    commentRowPresence = [dict(row) for row in dict_cur.fetchall()]
    if not (len(commentRowPresence) > 0 and commentRowPresence[0]['discussion_id'] == discussionRowPresence[0]['id']):
        flash("We cannot find the comment you're looking for.", flashStyling("warning"))
        return redirect("/")
    # make sure the comment to be edited belongs to the logged-in user
    dict_cur.execute("""SELECT sender_id FROM comments WHERE id = %s""", [int(commentID)])
    senderIDList = [dict(row) for row in dict_cur.fetchall()]
    if senderIDList[0]['sender_id'] != int(session.get('id')):
        flash("You are not authorized to edit this comment.", flashStyling("warning"))
        return redirect("/discussion/" + discussionID)
    if request.method == "GET":
        userDict = buildUserDict()
        discussionRows = getDiscussionRowsForDisplay(discussionID)
        commentRows = getDiscussionCommentRowsForDisplay(discussionID)
        commentEditMode = "edit"
        commentEditID = commentID
        dict_cur.close()
        return render_template("discussionView.html", userDict = userDict, discussionRow = discussionRows[0], commentRows = commentRows, commentEditMode = commentEditMode, commentEditID = commentEditID)
    else:
        # we have a post request
        textContent = request.form.get('commentEditTextContent')
        dict_cur.execute("""BEGIN""")
        try:
            # update that row in comments table
            dict_cur.execute("""UPDATE comments SET text = %s WHERE id = %s""", [textContent, int(commentID)])
        except Exception as error:
            print ("Oops! An exception has occurred:", error)
            print ("Exception TYPE:", type(error))
            dict_cur.execute("""ROLLBACK""")
            abort(500)
        else:
            dict_cur.execute("""COMMIT""")
            dict_cur.close()
        # redirect to that same discussion view, jumping to the anchor of the updated comment
        return redirect("/discussion/" + discussionID + "#commentItemTextDiv" + str(commentID))

@app.route("/discussion/<discussionID>/comment/<commentID>/delete", methods = ["GET"])
@login_required
@email_required
def discussionCommentDelete(discussionID, commentID):
    # make sure the items both exist and the logged-in user is the owner of the comment being deleted

    # make sure discussion exists
    dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    dict_cur.execute("""SELECT * FROM discussions WHERE id = %s""", [int(discussionID)])
    discussionRowPresence = [dict(row) for row in dict_cur.fetchall()]
    if len(discussionRowPresence) == 0:
        flash("We cannot find the discussion you're looking for.", flashStyling("warning"))
        return redirect("/")
    # make sure comment exists AND is associated with that discussion
    dict_cur.execute("""SELECT * FROM comments WHERE id = %s""", [int(commentID)])
    commentRowPresence = [dict(row) for row in dict_cur.fetchall()]
    if not (len(commentRowPresence) > 0 and commentRowPresence[0]['discussion_id'] == discussionRowPresence[0]['id']):
        flash("We cannot find the comment you're looking for.", flashStyling("warning"))
        return redirect("/")
    # make sure the comment to be edited belongs to the logged-in user
    dict_cur.execute("""SELECT sender_id FROM comments WHERE id = %s""", [int(commentID)])
    senderIDList = [dict(row) for row in dict_cur.fetchall()]
    if senderIDList[0]['sender_id'] != int(session.get('id')):
        flash("You are not authorized to delete this comment.", flashStyling("warning"))
        return redirect("/discussion/" + discussionID)
    dict_cur.execute("""BEGIN""")
    try:
        dict_cur.execute("""DELETE FROM comments WHERE id = %s""", [int(commentID)])
    except Exception as error:
        print ("Oops! An exception has occurred:", error)
        print ("Exception TYPE:", type(error))
        dict_cur.execute("""ROLLBACK""")
        abort(500)
    else:
        dict_cur.execute("""COMMIT""")
    dict_cur.close()
    return redirect("/discussion/" + discussionID)

@app.route("/discussion/delete/<discussionID>", methods = ["GET"])
@login_required
@email_required
def discussionDelete(discussionID):
    # make sure discussion exists
    dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    dict_cur.execute("""SELECT * FROM discussions WHERE id = %s""", [int(discussionID)])
    discussionRowPresence = [dict(row) for row in dict_cur.fetchall()]
    if len(discussionRowPresence) == 0:
        flash("We cannot find the discussion you're looking for.", flashStyling("warning"))
        return redirect("/discussions")
    # make sure the discussion to be deleted belongs to the logged-in user
    dict_cur.execute("""SELECT sender_id FROM discussions WHERE id = %s""", [int(discussionID)])
    senderIDList = [dict(row) for row in dict_cur.fetchall()]
    if senderIDList[0]['sender_id'] != int(session.get('id')):
        flash("You are not authorized to delete this discussion.", flashStyling("warning"))
        return redirect("/discussion/" + discussionID)

    dict_cur.execute("""BEGIN""")
    try:
        dict_cur.execute("""DELETE FROM discussions WHERE id = %s""", [int(discussionID)])
    except Exception as error:
        print ("Oops! An exception has occurred:", error)
        print ("Exception TYPE:", type(error))
        dict_cur.execute("""ROLLBACK""")
        abort(500)
    else:
        dict_cur.execute("""COMMIT""")
    dict_cur.close()
    return redirect("/discussions")

@app.route("/discussion/edit/<discussionID>", methods = ["GET","POST"])
@login_required
@email_required
def discussionEdit(discussionID):
    if request.method == "GET":
        userDict = buildUserDict()
        userRows = getUserRows(session.get("id"))
        selectsDict = dbSimpleDictBuilder('relationships+id+ASC','genders+id+ASC','ages+id+ASC','challenges+challenge+ASC')
        # make sure the item exists
        dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        dict_cur.execute("""SELECT * FROM discussions WHERE id = %s""", [int(discussionID)])
        discussionRowPresence = [dict(row) for row in dict_cur.fetchall()]
        if len(discussionRowPresence) == 0:
            flash("We cannot find the discussion you're looking for.", flashStyling("warning"))
            return redirect("/discussions")
        # make sure the item to be edited belongs to the logged-in user
        dict_cur.execute("""SELECT sender_id FROM discussions WHERE id = %s""", [int(discussionID)])
        senderIDList = [dict(row) for row in dict_cur.fetchall()]
        if senderIDList[0]['sender_id'] != int(session.get('id')):
            flash("You are not authorized to edit this content.", flashStyling("warning"))
            return redirect("/discussion/" + discussionID)
        discussionRows = getDiscussionRowsForDisplay(discussionID)
        editMode = "edit"
        return render_template("discussionThread.html", userDict = userDict, selectsDict = selectsDict, discussionRow = discussionRows[0], editMode = editMode)
    else:
        # post request
        newChallengeList = request.form.getlist('challenge')
        newAgeList = request.form.getlist('age')
        newGenderList = request.form.getlist('gender')
        # capture the content of other form values
        rawHTML = request.form.get('rawHTML')
        subject = request.form.get('subject')
        passedDict = {}
        passedDict['text'] = rawHTML
        passedDict['subject'] = subject
        # print(f"Passed dictionary is {passedDict}")
        keysList = list(passedDict.keys())
        keysString = ",".join(keysList)
        valuesList = list(passedDict.values())
        valuesString = ""
        for i in range(len(valuesList)):
            if type(valuesList[i]) == str:
                valuesString += "'" + valuesList[i] + "'"
            else:
                valuesString += str(valuesList[i])
            if i < len(valuesList)-1:
                valuesString += ","
        # print(f"keysString is {keysString} and valuesString is {valuesString}")
        if len(passedDict.keys()) > 1:
            update_str = sql.SQL("UPDATE discussions SET (%s) = (%s) WHERE id = %s")
        else:
            update_str = sql.SQL("UPDATE discussions SET %s = %s WHERE id = %s")
        dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        dict_cur.execute("""BEGIN""")
        try:
            # update discussion row
            dict_cur.execute(update_str,[AsIs(keysString),AsIs(valuesString),int(discussionID)])
            # remove all challenges, ages, genders from their discussion join tables
            dict_cur.execute("""DELETE FROM discussion_challenge WHERE discussion_id = %s""",[int(discussionID)])
            dict_cur.execute("""DELETE FROM discussion_age WHERE discussion_id = %s""",[int(discussionID)])
            dict_cur.execute("""DELETE FROM discussion_gender WHERE discussion_id = %s""",[int(discussionID)])
            # insert new challenges, ages, genders into their discussion join tables
            if len(newChallengeList) > 0:
                for challenge in newChallengeList:
                    dict_cur.execute("""INSERT INTO discussion_challenge (discussion_id, challenge_id) VALUES (%s,%s)""", [int(discussionID), challenge])
            if len(newAgeList) > 0:
                for age in newAgeList:
                    dict_cur.execute("""INSERT INTO discussion_age (discussion_id, age_id) VALUES (%s,%s)""", [int(discussionID), age])
            if len(newGenderList) > 0:
                for gender in newGenderList:
                    dict_cur.execute("""INSERT INTO discussion_gender (discussion_id, gender_id) VALUES (%s,%s)""", [int(discussionID), gender])
        except Exception as error:
            print ("Oops! An exception has occurred:", error)
            print ("Exception TYPE:", type(error))
            dict_cur.execute("""ROLLBACK""")
            abort(500)
        else:
            dict_cur.execute("""COMMIT""")
        dict_cur.close()
        # redirect the user to the view version of this discussion that was just edited
        return redirect("/discussion/" + discussionID)

@app.route("/discussion/thread/", methods = ["GET","POST"])
@login_required
@email_required
def discussionThreadBlank():
    if request.method == "GET":
        userDict = buildUserDict()
        userRows = getUserRows(session.get("id"))
        selectsDict = dbSimpleDictBuilder('relationships+id+ASC','genders+id+ASC','ages+id+ASC','challenges+challenge+ASC')
        editMode = "create"
        # create empty list for discussionRow so the jinja template logic will be happy
        discussionRow = [{
            'id':"",
            'subject':"",
            'text':"",
            'challenge_ids':"",
            'age_ids':"",
            'gender_ids':""
        }]
        return render_template("discussionThread.html", userDict = userDict, userRows = userRows, selectsDict = selectsDict, discussionRow = discussionRow, editMode = editMode)
    else:
        # method was POST
        # to write a new discussion, take the following steps
        # get the selections from each of the selects and condense them into lists/arrays
        newChallengeList = request.form.getlist('challenge')
        newAgeList = request.form.getlist('age')
        newGenderList = request.form.getlist('gender')
        passedDict = {}
        # capture the content of other form values
        passedDict['text'] = request.form.get('rawHTML')
        passedDict['subject'] = request.form.get('subject')
        passedDict['sender_id'] = session.get('id')
        # print(f"Passed dictionary is {passedDict}")
        insert_flds = [fld_name for fld_name in passedDict.keys()]
        # print(f"Insert fields: {insert_flds}")
        insert_str = sql.SQL("INSERT INTO discussions ({}) VALUES ({}) RETURNING id").format(
        sql.SQL(",").join(map(sql.Identifier, insert_flds)),
        sql.SQL(",").join(map(sql.Placeholder, insert_flds)))
        # print(f"Insert string is: {insert_str}")
        # begin transaction
        dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        dict_cur.execute("""BEGIN""")
        try:
            # create new discussion and capture its id
            dict_cur.execute(insert_str,passedDict)
            newID = [dict(row) for row in dict_cur.fetchall()]
            newID = newID[0]['id']
            # populate the other tables as needed (challenges, ages, genders)
            if len(newChallengeList) > 0:
                for challenge in newChallengeList:
                    dict_cur.execute("""INSERT INTO discussion_challenge (discussion_id, challenge_id) VALUES (%s,%s)""", [newID, challenge])
            if len(newAgeList) > 0:
                for age in newAgeList:
                    dict_cur.execute("""INSERT INTO discussion_age (discussion_id, age_id) VALUES (%s,%s)""", [newID, age])
            if len(newGenderList) > 0:
                for gender in newGenderList:
                    dict_cur.execute("""INSERT INTO discussion_gender (discussion_id, gender_id) VALUES (%s,%s)""", [newID, gender])
        except Exception as error:
            print ("Oops! An exception has occurred:", error)
            print ("Exception TYPE:", type(error))
            dict_cur.execute("""ROLLBACK""")
            abort(500)
        else:
            dict_cur.execute("""COMMIT""")
        dict_cur.close()
        # redirect the user to the view version of this discussion that was just created
        return redirect("/discussion/" + str(newID))

@app.route("/discussions", methods = ["GET"])
def discussions():
    userDict = buildUserDict()
    retrieveLimit = 50
    allDiscussionsList = []
    commentCount = 0
    # retrieve 50 most recent discussions from db
    dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    dict_cur.execute("""
    SELECT id FROM discussions
    ORDER BY date_created DESC
    LIMIT %s
    """, [retrieveLimit])
    allDiscussionIDs = [dict(row) for row in dict_cur.fetchall()]
    # print(allDiscussionIDs)
    # loop thru discussions and prep each one for display
    for item in allDiscussionIDs:
        commentCount = 0
        discussionRow = getDiscussionRowsForDisplay(item['id'])
        # count number of comments for each, add it to the dict
        dict_cur.execute("""SELECT COUNT(*) FROM comments WHERE discussion_id = %s""", [item['id']])
        commentCount = [dict(row) for row in dict_cur.fetchall()]
        discussionRow[0]['commentCount'] = commentCount[0]['count']
        # get textContent from HTML for each discussion; add it to the dict
        textContent = getTextContentFromHTML(discussionRow[0]['text'])
        discussionRow[0]['textContent'] = textContent
        # check for images in the HTML; grab code for the first one
        imageTagCode = getFirstImageFromHTML(discussionRow[0]['text'])[0]
        # get just the img src for use with the thumbnail
        imageTagSrc = getFirstImageFromHTML(discussionRow[0]['text'])[1]
        discussionRow[0]['imageTagCode'] = imageTagCode
        discussionRow[0]['imageTagSrc'] = imageTagSrc
        allDiscussionsList.append(discussionRow[0])
    dict_cur.close()
    # print(allDiscussionsList)
    return render_template ("discussionsView.html", userDict = userDict, allDiscussionsList = allDiscussionsList)

@app.route("/emailVerify1")
def emailVerify1():
    userDict = buildUserDict()
    return render_template ("emailVerify1.html", userDict = userDict)

@app.route("/emailVerifyReminder")
def emailVerifyReminder():
     #if not logged in
    if session.get("id") is None:
        return redirect("/signin")
    else:
        if session.get("emailConfirmed") == False:
            emailAddress = session.get("email")
            userDict = buildUserDict()
            return render_template("emailVerifyReminder.html", userDict = userDict, emailAddress = emailAddress)
        else:
            return redirect("/")

@app.route("/emailReverify")
def emailReverify():
    #if not logged in
    if session.get("id") is None:
       return redirect("/signin")
    else:
        if session.get("emailConfirmed") == 0:
            emailAddress = session.get("email")
            #call function to generate token and send email for verification
            sendVerificationEmail(emailAddress)
            #display the message that email has been sent for verification
            return redirect("/emailVerify1")
        else:
            #redirect to index route
            return redirect("/")

@app.route("/emailVerify/<token>")
def emailVerify(token):
    try:
        email = s.loads(token, salt='email-verify', max_age=7200)
    except SignatureExpired:
        userDict = buildUserDict()
        return errorView(userDict, "Token has expired", "Your email verification token has expired.", "Try again", "emailReverify")
    # email was verified, so retrieve user record
    dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    # update user record so emailConfirmed = True
    dict_cur.execute("""BEGIN""")
    try:
        dict_cur.execute("""UPDATE users SET email_confirmed = TRUE WHERE email = (%s)""", [email])
    except Exception as error:
        print ("Oops! An exception has occurred:", error)
        print ("Exception TYPE:", type(error))
        dict_cur.execute("""ROLLBACK""")
        abort(500)
    dict_cur.execute("COMMIT")
    # if not already logged in, log them in
    if session.get("id") is None:
        dict_cur.execute("""SELECT * FROM users WHERE email = (%s)""", [email])
        rows = [dict(row) for row in dict_cur.fetchall()]
        setSessionValues(rows)
        session["emailConfirmed"] = rows[0]["email_confirmed"]
    else:  # if already logged in, just update the session key for emailConfirmed
        session["emailConfirmed"] = True
    # send them to first page of profile sequence
    flash("Thanks, " + session["username"] + ", your email has been verified.", flashStyling("success"))
    return redirect("/profile1")

@app.route("/error")
def error():
    #this is just a prototype
    userDict = buildUserDict()
    return errorView(userDict, "We have a problem", "The database didn't show up for work today.", "Go to Topics", "topics")

@app.route("/messages/preload/<string>", methods = ["GET"])
@login_required
@email_required
def messagesPreload(string):
    dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    dict_cur.execute("""SELECT DISTINCT id, first_name, last_name, username FROM users WHERE first_name ILIKE %s OR last_name ILIKE %s OR username ILIKE %s ORDER BY first_name ASC""", [string + '%', string + '%', string + '%'])
    nameRows = [dict(row) for row in dict_cur.fetchall()]
    dict_cur.close()
    return jsonify(nameRows)

@app.route("/messages/view")
@login_required
@email_required
def messagesView():
    retrieveLimit = 50
    userDict = buildUserDict()
    userRows = getUserRows(session.get("id"))
    # retrieve unread messages for this user, limit 20; include the recipientID minus the userID so we can link to the thread
    # if length of resulting rows is less than 20, retrieve read messages for this user, limit 20 minus count
    # messageViewList = db.execute("SELECT messageID FROM MessageToRecipient WHERE recipientID = ? AND read = 0 LIMIT ? ORDER BY ")
    dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    dict_cur.execute("""
    SELECT * FROM messages
    LEFT JOIN message_recipient on messages.id = message_recipient.message_id
    WHERE message_recipient.recipient_id = %s
    ORDER BY message_recipient.read ASC, messages.date_created DESC
    LIMIT %s;
    """, [int(session.get("id")), retrieveLimit])
    threadRows = [dict(row) for row in dict_cur.fetchall()]
    dict_cur.close()
    # loop through senders and derive their displayName, profile_image, etc. for sending to the template
    superMessageList = messagePrepForDisplay(threadRows, True)
    # print(f"superMessageList = {superMessageList}")
    return render_template("messagesView.html", userDict = userDict, userRows = userRows, superMessageList = superMessageList)
    # return "hello"

@app.route("/messages/thread/<recipients>", methods = ["GET"])
@login_required
@email_required
def messagesThread(recipients):
    userDict = buildUserDict()
    userRows = getUserRows(session.get("id"))
    threadRows = []
    peopleRows = []
    ajaxMode = False
    # get recipients array from args
    threadArrayAll = recipients.split(',')
    # check for ajax flag in the args
    if "ajax" in threadArrayAll:
        ajaxMode = True
        threadArrayAll.remove("ajax")
    # build list of all the recipients, even if they haven't contributed yet to the thread, to display their names on the page
    dbSelectCommand = "SELECT * FROM users WHERE "
    for item in threadArrayAll:
        if "=" in dbSelectCommand:
            dbSelectCommand += " OR id = " + item
        else:
            dbSelectCommand += "id = " + item
    dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    dict_cur.execute(dbSelectCommand)
    peopleRows = [dict(row) for row in dict_cur.fetchall()]
    for row in peopleRows:
        personDisplayName = buildDisplayName(row)
        row['displayName'] = personDisplayName
    # convert each userID to int
    threadArrayAll = list(map(int, threadArrayAll))
    # add the logged-in user's ID to the array if it's not there already; this prevents someone from viewing other people's threads
    if session.get("id") not in threadArrayAll:
        threadArrayAll.append(session.get("id"))
    threadArrayAll.sort()
    # print(threadArrayAll)
    # execute query string, return result as threadRows
    threadRows = processMessageThread(threadArrayAll)
    # go thru threadrows and update the "read" column value to true for each of the user's messages in message_recipient
    dict_cur.execute("""BEGIN""")
    try:
        for item in threadRows:
            dict_cur.execute("""UPDATE message_recipient SET read = 'true' WHERE message_id = %s AND recipient_id = %s""", [item['id'], int(session.get("id"))])
    except Exception as error:
        print ("Oops! An exception has occurred:", error)
        print ("Exception TYPE:", type(error))
        dict_cur.execute("""ROLLBACK""")
        abort(500)
    else:
        dict_cur.execute("""COMMIT""")
    dict_cur.close()
    if ajaxMode:
        return jsonify(threadRows)
    else:
        return render_template("messagesThread.html", userDict = userDict, userRows = userRows, threadRows = threadRows, recipients = recipients, peopleRows = peopleRows)

@app.route("/messages/thread/", methods = ["GET","POST"])
@login_required
@email_required
def messagesThreadBlank():
    if request.method == "GET":
        userDict = buildUserDict()
        userRows = getUserRows(session.get("id"))
        threadRows = []
        peopleRows = []
        recipients = ""
        return render_template("messagesThread.html", userDict = userDict, userRows = userRows, threadRows = threadRows, recipients = recipients, peopleRows = peopleRows)
    else:
        # method was POST
        # to write a new message, take the following steps
        recipientsList = request.form.get('recipientsCSV').split(',')
        # print (f"recipientsList = {recipientsList}")
        # make sure the logged in user is not the sole recipient; if so, send feedback
        if len(recipientsList) == 1 and int(recipientsList[0]) == session.get('id'):
            flash("You can't send a message to yourself. At least not on this website. Please try again.", flashStyling("danger"))
            return redirect('/messages/thread/')
        # write a new row to message table, and get the newly created id
        dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        # for each recipient, write a new row to message_recipient
        dict_cur.execute("""BEGIN""")
        try:
            # create new messages row with data from the form
            dict_cur.execute("""INSERT INTO messages (sender_id, text) VALUES (%s,%s) RETURNING id""", [session.get("id"), request.form.get('messageText')])
            newID = [dict(row) for row in dict_cur.fetchall()]
            newID = newID[0]['id']
            # loop through recipients list and add rows to MessageToRecipient table
            for item in recipientsList:
                dict_cur.execute("""INSERT INTO message_recipient (message_id, recipient_id) VALUES (%s,%s)""", [newID, int(item)])
        except Exception as error:
            print ("Oops! An exception has occurred:", error)
            print ("Exception TYPE:", type(error))
            dict_cur.execute("""ROLLBACK""")
            abort(500)
        else:
            dict_cur.execute("""COMMIT""")
        dict_cur.close()
        # return the user to the same thread, with the newly added message displayed (hopefully!)
        return redirect('/messages/thread/' + request.form.get('recipientsCSV'))

@app.route("/passwordreset1", methods = ["GET","POST"])
def passwordReset1():
    if request.method == "GET":
        # call a function that checks for authentication and sends correct object to the template
        userDict = buildUserDict()
        return render_template ("passwordReset1.html", userDict = userDict)
    else:
        # we have a post request
        # first make sure the email submitted is in the db
        dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        dict_cur.execute("""SELECT username FROM users WHERE email = %s""",[request.form.get('email')])
        emailMatched = dict_cur.fetchall()
        if len(emailMatched) == 0:
            flash("This email is not associated with any user. Try a different email address, or register a new account with the link below.", flashStyling("danger"))
            return redirect('/passwordreset1')
        else:
            sendPasswordResetEmail(request.form.get('email'))
            return redirect('/passwordreset2/' + request.form.get('email'))

@app.route("/passwordreset2/<email>")
def passwordReset2(email):
    # call a function that checks for authentication and sends correct object to the template
    userDict = buildUserDict()
    return render_template ("passwordReset2.html", email=email, userDict = userDict)

@app.route("/passwordreset3/<token>", methods = ["GET", "POST"])
def passwordReset3(token):
    try:
        email = s.loads(token, salt='password-reset', max_age=7200)
    except SignatureExpired:
        userDict = buildUserDict()
        return errorView(userDict, "Token has expired", "Your password reset token has expired.", "Try again", "passwordReset1")
    if request.method == "GET":
        userDict = buildUserDict()
        return render_template ("passwordReset3.html", userDict = userDict)
    if request.method == "POST":
        # Ensure password was submitted, which is 99% certain via client side JS form validation
        if not request.form.get("password1"):
            flash("Please provide your new password.",flashStyling("danger"))
            return redirect("/passwordreset3/" + token)
        # hash the new password to create a text variable
        pw_hash = generate_password_hash(request.form.get("password1"), method='pbkdf2:sha256', salt_length=8)
        # update user record with new password
        dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        dict_cur.execute("""BEGIN""")
        try:
            dict_cur.execute("""UPDATE users SET pw_hash = %s WHERE email = %s""", [pw_hash,email])
        except Exception as error:
            print ("Oops! An exception has occurred:", error)
            print ("Exception TYPE:", type(error))
            dict_cur.execute("""ROLLBACK""")
            abort(500)
        dict_cur.execute("COMMIT")
        # log the user in
        if session.get("id") is None:
            dict_cur.execute("""SELECT * FROM users WHERE email = %s""", [email])
            rows = [dict(row) for row in dict_cur.fetchall()]
            # print(f"email is: {email}")
            # print(f"Rows: {rows}")
            setSessionValues(rows)
        # continue to home page
        flash("Thanks, " + session["username"] + ", your password has been reset.", flashStyling("success"))
        return redirect ("/")

@app.route("/people")
def people():
    # set the max number of people to display when the page loads
    defaultLimit = '50'
    userDict = buildUserDict()
    dbSelectCommand = "SELECT * FROM users "
    queryDict = {}
    rowCountDict = {}
    # here we add parameters to the db query based on request.args
    if request.args:
        # convert request.args immutable multidict to a regular dict
        argsDict = request.args.to_dict(flat=True)
        for item in argsDict.keys():
            # print(f"{item} is {argsDict[item]}")
            if item == 'offset' or item == 'limit':
                rowCountDict[item] = argsDict[item]
            elif argsDict[item] != "":
                queryDict[item] = argsDict[item]
        # print(f"rowCountDict is: {rowCountDict}")
        # print(f"queryDict is: {queryDict}")
    # translate request.args into dict_cur.execute language
    joinString = "LEFT OUTER JOIN loved_ones on loved_ones.user_id = users.id "
    whereString = ""
    gotLovedOnes = False
    if len(queryDict) > 0:
        whereString += " WHERE "
        if 'relationship' in queryDict and queryDict['relationship'] != "":
            gotLovedOnes = True
            joinString += "LEFT OUTER JOIN relationships on relationships.id = loved_ones.relationship_id "
            if " = " in whereString:
                whereString += " and "
            whereString += "loved_ones.relationship_id = " + queryDict['relationship']
        if 'challenge' in queryDict and queryDict['challenge'] != "":
            gotLovedOnes = True
            joinString += "LEFT OUTER JOIN loved_one_challenge on loved_one_challenge.loved_one_id = loved_ones.id LEFT OUTER JOIN challenges on challenges.id = loved_one_challenge.challenge_id "
            if " = " in whereString:
                whereString += " and "
            whereString += "loved_one_challenge.challenge_id = " + queryDict['challenge']
        if 'age' in queryDict and queryDict['age'] != "":
            gotLovedOnes = True
            joinString += "LEFT OUTER JOIN ages on ages.id = loved_ones.age_id "
            if " = " in whereString:
                whereString += " and "
            whereString += "loved_ones.age_id = " + queryDict['age']
        if 'gender' in queryDict and queryDict['gender'] != "":
            gotLovedOnes = True
            joinString += "LEFT OUTER JOIN genders on genders.id = loved_ones.gender_id "
            if " = " in whereString:
                whereString += " and "
            whereString += "loved_ones.gender_id = " + queryDict['gender']
        if 'state' in queryDict and queryDict['state'] != "":
            if " = " in whereString:
                whereString += " and "
            whereString += "users.state = '" + queryDict['state'] + "'"
        if 'county' in queryDict and queryDict['county'] != "":
            if " = " in whereString:
                whereString += " and "
            whereString += "users.county = '" + queryDict['county'] + "'"
        if 'city' in queryDict and queryDict['city'] != "":
            if " = " in whereString:
                whereString += " and "
            whereString += "users.city = '" + queryDict['city'] + "'"
        if 'name' in queryDict and queryDict['name'] != "":
            if " = " in whereString:
                whereString += " and "
            whereString += "(users.first_name ILIKE '%" + queryDict['name'] + "%' or users.last_name ILIKE '%" + queryDict['name'] + "%' or users.username ILIKE '%" + queryDict['name'] + "%')"
    if gotLovedOnes == True:
        dbSelectCommand += joinString
    dbSelectCommand += whereString
    if len(rowCountDict) > 0:
        if rowCountDict['limit']:
            dbSelectCommand += " LIMIT " + rowCountDict['limit']
        if rowCountDict['offset']:
            dbSelectCommand += " OFFSET " + rowCountDict['offset']
    # provide default values if user has not specified limit
    if 'LIMIT' not in dbSelectCommand:
        dbSelectCommand += " LIMIT " + defaultLimit
    # print(f"dbSelectCommand: {dbSelectCommand}")
    dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    dict_cur.execute(dbSelectCommand)
    peopleRows = [dict(row) for row in dict_cur.fetchall()]
    dict_cur.close()
    for row in peopleRows:
        personDisplayName = buildDisplayName(row)
        row['displayName'] = personDisplayName
    zipcode = ""
    state = request.args.get('state') if request.args.get('state') else ""
    city = request.args.get('city') if request.args.get('city') else ""
    county = request.args.get('county') if request.args.get('county') else ""
    selects3Dict = dbSimpleDictBuilder('relationships+id+ASC','genders+id+ASC','ages+id+ASC','challenges+challenge+ASC')
    super4Dict = citiesDictBuilder(zipcode,state,city,county)
    # print(f"super4Dict: {super4Dict}")
    # print(f"queryDict: {queryDict}")
    return render_template("people.html", userDict = userDict, peopleRows = peopleRows, selects4Dict = super4Dict['selects'], selects3Dict = selects3Dict, rowCountDict = rowCountDict, queryDict = queryDict)

@app.route("/person/<username>")
def person(username):
    userDict = buildUserDict()
    dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    dict_cur.execute("""SELECT * FROM users WHERE username = %s""", [username])
    personRows = [dict(row) for row in dict_cur.fetchall()]
    personID = personRows[0]['id']
    lovedOnes = selectLovedOnes(personID)
    personDisplayName = buildDisplayName(personRows[0])
    return render_template("person.html", userDict = userDict, personRows = personRows, personDisplayName = personDisplayName, lovedOnes = lovedOnes)

@app.route("/profile")
@login_required
@email_required
def profile():
    userDict = buildUserDict()
    userRows = getUserRows(session.get("id"))
    selects3Dict = dbSimpleDictBuilder('relationships+id+ASC','genders+id+ASC','ages+id+ASC','challenges+challenge+ASC')
    lovedOnes = selectLovedOnes(session.get("id"))
    super4Dict = citiesDictBuilder(userRows[0]['zip'],userRows[0]['state'],userRows[0]['city'],userRows[0]['county'])
    if super4Dict['selects']['zip'] and super4Dict['selects']['zip'][0] == 'invalid':
        flash("You provided a ZIP code that is not in our database. Please try again, or skip it and select your state, city and county.", flashStyling("danger"))
    return render_template("profile.html", userDict = userDict, userRows = userRows, formSource = "profile", editID = "", lovedOnes = lovedOnes, selects3Dict = selects3Dict, selects4Dict = super4Dict['selects'])

@app.route("/profile1")
@login_required
@email_required
def profile1():
    userDict = buildUserDict()
    return render_template("profileSequence1.html", userDict = userDict)

@app.route("/profile2", methods = ["GET","POST"])
@login_required
@email_required
def profile2():
    if request.method == "GET":
        userDict = buildUserDict()
        userRows = getUserRows(session.get("id"))
        return render_template("profileSequence2.html", userDict = userDict, userRows = userRows, formSource = "profile2")
    else:
        nextURLs = getProfileNextURLs(request.form.get("formSource2"))
        # check the uploaded file in terms of size, properties, etc. If it fails, redirect to same page with error message. If it passes, store the file with user id as its filename and update the db
        # print (f"File list: {request.files.getlist('file')}")
        if "file" not in request.files:
            userDict = buildUserDict()
            return errorView(userDict,"Upload file not found","We did not receive the file you tried to upload.","Try again",nextURLs['tryAgainURL'])
        uploaded_file = request.files['file']
        filename = uploaded_file.filename
        # print(f"Filename is {filename}.")
        dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        if filename != '':
            file_ext = os.path.splitext(filename)[1]
            if file_ext not in app.config['UPLOAD_EXTENSIONS'] or \
                    file_ext != validate_image(uploaded_file.stream):
                # abort(400)
                userDict = buildUserDict()
                return errorView(userDict,"File type not allowed","We cannot accept the file type you tried to upload.","Try again",nextURLs['tryAgainURL'])
            uploaded_file.save(os.path.join(app.config['UPLOAD_PATH'], str(session.get("id")) + file_ext))
            #update the db with filename
            dict_cur.execute("""BEGIN""")
            try:
                dict_cur.execute("""UPDATE users SET profile_image = (%s) WHERE id = (%s)""", [str(session.get("id")) + file_ext, session.get("id")])
            except Exception as error:
                print ("Oops! An exception has occurred:", error)
                print ("Exception TYPE:", type(error))
                dict_cur.execute("""ROLLBACK""")
                abort(500)
            dict_cur.execute("""COMMIT""")
        # retrieve the user's db record and store in a dict
        dict_cur.execute("""SELECT * FROM users WHERE id = (%s)""", [session.get("id")])
        rows = [dict(row) for row in dict_cur.fetchall()]
        # compare submitted username to existing. If different, make sure the new one is unique. If not redirect to same page with error message. Else, update db record and move on to next step.
        if request.args.get("username") != rows[0]["username"]:
            dict_cur.execute("""SELECT * FROM users WHERE username = (%s)""", [request.args.get("username")])
            usernameCheck = [dict(row) for row in dict_cur.fetchall()]
            if len(usernameCheck) > 0:
                #requested username already exists in the db
                flash("The username you requested (" + request.args.get('username') + ") is already in use. Please try again.", flashStyling("danger"))
                return redirect(nextURLs['tryAgainURL'])
            #update the db with username
            dict_cur.execute("""BEGIN""")
            try:
                dict_cur.execute("""UPDATE users SET username = (%s) WHERE id = (%s)""", [request.args.get("username"), session.get("id")])
            except Exception as error:
                print ("Oops! An exception has occurred:", error)
                print ("Exception TYPE:", type(error))
                dict_cur.execute("""ROLLBACK""")
                abort(500)
            dict_cur.execute("""COMMIT""")
        # compare submitted firstName to existing. If different, update firstName in db record
        if request.args.get("first_name") != rows[0]["first_name"]:
            dict_cur.execute("""BEGIN""")
            try:
                dict_cur.execute("""UPDATE users SET first_name = (%s) WHERE id = (%s)""", [request.args.get("first_name"), session.get("id")])
            except Exception as error:
                print ("Oops! An exception has occurred:", error)
                print ("Exception TYPE:", type(error))
                dict_cur.execute("""ROLLBACK""")
                abort(500)
            dict_cur.execute("""COMMIT""")
        # compare submitted lastName to existing. If different, update lastName in db record
        if request.args.get("last_name") != rows[0]["last_name"]:
            dict_cur.execute("""BEGIN""")
            try:
                dict_cur.execute("""UPDATE users SET last_name = (%s) WHERE id = (%s)""", [request.args.get("last_name"), session.get("id")])
            except Exception as error:
                print ("Oops! An exception has occurred:", error)
                print ("Exception TYPE:", type(error))
                dict_cur.execute("""ROLLBACK""")
                abort(500)
            dict_cur.execute("""COMMIT""")
        # compare submitted displayNameOption to existing. If different, update displayNameOption in db record.
        displayNameOptionRequest = int(request.args.get("display_name_option"))
        if displayNameOptionRequest != rows[0]["display_name_option"]:
            dict_cur.execute("""BEGIN""")
            try:
                dict_cur.execute("""UPDATE users SET display_name_option = (%s) WHERE id = (%s)""", [displayNameOptionRequest, session.get("id")])
            except Exception as error:
                print ("Oops! An exception has occurred:", error)
                print ("Exception TYPE:", type(error))
                dict_cur.execute("""ROLLBACK""")
                abort(500)
            dict_cur.execute("""COMMIT""")
        dict_cur.close()
        return redirect(nextURLs['successURL']) # or conditional destination, based on formSource

@app.route("/profile3", methods = ["GET","POST"])
@login_required
@email_required
def profile3():
    if request.method == "GET":
        userDict = buildUserDict()
        userRows = getUserRows(session.get("id"))
        selects3Dict = dbSimpleDictBuilder('relationships+id+ASC','genders+id+ASC','ages+id+ASC','challenges+challenge+ASC')
        lovedOnes = selectLovedOnes(session.get("id"))
        return render_template("profileSequence3.html", userDict = userDict, userRows = userRows, formSource = "profile3", editID = "", lovedOnes = lovedOnes, selects3Dict = selects3Dict)
    else:
        # we have POST request
        newAge = request.form.get('age')
        newChallengeList = request.form.getlist('challenge')
        newGender = request.form.get('gender')
        newRelationship = request.form.get('relationship')
        passedDict = {}
        if newAge != '':
           passedDict['age_id'] = int(newAge)
        if newGender != '':
            passedDict['gender_id'] = int(newGender)
        if newRelationship != '':
            passedDict['relationship_id'] = int(newRelationship)
        passedDict['user_id'] = session.get('id')
        # print(f"Passed dictionary is {passedDict}")
        insert_flds = [fld_name for fld_name in passedDict.keys()]
        # print(f"Insert fields: {insert_flds}")
        insert_str = sql.SQL("INSERT INTO loved_ones ({}) VALUES ({}) RETURNING id").format(
        sql.SQL(",").join(map(sql.Identifier, insert_flds)),
        sql.SQL(",").join(map(sql.Placeholder, insert_flds)))
        nextURLs = getProfileNextURLs(request.form.get("formSource3"))
        dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        dict_cur.execute("""BEGIN""")
        try:
            # create new LovedOnes row
            dict_cur.execute(insert_str,passedDict)
            newID = [dict(row) for row in dict_cur.fetchall()]
            newID = newID[0]['id']
            # remove any and all challenges for this LovedOne in LovedOneToChallenge, then insert new ones from the form's array
            dict_cur.execute("""DELETE FROM loved_one_challenge WHERE loved_one_id = (%s)""", [newID])
            if len(newChallengeList) > 0:
                for challenge in newChallengeList:
                    dict_cur.execute("""INSERT INTO loved_one_challenge (loved_one_id, challenge_id) VALUES ((%s),(%s))""", [newID, challenge])
        except Exception as error:
            print ("Oops! An exception has occurred:", error)
            print ("Exception TYPE:", type(error))
            dict_cur.execute("""ROLLBACK""")
            abort(500)
        else:
            dict_cur.execute("""COMMIT""")
        dict_cur.close()
        return redirect(nextURLs['successURL']) # or conditional destination, based on formSource

@app.route("/profile3/edit/<editID>")
@login_required
@email_required
def profile3edit(editID):
    if request.method == "GET":
        # make sure the editID belongs to the logged-in user, so people can't edit other people's loved ones!
        dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        dict_cur.execute("""SELECT user_id FROM loved_ones WHERE id = (%s)""", [editID])
        lovedOneOwnerRow = [dict(row) for row in dict_cur.fetchall()]
        lovedOneOwnerID = lovedOneOwnerRow[0]['user_id']
        if session.get("id") != lovedOneOwnerID:
            flash("That item is not yours to edit.", flashStyling("danger"))
            return redirect("/")
        else:
            # good to go
            userDict = buildUserDict()
            userRows = getUserRows(session.get("id"))
            dict_cur.execute("""
            SELECT loved_ones.id, relationships.relationship, genders.gender, ages.age, challenges.challenge
            FROM loved_ones
            LEFT OUTER JOIN relationships on relationships.id = loved_ones.relationship_id
            LEFT OUTER JOIN genders on genders.id = loved_ones.gender_id
            LEFT OUTER JOIN ages on ages.id = loved_ones.age_id
            LEFT OUTER JOIN loved_one_challenge on loved_one_challenge.loved_one_id = loved_ones.id
            LEFT OUTER JOIN challenges on challenges.id = loved_one_challenge.challenge_id
            WHERE loved_ones.id = (%s) ORDER BY loved_ones.id ASC, challenges.id ASC;
            """, [editID])
            editRow = [dict(row) for row in dict_cur.fetchall()]
            dict_cur.close()
            editRow = buildChallengeList(editRow)
            return jsonify(editRow)

@app.route("/profile3/update/<editID>", methods=["POST"])
@login_required
@email_required
def profile3update(editID):
    if checkOwnership('loved_ones', editID):
        # we can update this item
        newRelationship = request.form.get('relationship')
        newChallengeList = request.form.getlist('challenge')
        newAge = request.form.get('age')
        newGender = request.form.get('gender')
        nextURLs = getProfileNextURLs(request.form.get("formSource3"))
        passedDict = {}
        if newAge != '':
           passedDict['age_id'] = int(newAge)
        if newGender != '':
            passedDict['gender_id'] = int(newGender)
        if newRelationship != '':
            passedDict['relationship_id'] = int(newRelationship)
        passedDict['user_id'] = session.get('id')
        # print(f"Passed dictionary is {passedDict}")
        dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        keysList = list(passedDict.keys())
        keysString = ",".join(keysList)
        valuesList = list(passedDict.values())
        valuesString = ""
        for i in range(len(valuesList)):
            if type(valuesList[i]) == str:
                valuesString += "'" + valuesList[i] + "'"
            else:
                valuesString += str(valuesList[i])
            if i < len(valuesList)-1:
                valuesString += ","
        # print(f"keysString is {keysString} and valuesString is {valuesString}")
        if len(passedDict.keys()) > 1:
            update_str = sql.SQL("UPDATE loved_ones SET (%s) = (%s) WHERE id = %s")
        else:
            update_str = sql.SQL("UPDATE loved_ones SET %s = %s WHERE id = %s")
        dict_cur.execute("""BEGIN""")
        try:
            # update this LovedOnes row
            dict_cur.execute(update_str, [AsIs(keysString),AsIs(valuesString),editID])
            # remove any and all challenges for this LovedOne in LovedOneToChallenge, then insert new ones from the form's array
            dict_cur.execute("""DELETE FROM loved_one_challenge WHERE loved_one_id = (%s)""", [editID])
            if len(newChallengeList) > 0:
                for challenge in newChallengeList:
                    dict_cur.execute("""INSERT INTO loved_one_challenge (loved_one_id, challenge_id) VALUES ((%s),(%s))""", [editID, challenge])
        except Exception as error:
            print ("Oops! An exception has occurred:", error)
            print ("Exception TYPE:", type(error))
            dict_cur.execute("""ROLLBACK""")
            abort(500)
        else:
            dict_cur.execute("""COMMIT""")
        dict_cur.close()
        return redirect(nextURLs['successURL']) # or conditional destination, based on formSource
    else:
        flash("You are not authorized to edit this content.", flashStyling("warning"))
        return redirect("/")

@app.route("/profile3/delete/<editID>/<formSource>", methods=["GET"])
@login_required
@email_required
def profile3delete(editID,formSource):
    if checkOwnership('loved_ones', editID):
        # we can delete this item
        nextURLs = getProfileNextURLs(formSource)
        dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            dict_cur.execute("""DELETE FROM loved_ones WHERE id = (%s)""", [editID])
        except Exception as error:
            print ("Oops! An exception has occurred:", error)
            print ("Exception TYPE:", type(error))
            dict_cur.execute("""ROLLBACK""")
            abort(500)
        else:
            dict_cur.execute("""COMMIT""")
        dict_cur.close()
        return redirect(nextURLs['tryAgainURL']) # or conditional destination, based on formSource
    else:
        flash("You are not authorized to delete this content.", flashStyling("warning"))
        return redirect("/")

@app.route("/profile4", methods = ["GET","POST"])
@login_required
@email_required
def profile4():
    if request.method == "GET":
        userDict = buildUserDict()
        userRows = getUserRows(session.get("id"))
        super4Dict = citiesDictBuilder(userRows[0]['zip'],userRows[0]['state'],userRows[0]['city'],userRows[0]['county'])
        if super4Dict['selects']['zip'] and super4Dict['selects']['zip'][0] == 'invalid':
            flash("You provided a ZIP code that is not in our database. Please try again, or skip it and select your state, city and county.", flashStyling("danger"))
        return render_template("profileSequence4.html", userDict = userDict, userRows = userRows, formSource = "profile4", selects4Dict = super4Dict['selects'])
    else:
        # post request
        # get form field values
        # userZip = request.form.get('zip');
        # note that we are NOT storing zip code; it's only for convenience as the user completes the form
        userState = request.form.get('state');
        userCounty = request.form.get('county');
        userCity = request.form.get('city');
        # save them to user's db record
        passedDict = {}
        if userState != '':
           passedDict['state'] = userState
        if userCounty != '':
            passedDict['county'] = userCounty
        if userCity != '':
            passedDict['city'] = userCity
        # print(f"Passed dictionary is {passedDict}")
        keysList = list(passedDict.keys())
        keysString = ",".join(keysList)
        valuesList = list(passedDict.values())
        valuesString = ""
        for i in range(len(valuesList)):
            if type(valuesList[i]) == str:
                valuesString += "'" + valuesList[i] + "'"
            else:
                valuesString += str(valuesList[i])
            if i < len(valuesList)-1:
                valuesString += ","
        # print(f"keysString is {keysString} and valuesString is {valuesString}")
        if len(passedDict.keys()) > 1:
            update_str = sql.SQL("UPDATE users SET (%s) = (%s) WHERE id = %s")
        else:
            update_str = sql.SQL("UPDATE users SET %s = %s WHERE id = %s")
        dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        dict_cur.execute("""BEGIN""")
        try:
            # update user's row
            dict_cur.execute(update_str,[AsIs(keysString),AsIs(valuesString),session.get('id')])
        except Exception as error:
            print ("Oops! An exception has occurred:", error)
            print ("Exception TYPE:", type(error))
            dict_cur.execute("""ROLLBACK""")
            abort(500)
        else:
            dict_cur.execute("""COMMIT""")
        dict_cur.close()
        nextURLs = getProfileNextURLs(request.form.get("formSource4"))
        return redirect(nextURLs['successURL']) # or conditional destination, based on formSource

@app.route("/profile4/geo")
@login_required
@email_required
def profile4geo():
    if request.method == "GET":
        # ternary operation in python: x = a if True else b
        zipcode = request.args.get('zip') if request.args.get('zip') else ""
        state = request.args.get('state') if request.args.get('state') else ""
        city = request.args.get('city') if request.args.get('city') else ""
        county = request.args.get('county') if request.args.get('county') else ""
        # return ("zipcode is "+zipcode+", state is "+state+", city is "+city+", county is "+county)
        super4Dict = citiesDictBuilder(zipcode,state,city,county)
        # print(f"super4Dict: {super4Dict}")
        return jsonify(super4Dict)

@app.route("/profile5")
@login_required
@email_required
def profile5():
    userDict = buildUserDict()
    return render_template("profileSequence5.html", userDict = userDict)

# @app.route("/ajaxtest")
# def ajaxtext():
#     if request.method == "GET":
#         # myState = request.args.get('state')
#         # countyList = ajaxtest_sub(myState)
#         # return countyList
#         cityConnect = SQL("sqlite:///uscities.db")
#         countyList = cityConnect.execute('SELECT * FROM cities WHERE ?', 'city = Union Springs')
#         return jsonify(countyList)


@app.route("/register", methods = ["GET", "POST"])
def register():
    if request.method == "GET":
        userDict = buildUserDict()
        if session.get("id") is None:
            return render_template ("register.html",userDict = userDict)
        else:
            flash("You requested the Register page, but you're already registered, so we're sending you to your Profile page instead.", flashStyling("warning"))
            return redirect("/profile")
    if request.method == "POST":
        # ensure username does NOT exist in db
        dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        dict_cur.execute("""SELECT * FROM users WHERE username = (%s)""", [request.form.get("username")])
        checkUsernameRow = [dict(row) for row in dict_cur.fetchall()]
        if len(checkUsernameRow) > 0:
            flash("That username is already being used; please choose another.", flashStyling("danger"))
            return redirect("/register")
        # ensure email does NOT exist in db
        dict_cur.execute("""SELECT * FROM users WHERE email = (%s)""", [request.form.get("email")])
        checkEmailRow = [dict(row) for row in dict_cur.fetchall()]
        if len(checkEmailRow) > 0:
            flash("That email address is already being used. You can use another, or use the \"Forgot / Reset password\" link at the bottom of this form.", flashStyling("danger"))
            return redirect("/register")
        # hash the pwd1 to create a text variable
        pw_hash = generate_password_hash(request.form.get("password"), method='pbkdf2:sha256', salt_length=8)
        # write a new row to the users db with username and hash
        dict_cur.execute("""BEGIN""")
        try:
            dict_cur.execute("""INSERT INTO users (username, email, pw_hash) VALUES((%s),(%s),(%s))""", [request.form.get("username"), request.form.get("email"), pw_hash])
        except Exception as error:
            print ("Oops! An exception has occurred:", error)
            print ("Exception TYPE:", type(error))
            dict_cur.execute("""ROLLBACK""")
            abort(500)
        dict_cur.execute("""COMMIT""")
        # select this new user from the db
        dict_cur.execute("""SELECT * FROM users WHERE username = (%s)""", [request.form.get("username")])
        rows = [dict(row) for row in dict_cur.fetchall()]
        dict_cur.close()
        # go ahead and log the user in
        setSessionValues(rows)
        #call function to generate token and send email for verification
        emailAddress = request.form.get("email")
        sendVerificationEmail(emailAddress)
        flash("Welcome, " + session["username"] + "! You are registered.", flashStyling("success"))
        return redirect("/emailVerify1")

@app.route("/signin", methods = ["GET", "POST"])
def signin():
    if request.method == "GET":
        userDict = buildUserDict()
        return render_template ("signin.html", userDict = userDict)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("email"):
            flash("Please provide your email address.",flashStyling("danger"))
            return redirect("/signin")

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("Please provide your password.",flashStyling("danger"))
            return redirect("/signin")

        # # Query database for username
        dict_cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        # dict_cur.execute("SELECT * FROM users WHERE email = (%s)", request.form.get('email'))
        dict_cur.execute("""SELECT * FROM users WHERE email = (%s)""", [request.form.get('email')])
        rows = dict_cur.fetchall()
        dict_cur.close() 
        # the cursor is now closed
        # Ensure email exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["pw_hash"], request.form.get("password")):
            flash("Invalid email or password. Try again, or use the \"Forgot / Reset password\" link at the bottom of this form",flashStyling("danger"))
            return redirect("/signin")

        # Remember which user has logged in
        setSessionValues(rows)
        # continue to destination page, or to home page if no destination
        if not request.form.get("next"):
            return redirect ("/")
        else:
            return redirect (request.form.get("next"))

@app.route("/signout")
def signout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to home page
    return redirect("/")

# @app.route("/topics", methods = ["GET", "POST"])
# @email_required
# def topics():
#     if request.method == "POST":
#         db.execute("INSERT INTO topics (topic) VALUES (?)", request.form.get("newTopic"))
#         return redirect("/topics")
#     # query db topics table to get list of topics
#     topics = db.execute("SELECT * FROM topics ORDER BY topic ASC")
#     userDict = buildUserDict()
#     return render_template ("topics.html", topics = topics, userDict = userDict)

# @app.route("/testForErrors", methods = ["GET", "POST"])
# def testForErrors():
#     if request.method == "POST":
#         userID = int(request.form.get("userID"))
#         topicID = int(request.form.get("topicID"))
#         db.execute("BEGIN TRANSACTION")
#         try:
#             db.execute("INSERT INTO UserToTopic (userID,topicID) VALUES (?,?)", userID, topicID)
#         except:
#             db.execute("ROLLBACK")
#             abort(500)
#         db.execute("COMMIT")
#         return "Your update was successful"
#     else:
#         return render_template ("testForErrors.html")


# ===== END ROUTES ========



# ======== START ERROR HANDLING ========

@app.errorhandler(400)
def badrequest_error():
    userDict = buildUserDict()
    return render_template('400.html', userDict = userDict), 400

@app.errorhandler(404)
def not_found_error(error):
    userDict = buildUserDict()
    return render_template('404.html', userDict = userDict), 404

@app.errorhandler(405)
def not_found_error(error):
    userDict = buildUserDict()
    return render_template('400.html', userDict = userDict), 405

@app.errorhandler(413)
def request_entity_too_large(error):
    userDict = buildUserDict()
    return render_template('413.html', userDict = userDict), 413

@app.errorhandler(500)
def internal_error(error):
    userDict = buildUserDict()
    return render_template('500.html', userDict = userDict), 500
# ======== END ERROR HANDLING ========

# ========= OTHER HANDY FUNCTIONS ============
def buildUserDict():
    if session.get("id") is None:
        userDict = {}
    else:
        # retrieve properties from authenticated user's db record for sending to view templates
        displayName = ""

        # rows = db.execute("SELECT * FROM users WHERE id = ?", session.get("id"))
        dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        dict_cur.execute("""SELECT * FROM users WHERE id = (%s)""", [session.get('id')])
        rows = [dict(row) for row in dict_cur.fetchall()]
        displayNameMaxLength = 20
        if rows[0]["display_name_option"] == 1:
            displayName = rows[0]["username"]
            # truncate the string to maxlength w/ellipsis if needed
            if len(displayName) > displayNameMaxLength:
                displayName = displayName[:displayNameMaxLength-3] + "..."
        else:
            firstName = rows[0]["first_name"]
            lastName = rows[0]["last_name"]
            if len(firstName) + len(lastName) + 1 > displayNameMaxLength:
                if len(firstName) < displayNameMaxLength - 2:
                    #this means we could fit the entire first name w/ last initial
                    displayName = firstName + " " + lastName[0]
                else:
                    #first name is too long, we need to truncate
                    displayName = firstName[:displayNameMaxLength-2] + " " + lastName[0]
            else:
                displayName = firstName + " " + lastName
        # now get a count of unread messages
        dict_cur.execute("""SELECT COUNT (message_id) FROM message_recipient WHERE recipient_id = (%s) AND read = 'false'""",[session.get("id")])
        unreadMessageCount = [dict(row) for row in dict_cur.fetchall()]
        # unreadMessageCount = db.execute("SELECT COUNT (messageID) FROM MessageToRecipient WHERE recipientID = ? AND read = 0", session.get("id"))
        dict_cur.close()

        userDict = {
            "id":rows[0]["id"],
            "displayName":displayName,
            "profileImage":rows[0]["profile_image"],
            "emailConfirmed":rows[0]["email_confirmed"],
            "role":rows[0]["role"],
            "unreadMessageCount":unreadMessageCount[0]['count']
            }
    return userDict

def buildDisplayName(userRow):
    displayNameMaxLength = 20
    if userRow["display_name_option"] == 1:
        displayName = userRow["username"]
        # truncate the string to maxlength w/ellipsis if needed
        if len(displayName) > displayNameMaxLength:
            displayName = displayName[:displayNameMaxLength-3] + "..."
    else:
        firstName = userRow["first_name"]
        lastName = userRow["last_name"]
        if len(firstName) + len(lastName) + 1 > displayNameMaxLength:
            if len(firstName) < displayNameMaxLength - 2:
                #this means we could fit the entire first name w/ last initial
                displayName = firstName + " " + lastName[0]
            else:
                #first name is too long, we need to truncate
                displayName = firstName[:displayNameMaxLength-2] + " " + lastName[0]
        else:
            displayName = firstName + " " + lastName
    return displayName

def buildDateTimeString(dateCreated):
    dateTimeString = dateCreated.strftime('%B %d, %Y - %I:%M %p')
    return dateTimeString

def sendVerificationEmail(emailAddress):
    token = s.dumps(emailAddress, salt='email-verify')
    # generate the email for validation
    link = url_for('emailVerify', token=token, _external=True)
    msg = Message("MySupport email verification", sender=("MySupport", "info@bluemontcommunications.com"), recipients=[emailAddress])
    msg.body = "If you recently registered with MySupport, please click the link below to verify your email address. If you did not register with MySupport, please ignore this message and do not click the link. The link is:" + link
    mail.send(msg)

def sendPasswordResetEmail(emailAddress):
    token = s.dumps(emailAddress, salt='password-reset')
    # generate the email for pasword reset
    link = url_for('passwordReset3', token=token, _external=True)
    msg = Message("MySupport pasword reset", sender=("MySupport", "info@bluemontcommunications.com"), recipients=[emailAddress])
    msg.body = "If you recently requested a password reset with MySupport, please click the link below to continue with your reset. If you did not request a password reset with MySupport, please ignore this message and do not click the link. The link is:" + link
    mail.send(msg)

# when signing a user in
def setSessionValues(rows):
    session["id"] = rows[0]["id"]
    session["username"] = rows[0]["username"]
    session["displayNameOption"] = rows[0]["display_name_option"]
    session["role"] = rows[0]["role"]
    session["email"] = rows[0]["email"]
    session["emailConfirmed"] = rows[0]["email_confirmed"]

# build an entire list consisting of a user's db record, usually  for sending to a view
def getUserRows(id):
    dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    dict_cur.execute("""SELECT * FROM users WHERE id = (%s)""", [id])
    rows = [dict(row) for row in dict_cur.fetchall()]
    dict_cur.close()
    return rows

# check image file header data to make sure it's an image file; uses imghdr library
def validate_image(stream):
    header = stream.read(512)
    stream.seek(0)
    format = imghdr.what(None, header)
    if not format:
        return None
    return '.' + (format if format != 'jpeg' else 'jpg')

# get next URLs after profile submit, based on formSource, standalone vs. sequence
def getProfileNextURLs(formSource):
    if formSource == "profile":
        nextURLs = {
            'successURL':'/profile',
            'tryAgainURL':'/profile'
        }
    else:
        ProfileSequenceNumber = int(formSource[-1])
        if ProfileSequenceNumber == 3 or ProfileSequenceNumber == 4:
            # for profile3 and profile4, we want to stay on the page after form submits and updates
            successURL = "profile" + str(ProfileSequenceNumber)
        else:
            successURL = "profile" + str(ProfileSequenceNumber + 1)
        tryAgainURL = "profile" + str(ProfileSequenceNumber)
        nextURLs = {
            'successURL':url_for('index') + successURL,
            'tryAgainURL':url_for('index') + tryAgainURL
        }
    return nextURLs

# make sure an item to be edited or deleted belongs to the logged-in user, so people can't edit other people's stuff via URL args or other mayhem
def checkOwnership(tableName, tableRowID):
    dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    dict_cur.execute("""SELECT user_id FROM %s WHERE id = %s""", [AsIs(tableName), AsIs(tableRowID)])
    ownerRow = [dict(row) for row in dict_cur.fetchall()]
    dict_cur.close()
    ownerID = ownerRow[0]['user_id']
    if session.get("id") != ownerID:
        flash("That item is not yours to edit.", flashStyling("danger"))
        return redirect("/")
    else:
        return True

# build a nested dict with values from db to send to templates for display
def dbSimpleDictBuilder(*args):
    simpleDict = {}
    for arg in args:
        argList = arg.split('+')
        table = argList[0]
        orderBy = argList[1]
        orderType = argList[2]
        # print(f"SELECT * FROM {table} ORDER BY {orderBy} {orderType}")
        # rows = db.execute("SELECT * FROM ? ORDER BY ? ?", table, orderBy, orderType)
        dbExecuteString = 'SELECT * FROM ' + table + ' ORDER BY ' + orderBy + ' ' + orderType
        dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        dict_cur.execute(dbExecuteString)
        rows = [dict(row) for row in dict_cur.fetchall()]
        dict_cur.close()
        simpleDict[table] = rows
    return (simpleDict)

# build a nested dict with values from cities table to send to profile4 template(s) for display
def citiesDictBuilder(zipcode,state,city,county):
    dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    selects4Dict = {'zip':[], 'state':[], 'city':[], 'county':[]}
    matches4Dict = {'state':[], 'city':[], 'county':[]}
    dict_cur.execute("""SELECT DISTINCT state_name FROM cities ORDER BY state_name ASC""")
    alphaStatesList = [dict(row) for row in dict_cur.fetchall()]
    dict_cur.close()
    matchingStatesList = []
    alphaCountiesList = []
    matchingCountiesList = []
    alphaCitiesList = []
    matchingCitiesList = []
    # if we have a zipcode and state, and nothing else, we're handling a case where a zipcode covers multiple states
    if zipcode and state:
    # if zipcode and state and not county and not city:
        dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        dict_cur.execute("""SELECT * FROM cities WHERE zips LIKE (%s)""", ["%"+zipcode+"%"])
        zipsRowsFound = [dict(row) for row in dict_cur.fetchall()]
        dict_cur.close()
        if len(zipsRowsFound) == 0:
            selects4Dict['zip'].append('invalid')
            super4Dict = {'selects':selects4Dict,'matches':matches4Dict}
            return super4Dict
        # zip is valid, move on
        dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        # the following line should not be needed since it appears above the if statement
        # alphaStatesList = cityConnect.execute("SELECT DISTINCT state_name FROM cities ORDER BY state_name ASC")
        dict_cur.execute("""SELECT DISTINCT state_name FROM cities WHERE state_name = (%s)""", [state])
        matchingStatesList = [dict(row) for row in dict_cur.fetchall()]
        dict_cur.execute("""SELECT DISTINCT county_name FROM cities WHERE state_name = (%s) ORDER BY county_name ASC""", [state])
        alphaCountiesList = [dict(row) for row in dict_cur.fetchall()]
        # populate both city and county alpha lists based on state and zip
        dict_cur.execute("""SELECT DISTINCT county_name FROM cities WHERE state_name = (%s) and zips LIKE (%s)  ORDER BY county_name ASC""", [state, "%"+zipcode+"%"])
        matchingCountiesList = [dict(row) for row in dict_cur.fetchall()]
        if len(matchingCountiesList) > 1:
            dict_cur.execute("""SELECT DISTINCT city FROM cities WHERE state_name = (%s) and zips LIKE (%s) ORDER BY city ASC""", [state, "%"+zipcode+"%"])
            matchingCitiesList = [dict(row) for row in dict_cur.fetchall()]
        else:
            dict_cur.execute("""SELECT DISTINCT city FROM cities WHERE state_name = (%s) and county_name = (%s) and zips LIKE (%s) ORDER BY city ASC""", [state, matchingCountiesList[0]['county_name'], "%"+zipcode+"%"])
            matchingCitiesList = [dict(row) for row in dict_cur.fetchall()]
        alphaCitiesList = matchingCitiesList
        dict_cur.close()
    #  if we have only a zipcode, check zipcode for validity, and populate states accordingly
    elif zipcode:
        dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        dict_cur.execute("""SELECT * FROM cities WHERE zips LIKE (%s)""", ["%"+zipcode+"%"])
        zipsRowsFound = [dict(row) for row in dict_cur.fetchall()]
        dict_cur.close()
        if len(zipsRowsFound) == 0:
            selects4Dict['zip'].append('invalid')
            super4Dict = {'selects':selects4Dict,'matches':matches4Dict}
            return super4Dict
        else:
            selects4Dict['zip'].append(zipcode)
            # populate states with all states that match the zip code, ascending
            dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            dict_cur.execute("""SELECT DISTINCT state_name FROM cities WHERE zips LIKE (%s) ORDER BY state_name ASC""", ["%"+zipcode+"%"])
            matchingStatesList = [dict(row) for row in dict_cur.fetchall()]
            # if only one state, populate counties the same way
            if len(matchingStatesList) == 1:
                dict_cur.execute("""SELECT DISTINCT county_name FROM cities WHERE zips LIKE (%s) ORDER BY county_name ASC""", ["%"+zipcode+"%"])
                matchingCountiesList = [dict(row) for row in dict_cur.fetchall()]
                dict_cur.execute("""SELECT DISTINCT county_name FROM cities WHERE state_name = (%s) ORDER BY county_name ASC""", [matchingStatesList[0]['state_name']])
                alphaCountiesList = [dict(row) for row in dict_cur.fetchall()]
            else:
                # if more than one state matches the zip code, don't bother to populate counties or cities
                alphaStatesList = matchingStatesList
            # if only one county, populate cities the same way
            if len(matchingCountiesList) == 1:
                dict_cur.execute("SELECT DISTINCT city FROM cities WHERE zips LIKE (%s) ORDER BY city ASC", ["%"+zipcode+"%"])
                matchingCitiesList = [dict(row) for row in dict_cur.fetchall()]
                dict_cur.execute("""SELECT DISTINCT city FROM cities WHERE county_name = (%s) ORDER BY city ASC""", [matchingCountiesList[0]['county_name']])
                alphaCitiesList = [dict(row) for row in dict_cur.fetchall()]
            else:
                # if more than one county matches the zip code, limit the counties picklist to the matching counties, and don't bother to populate the cities
                alphaCountiesList = matchingCountiesList
            if len(matchingCitiesList) > 1:
                # if more than one city matches the zip code, limit the cities picklist to the matching cities
                alphaCitiesList = matchingCitiesList
            dict_cur.close()
    elif state:
        dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        dict_cur.execute("""SELECT DISTINCT state_name FROM cities WHERE state_name = (%s)""", [state])
        matchingStatesList = [dict(row) for row in dict_cur.fetchall()]
        if (city and county) or (not city and not county):
            # populate both alpha lists based on state
            dict_cur.execute("""SELECT DISTINCT city FROM cities WHERE state_name = (%s) ORDER BY city ASC""", [state])
            alphaCitiesList = [dict(row) for row in dict_cur.fetchall()]
            dict_cur.execute("""SELECT DISTINCT county_name FROM cities WHERE state_name = (%s) ORDER BY county_name ASC""", [state])
            alphaCountiesList = [dict(row) for row in dict_cur.fetchall()]
            # for row in alphaCitiesList:
            #     selects4Dict['city'].append(row['city'])
            # for row in alphaCountiesList:
            #     selects4Dict['county'].append(row['county_name'])
            # update matching lists only if we have both city and county
            if (city and county):
                dict_cur.execute("""SELECT DISTINCT city FROM cities WHERE state_name = (%s) and county_name = (%s) and city = (%s) ORDER BY city ASC""", [state, county, city])
                matchingCitiesList = [dict(row) for row in dict_cur.fetchall()]
                dict_cur.execute("""SELECT DISTINCT county_name FROM cities WHERE state_name = (%s) and county_name = (%s) and city = (%s) ORDER BY county_name ASC""", [state, county, city])
                matchingCountiesList = [dict(row) for row in dict_cur.fetchall()]
        if city:
            # populate cities based on state, populate counties based on city
            dict_cur.execute("""SELECT DISTINCT city FROM cities WHERE state_name = (%s) ORDER BY city ASC""", [state])
            alphaCitiesList = [dict(row) for row in dict_cur.fetchall()]
            dict_cur.execute("""SELECT DISTINCT county_name FROM cities WHERE city = (%s) ORDER BY county_name ASC""", [city])
            alphaCountiesList = [dict(row) for row in dict_cur.fetchall()]
            # for row in alphaCitiesList:
            #     selects4Dict['city'].append(row['city'])
            # for row in alphaCountiesList:
            #     selects4Dict['county'].append(row['county_name'])
            # get county matches based on state and city
            dict_cur.execute("""SELECT DISTINCT county_name FROM cities WHERE state_name = (%s) and city = (%s) ORDER BY county_name ASC""", [state, city])
            matchingCountiesList = [dict(row) for row in dict_cur.fetchall()]
        if county:
            # populate counties based on state, populate cities based on county, and return
            dict_cur.execute("""SELECT DISTINCT county_name FROM cities WHERE state_name = (%s) ORDER BY county_name ASC""", [state])
            alphaCountiesList = [dict(row) for row in dict_cur.fetchall()]
            dict_cur.execute("""SELECT DISTINCT city FROM cities WHERE county_name = (%s) ORDER BY city ASC""", [county])
            alphaCitiesList = [dict(row) for row in dict_cur.fetchall()]
            # for row in alphaCitiesList:
            #     selects4Dict['city'].append(row['city'])
            # for row in alphaCountiesList:
            #     selects4Dict['county'].append(row['county_name'])
            # print (f"selects4Dict: {selects4Dict}")
            # return selects4Dict
        dict_cur.close()
    # else:
    #     # no state
    #     return selects4Dict
    # if county:
        # code here
    # if city
        # code here
    for row in alphaStatesList:
        selects4Dict['state'].append(row['state_name'])
    for row in alphaCountiesList:
        selects4Dict['county'].append(row['county_name'])
    for row in alphaCitiesList:
        selects4Dict['city'].append(row['city'])
    for row in matchingStatesList:
        matches4Dict['state'].append(row['state_name'])
    for row in matchingCountiesList:
        matches4Dict['county'].append(row['county_name'])
    for row in matchingCitiesList:
        matches4Dict['city'].append(row['city'])
    # print (f"in citydict builder, selects4Dict: {selects4Dict}")
    # print (f"in citydictbuilder, matches4Dict: {matches4Dict}")
    super4Dict = {'selects':selects4Dict,'matches':matches4Dict}
    return super4Dict

# select all loved ones, with dict for each one's challenges, from db based on user id
def selectLovedOnes(userID):
    dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    dict_cur.execute("""
    SELECT loved_ones.id, relationships.relationship, genders.gender, ages.age, challenges.challenge
    FROM loved_ones
    LEFT OUTER JOIN relationships on relationships.id = loved_ones.relationship_id
    LEFT OUTER JOIN genders on genders.id = loved_ones.gender_id
    LEFT OUTER JOIN ages on ages.id = loved_ones.age_id
    LEFT OUTER JOIN loved_one_challenge on loved_one_challenge.loved_one_id = loved_ones.id
    LEFT OUTER JOIN challenges on challenges.id = loved_one_challenge.challenge_id
    WHERE user_id = (%s) ORDER BY loved_ones.id ASC, challenges.id ASC
    """, [userID])
    lovedOnes = [dict(row) for row in dict_cur.fetchall()]
    dict_cur.close()
    # check to see if any loved ones have more than one challenge
    tempRows = []
    for row in lovedOnes:
        if len(tempRows) > 0:
            if row['id'] != tempRows[len(tempRows)-1]['id']:
                # first occurrence of this id
                tempRows.append(row)
            else:
                # not the first
                tempRows[len(tempRows)-1]['challenge'] += "!" + row['challenge']
        else:
            tempRows.append(row)
    lovedOnes = tempRows
    for row in lovedOnes:
        if row['challenge']:
            row['challenge'] = row['challenge'].split('!')
    return lovedOnes

# build array of challenges as needed for each loved one
def buildChallengeList(lovedOnes):
    tempRows = []
    for row in lovedOnes:
        if len(tempRows) > 0:
            if row['id'] != tempRows[len(tempRows)-1]['id']:
                # first occurrence of this id
                tempRows.append(row)
            else:
                # not the first
                tempRows[len(tempRows)-1]['challenge'] += "!" + row['challenge']
        else:
            tempRows.append(row)
    lovedOnes = tempRows
    for row in lovedOnes:
        if row['challenge']:
            row['challenge'] = row['challenge'].split('!')
    return lovedOnes

# process returned rows for a message thread; get it ready for display on page
def processMessageThread(threadArrayAll):
    thread1 = []
    tempRows = []
    threadRows = []
    dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    for userID in threadArrayAll:
        # find rows where the specified user is either a sender or recipient
        dict_cur.execute("""
        SELECT * FROM messages
        LEFT JOIN message_recipient on messages.id = message_recipient.message_id
        WHERE (messages.sender_id = (%s) or message_recipient.recipient_id = (%s))
        ORDER BY messages.id ASC, message_recipient.recipient_id ASC
        """, [userID, userID])
        tempRows = [dict(row) for row in dict_cur.fetchall()]
        # print (f"For userID {userID}, tempRows is {tempRows}")
        # thread1.append(tempRows)
        # append each of these returned rows to thread1
        for row in tempRows:
            thread1.append(row)
    dict_cur.close()
    # we should emerge from the loop with lots of rows that need sorting, deduping, etc.
    thread2 = sorted(thread1, key = lambda x: (x['id'], x['recipient_id']))
    # change all recipient IDs to array of ints
    for item in thread2:
        item['recipient_id'] = [item['recipient_id']]
    # print (f"thread2 is {thread2}")
    thread3 = []
    previousID = 0
    # for each message, combine sender and recipient ids into an array of recipient ids
    for item in thread2:
        if item['id'] != previousID:
            # first time for this id
            previousID = item['id']
            thread3.append(item)
            thread3[len(thread3)-1]['recipient_id'].append(item['sender_id'])
        else:
            # not the first for this id
            thread3[len(thread3)-1]['recipient_id'].append(item['recipient_id'][0])
    # dedupe and sort recipient array
    for item in thread3:
        item['recipient_id'] = list(set(item['recipient_id']))
        item['recipient_id'].sort()
    # print (f"thread3 is {thread3}")
    # create new list with only the messages that match the request args list
    for item in thread3:
        if item['recipient_id'] == threadArrayAll:
            threadRows.append(item)
    # add displayName and other display items, based on senderID, for each item
    threadRows = messagePrepForDisplay(threadRows, False)
    dateSortedRows = sorted(threadRows, key=itemgetter('dateTime'))
    # print (f"dateSortedRows is {dateSortedRows}")
    return dateSortedRows

# add user-specific display data and format dateTimeString for a list of messages
def messagePrepForDisplay(rows,condense):
    superMessageList = []
    userRow = []
    displayName = ""
    profileImage = ""
    dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    for item in rows:
        allRecipientsRaw = []
        allRecipientsInts = []
        allDisplayNames = []
        # build array of participants in thread other than logged-in user
        dict_cur.execute("""SELECT DISTINCT recipient_id FROM message_recipient WHERE message_id = (%s)""", [int(item['message_id'])])
        allRecipientsRaw = [dict(row) for row in dict_cur.fetchall()]
        for recipient in allRecipientsRaw:
            allRecipientsInts.append(recipient['recipient_id'])
        allRecipientsInts.append(int(item['sender_id']))
        allRecipientsInts.remove(int(session.get("id")))
        allRecipientsInts.sort()
        # print(f"allRecipientsInts = {allRecipientsInts}")
        # build array of displayNames for those recipients
        for recipient in allRecipientsInts:
            if recipient != int(item['sender_id']):
                recipientRow = getUserRows(recipient)
                recipientDisplayName = buildDisplayName(recipientRow[0])
                allDisplayNames.append(recipientDisplayName)
        allDisplayNamesString = ""
        for name in allDisplayNames:
            allDisplayNamesString += name + ", "
        allDisplayNamesString = allDisplayNamesString[:-2]
        allRecipientsIntsString = ""
        for buddy in allRecipientsInts:
            allRecipientsIntsString += str(buddy) + ","
        allRecipientsIntsString = allRecipientsIntsString[:-1]
        item['allRecipientsInts'] = allRecipientsIntsString
        item['allDisplayNames'] = allDisplayNamesString
        # add a flag for unread message we will use later when combining messages by thread
        if item['read'] == False:
            item['unreadCount'] = 1
        else:
            item['unreadCount'] = 0
        #  add other stuff for display
        userRow = getUserRows(item['sender_id'])
        displayName = buildDisplayName(userRow[0])
        profileImage = userRow[0]['profile_image']
        item['displayName'] = displayName
        item['profileImage'] = profileImage
        # item['dateTime'] = datetime.fromisoformat(str(item['date_created']))
        item['dateTime'] = item['date_created']
        item['dateTimeString'] = buildDateTimeString(item['date_created'])
    # print(f"rows = {rows}")
    dict_cur.close()
    if not condense:
        return rows
    # now we are condensing, so iterate thru rows and copy latest item from each thread into superMessageList and increment unreadCount for each
    matchFound = False
    for item in rows:
        if len(superMessageList) == 0:
            superMessageList.append(item)
        else:
            # get recipientInts from item and check to see if a row already exists with that list in superMessageList; if not, append
            for message in superMessageList:
                matchFound = False
                if message['allRecipientsInts'] == item['allRecipientsInts']:
                    matchFound = True
                    if item['read'] == 0:
                        message['unreadCount'] += 1
                        break
            if not matchFound:
                superMessageList.append(item)
    # print(f"superMessageList = {superMessageList}")
    return superMessageList

#  testing ajax calls; we can delete this when we go to production
def ajaxtest_sub(state_name):
    dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    dict_cur.execute("""SELECT DISTINCT county_name FROM cities WHERE state_name = (%s)""", [state_name])
    countyList = [dict(row) for row in dict_cur.fetchall()]
    dict_cur.close()
    return jsonify(countyList)

def cleanThisHTML(rawHTML):
        cleanHTML = bleach.clean(rawHTML, tags=['a', 'b', 'blockquote', 'em', 'i', 'img','li', 'ol', 'strong', 'ul'], attributes={'a': ['href', 'title'], 'abbr': ['title'], 'acronym': ['title']}, styles=[], protocols=['http', 'https', 'mailto'], strip=False, strip_comments=True)
        return cleanHTML

def getArticleRowsForDisplay(articleID):
    dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        dict_cur.execute("""
            SELECT
            DISTINCT ON (articles.id) articles.id,
            articles.sender_id,
            articles.url,
            articles.title,
            articles.description,
            articles.date_created,
            articles.date_published,
            articles.og_image,
            users.first_name,
            users.last_name,
            users.username,
            users.profile_image,
            users.display_name_option
            FROM articles
            LEFT OUTER JOIN article_challenge on articles.id = article_challenge.article_id
            LEFT OUTER JOIN challenges on challenges.id = article_challenge.challenge_id
            LEFT OUTER JOIN article_age on articles.id = article_age.article_id
            LEFT OUTER JOIN ages on ages.id = article_age.age_id
            LEFT OUTER JOIN article_gender on articles.id = article_gender.article_id
            LEFT OUTER JOIN genders on genders.id = article_gender.gender_id
            LEFT OUTER JOIN users on users.id = articles.sender_id
            WHERE articles.id = %s
            ORDER BY articles.id
        """, [int(articleID)])
        articleRows = [dict(row) for row in dict_cur.fetchall()]
        # print(f"Records retrieved: {len(articleRows)}")
        # print("Preliminary article rows:")
        # print(articleRows)
        for row in articleRows:
            # get challenge ids as array and add them to each row
            dict_cur.execute("""
            SELECT article_id, 
            array_agg(challenge_id) AS challenge_ids
            FROM article_challenge
            WHERE article_id = %s
            GROUP BY article_id""",[row['id']])
            challenge_ids = [dict(row) for row in dict_cur.fetchall()]
            if len(challenge_ids) != 0:
                challenge_ids = challenge_ids[0]['challenge_ids']
                # print(f"challenge_ids to be added: {challenge_ids}")
                row['challenge_ids'] = challenge_ids
                # get challenges as strings and add them, comma-separated, to one big string
                challenge_ids_string = ','.join(map(str, challenge_ids))
                dict_cur.execute("""SELECT string_agg(challenge,',') AS my_challenges FROM challenges WHERE id IN (%s)""",[AsIs(challenge_ids_string)])
                challenges = dict_cur.fetchone()['my_challenges']
                # print (f"challenges to be added: {challenges}")
                row['challenges'] = challenges
            # get age ids as array and add them to each row
            dict_cur.execute("""
            SELECT article_id, 
            array_agg(age_id) AS age_ids
            FROM article_age
            WHERE article_id = %s
            GROUP BY article_id""",[row['id']])
            age_ids = [dict(row) for row in dict_cur.fetchall()]
            if len(age_ids) != 0:
                age_ids = age_ids[0]['age_ids']
                # print(f"age_ids to be added: {age_ids}")
                row['age_ids'] = age_ids
                # get ages as strings and add them, comma-separated, to one big string
                age_ids_string = ','.join(map(str, age_ids))
                dict_cur.execute("""SELECT string_agg(age,',') AS my_ages FROM ages WHERE id IN (%s)""",[AsIs(age_ids_string)])
                ages = dict_cur.fetchone()['my_ages']
                # print (f"ages to be added: {ages}")
                row['ages'] = ages
            # get gender ids as array and add them to each row
            dict_cur.execute("""
            SELECT article_id, 
            array_agg(gender_id) AS gender_ids
            FROM article_gender
            WHERE article_id = %s
            GROUP BY article_id""",[row['id']])
            gender_ids = [dict(row) for row in dict_cur.fetchall()]
            if len(gender_ids) != 0:
                gender_ids = gender_ids[0]['gender_ids']
                # print(f"gender_ids to be added: {gender_ids}")
                row['gender_ids'] = gender_ids
                # get genders as strings and add them, comma-separated, to one big string
                gender_ids_string = ','.join(map(str, gender_ids))
                dict_cur.execute("""SELECT string_agg(gender,',') AS my_genders FROM genders WHERE id IN (%s)""",[AsIs(gender_ids_string)])
                genders = dict_cur.fetchone()['my_genders']
                # print (f"genders to be added: {genders}")
                row['genders'] = genders
        # print("Enhanced article rows:")
        # print(articleRows)
    except Exception as error:
        print ("Oops! An exception has occurred:", error)
        print ("Exception TYPE:", type(error))
        dict_cur.execute("""ROLLBACK""")
        abort(500)
    else:
        dict_cur.execute("""COMMIT""")
    dict_cur.close()
    articleRows[0]['displayName'] = buildDisplayName(articleRows[0])
    articleRows[0]['dateTimeString'] = buildDateTimeString(articleRows[0]['date_created'])
    articleRows[0]['publishedDateTimeString'] = buildDateTimeString(articleRows[0]['date_published'])
    # print("Article rows:")
    # print (articleRows)
    return articleRows

def getArticleCommentRowsForDisplay(articleID):
    dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    dict_cur.execute("""
        SELECT comments.id, comments.text, comments.sender_id, comments.date_created, users.first_name, users.last_name, users.username, users.display_name_option, users.profile_image
        FROM comments
        LEFT OUTER JOIN users on comments.sender_id = users.id
        WHERE comments.article_id = (%s)
        ORDER BY comments.date_created ASC
    """, [int(articleID)])
    articleCommentRows = [dict(row) for row in dict_cur.fetchall()]
    dict_cur.close()
    for row in articleCommentRows:
        row['displayName'] = buildDisplayName(row)
        row['dateTimeString'] = buildDateTimeString(row['date_created'])
    return articleCommentRows

def getDiscussionRowsForDisplay(discussionID):
    dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        dict_cur.execute("""
            SELECT
            discussions.id,
            discussions.sender_id,
            discussions.subject,
            discussions.text,
            discussions.date_created,
            users.first_name,
            users.last_name,
            users.username,
            users.profile_image,
            users.display_name_option
            FROM discussions
            LEFT JOIN discussion_challenge on discussions.id = discussion_challenge.discussion_id
            LEFT JOIN challenges on challenges.id = discussion_challenge.challenge_id
            LEFT JOIN discussion_age on discussions.id = discussion_age.discussion_id
            LEFT JOIN ages on ages.id = discussion_age.age_id
            LEFT JOIN discussion_gender on discussions.id = discussion_gender.discussion_id
            LEFT JOIN genders on genders.id = discussion_gender.gender_id
            LEFT JOIN users on users.id = discussions.sender_id
            WHERE discussions.id = (%s)
        """, [discussionID])
        discussionRows = [dict(row) for row in dict_cur.fetchall()]
        # print(f"Records retrieved: {len(discussionRows)}")
        # print("Preliminary discussion rows:")
        # print(discussionRows)
        for row in discussionRows:
            # get challenge ids as array and add them to each row
            dict_cur.execute("""
            SELECT discussion_id, 
            array_agg(challenge_id) AS challenge_ids
            FROM discussion_challenge
            WHERE discussion_id = %s
            GROUP BY discussion_id""",[row['id']])
            challenge_ids = [dict(row) for row in dict_cur.fetchall()]
            if len(challenge_ids) != 0:
                challenge_ids = challenge_ids[0]['challenge_ids']
                row['challenge_ids'] = challenge_ids
                # get challenges as strings and add them, comma-separated, to one big string
                challenge_ids_string = ','.join(map(str, challenge_ids))
                dict_cur.execute("""SELECT string_agg(challenge,',') AS my_challenges FROM challenges WHERE id IN (%s)""",[AsIs(challenge_ids_string)])
                challenges = dict_cur.fetchone()['my_challenges']
                row['challenges'] = challenges
            # get age ids as array and add them to each row
            dict_cur.execute("""
            SELECT discussion_id, 
            array_agg(age_id) AS age_ids
            FROM discussion_age
            WHERE discussion_id = %s
            GROUP BY discussion_id""",[row['id']])
            age_ids = [dict(row) for row in dict_cur.fetchall()]
            if len(age_ids) != 0:
                age_ids = age_ids[0]['age_ids']
                row['age_ids'] = age_ids
                # get ages as strings and add them, comma-separated, to one big string
                age_ids_string = ','.join(map(str, age_ids))
                dict_cur.execute("""SELECT string_agg(age,',') AS my_ages FROM ages WHERE id IN (%s)""",[AsIs(age_ids_string)])
                ages = dict_cur.fetchone()['my_ages']
                row['ages'] = ages
            # get gender ids as array and add them to each row
            dict_cur.execute("""
            SELECT discussion_id, 
            array_agg(gender_id) AS gender_ids
            FROM discussion_gender
            WHERE discussion_id = %s
            GROUP BY discussion_id""",[row['id']])
            gender_ids = [dict(row) for row in dict_cur.fetchall()]
            if len(gender_ids) != 0:
                gender_ids = gender_ids[0]['gender_ids']
                row['gender_ids'] = gender_ids
                # get genders as strings and add them, comma-separated, to one big string
                gender_ids_string = ','.join(map(str, gender_ids))
                dict_cur.execute("""SELECT string_agg(gender,',') AS my_genders FROM genders WHERE id IN (%s)""",[AsIs(gender_ids_string)])
                genders = dict_cur.fetchone()['my_genders']
                row['genders'] = genders
        # print("Enhanced discussion rows:")
        # print(discussionRows)
    except Exception as error:
        print ("Oops! An exception has occurred:", error)
        print ("Exception TYPE:", type(error))
        dict_cur.execute("""ROLLBACK""")
        abort(500)
    else:
        dict_cur.execute("""COMMIT""")
    dict_cur.close()
    discussionRows[0]['displayName'] = buildDisplayName(discussionRows[0])
    discussionRows[0]['dateTimeString'] = buildDateTimeString(discussionRows[0]['date_created'])
    return discussionRows

def getDiscussionCommentRowsForDisplay(discussionID):
    dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    dict_cur.execute("""
        SELECT comments.id, comments.text, comments.sender_id, comments.date_created, users.first_name, users.last_name, users.username, users.display_name_option, users.profile_image
        FROM comments
        LEFT OUTER JOIN users on comments.sender_id = users.id
        WHERE comments.discussion_id = (%s)
        ORDER BY comments.date_created ASC
    """, [int(discussionID)])
    discussionCommentRows = [dict(row) for row in dict_cur.fetchall()]
    dict_cur.close()
    for row in discussionCommentRows:
        row['displayName'] = buildDisplayName(row)
        row['dateTimeString'] = buildDateTimeString(row['date_created'])
    return discussionCommentRows

def getTextContentFromHTML(HTMLstring):
    soup = BeautifulSoup(HTMLstring, 'html.parser')
    textContent = soup.get_text(strip=True)
    return textContent

def getFirstImageFromHTML(HTMLstring):
    # Using a tag name as an attribute will give you only the first tag by that name:
    # soup.a
    # <a class="sister" href="http://example.com/elsie" id="link1">Elsie</a>
    soup = BeautifulSoup(HTMLstring, 'html.parser')
    imageTagCode = soup.img
    if imageTagCode:
        imageTagSrc = soup.img['src']
    else:
        imageTagSrc = None
    imageTagList = [imageTagCode,imageTagSrc]
    return imageTagList

def checkDateFormat (string):
    # parse a string to see if the first 10 characters are a valid date informat YYYY-MM-DD
    dateFormat = False
    firstTenChars = string[:10]
    try:
        datetime.strptime(firstTenChars, '%Y-%m-%d')
    except ValueError:
        return dateFormat
    dateFormat = True
    return dateFormat

# ========= END OTHER HANDY FUNCTIONS ============

if __name__ == "__main__":
    app.run(host='0.0.0.0')