from flask.ext.mail import Message
from app import app, mail
from config import ADMINS, DOMAIN_ID
from config_more import DOMAIN_URLS
DOMAIN_URL=DOMAIN_URLS[DOMAIN_ID]

from app import db
from app import models

games = db.session.query(models.Game)
games = games.filter(models.Game.approved==False)
games = games.all()

releases = db.session.query(models.Release, models.Game)
releases = releases.join(models.Game, models.Release.game_id==models.Game.id)
releases = releases.filter(models.Release.approved==False)
releases = releases.distinct(models.Game.id)
releases = releases.all()

screenshots = db.session.query(models.Screenshot, models.Game)
screenshots = screenshots.join(models.Game, models.Screenshot.game_id==models.Game.id)
screenshots = screenshots.filter(models.Screenshot.approved==False)
screenshots = screenshots.distinct(models.Game.id)
screenshots = screenshots.all()

files = db.session.query(models.File, models.Game)
files = files.join(models.Release, models.File.release_id==models.Release.id)
files = files.join(models.Game, models.Release.game_id==models.Game.id)
files = files.filter(models.File.approved==False)
files = files.distinct(models.Game.id)
files = files.all()

# print ("Games: " + str(len(games)))
# for game in games:
#     print (game.game_title)
#
# print ("--------------")
# print ("Releases: " + str(len(releases)))
# for release in releases:
#     print (release[1].game_title)
#
# print ("--------------")
# print ("Files: " + str(len(files)))
# for file in files:
#     print (file[1].game_title)
#
# print ("--------------")
# print ("Screenshots: " + str(len(screenshots)))
# for screenshot in screenshots:
#     print (screenshot[1].game_title)

msg = Message('Dirty Pages', sender = ADMINS[0], recipients = ADMINS)
msg.body = ""
msg.html = ""

body = "Pages that require your attention:"
msg.body += body + "\n\n";
msg.html += "<h1>" + body + "</h1>"

body = "Games:"
msg.body += body + "\n";
msg.html += "<p>" + body + "</p>"

for game in games:
    title = game.game_title
    url = DOMAIN_URL + "game/" + game.slug
    msg.body += title + " " + url + "\n"
    msg.html += '<p><a href="' + url + '">' + title + "</a></p>"

body = "---------------\n"
msg.body += body + "\n";
msg.html += "<hr/>"

body = "Releases:"
msg.body += body + "\n";
msg.html += "<p>" + body + "</p>"

for release in releases:
    title = release[1].game_title
    url = DOMAIN_URL + "game/" + release[1].slug
    msg.body += title + " " + url + "\n"
    msg.html += '<p><a href="' + url + '">' + title + "</a></p>"

body = "---------------\n"
msg.body += body + "\n";
msg.html += "<hr/>"

body = "Files:\n"
msg.body += body + "\n";
msg.html += "<p>" + body + "</p>"

for file in files:
    title = file[1].game_title
    url = DOMAIN_URL + "game/" + file[1].slug
    msg.body += title + " " + url + "\n"
    msg.html += '<p><a href="' + url + '">' + title + "</a></p>"


body = "---------------\n"
msg.body += body + "\n";
msg.html += "<hr/>"

body = "Screenshots:\n"
msg.body += body + "\n";
msg.html += "<p>" + body + "</p>"

for screenshot in screenshots:
    title = screenshot[1].game_title
    url = DOMAIN_URL + "game/" + screenshot[1].slug
    msg.body += title + " " + url + "\n"
    msg.html += '<p><a href="' + url + '">' + title + "</a></p>"

with app.app_context():
    mail.send(msg)
