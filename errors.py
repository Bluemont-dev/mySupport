from flask import render_template, url_for
# from app import app, db

def errorView(userDict,title,text,buttonLabel,nextRoute):
    errorView = {}
    errorView["title"] = title
    errorView["text"] = text
    errorView["buttonLabel"] = buttonLabel
    errorView["nextRoute"] = url_for(nextRoute)
    return render_template ("error.html", errorView = errorView, userDict = userDict)

def flashStyling(category):
    # used along with the Flask flash function; create a string we can pass to layout.html for boostrap class styling of alert messages by category, e.g. info, success, danger, etc.
    return "alert alert-" + category + " border text-center"