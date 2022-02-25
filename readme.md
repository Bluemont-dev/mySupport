# MySupport
#### Description:
MySupport is an online community powered by a web-based application. The application is written in Python, uses Flask as the web server, and integrates with a Postgtresql database.

The main purposes of MySupport are to help connect people who share a common struggle, such as mental illness, substance abuse, developmental disabilities, domestic abuse, etc. It is intended to supplement an in-person support group, but it also could be used by those who do not or cannot attend in person.

## Key Features for Users of MySupport

### Profile / Find People
Users can share as much or as little as they wish about themselves and their challenges, and they can look for others in the community based on those same demographics.

### Messaging
Users can send each other messages on a one-to-one or group basis. Users see a count of unread messages when they log into the site.

### Discussions
Users can start a discussion with a subject line and text content. These can be formatted with simple WYSIWYG editing buttons, and the app will "sanitize" the submitted content to make sure no malicious HTML code was submitted. Readers of an article can comment.

### Articles
Users can share an online article or blog post of interest to the community and get comments in response. They can start with just the URL of the external content, and a Python web scraper will fetch the title, date published, description and featured image, if these items are appropriately meta-tagged. If not, the user will be prompted to provide this information before sharing the article.

* *A note on authentication: to make MySupport inviting for users who are reluctant to join in, all of the content is available to non-authenticated (non-logged-in) users, except for messages. However, users must be logged in to comment, or to send and receive messages.* *

## Structure and Design of MySupport

Users interact with the site using a collection of HTML templates with corresponding Javascript (\*.js) and CSS (\*.css) files for each. The templates fall into 6 groups:
- Sign In / Register / Verify Email
- Profile
- People
- Articles
- Discussions
- Messages

Bootstrap 5 is the design framework for MySupport.

The primary application code is in application.py; some functions are stored in helpers.py.

The database includes a large number of tables due to the many content types and the tags that can be assigned to them. For example, the users table contains basic information about each user, while the messages, articles and discussions table contain the content that is published by those users. But the app uses many JOIN tables because of the many-to-many relationships involving comments, a user's loved ones, and the demographic data shared anonymously about those loved ones, such as relationship, age, gender, and the challenges they live with.

Some key site features and the Python libraries that power them are:

| Feature                                             | Library                  |
| --------------------------------------------------- | ------------------------ |
| Authentication and password hashing                 | werkzeug security        |
| Sending emails for verification or password reset   | flask_mail               |
| Expiring tokens for email verification              | itsdangerous             |
| Date and time manipulation and formatting           | datetime                 |
| Cleaning up user-submitted HTML                     | bleach                   |
| Scraping external URLs for selected metadata        | BeautifulSoup and urllib |
| Checking user-selected image files to verify format | imghdr                   |

Sensitive data are stored as environmental variables in a \*.env file, excluded from git.

## Future enhancements

Features I would like to add include:
- **Search** -- a full-text search field available as part of the global navigation, able to search all content by keywords or phrases.
- **Events Calendar** -- Support groups who meet in person would be able to share the dates of their upcoming meetings, along with relevant webinars, advocacy opportunities, etc.  This could be easily integrated with a third-party library rather than build a calendar tool from scratch.
- **Tagging by topic** -- MySupport has a simple taxonomy based on the relationships, ages, genders and challenges faced by community members and their loved ones.  But a more robust tagging system is needed based on the topics of the articles, discussions, and events calendar.  Topics such as employment, housing, medications and health insurance, and legal issues would among the things a user should be able to search for, sort by, or filter against.

## Difficulties
Due to limited experience with Python, I was unable to figure out how to break my main file (application.py) into smaller modules. As a result, this file has over 2,000 lines of code, and is a bit unwieldy to edit. I will definitely learn how to refactor the code if I move forward with this as a production-ready offering.

