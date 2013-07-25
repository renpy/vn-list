from app import app, db, views, models
from sqlalchemy import Integer, String, Boolean, Date, Text, DateTime, SmallInteger, and_, or_, desc
from flask import g #,render_template, request, session, redirect, url_for, abort, flash, send_from_directory
import sys
games = db.session.query(models.Game).all()

print "---------------------------------------------------------------"
i=1
for game in games:
    output=False
    playtime = 0
    hours=False
    minutes=False
    per_path=False
    str1 = game.temp_playtime
    if str1:
        str1 = str1.replace("-", " - ")
        str1 = str1.lower()
        str1 = str1.replace("~", "")
        str1 = str1.replace("+", "")
        str1 = str1.replace("<", "")
        str1 = str1.replace(">", "")
        if str1.find("min")>0:
            minutes=True
        if str1.find("hour")>0 or str1.find("hrs")>0 or str1.find("hr.")>0:
            hours=True

        if str1.find("path")>0 or str1.find("playthrough")>0 or str1.find("ending")>0 or str1.find("route")>0:
            per_path=True
        if minutes and hours:
            per_path=True

        if (minutes or hours) and (not per_path):
            playtime = [int(s) for s in str1.split() if s.isdigit()]
            if len(playtime)==1:
                playtime = playtime[0]
            elif len(playtime)==2:
                playtime = round(float((playtime[0]+playtime[1]))/2,1)
            if hours:
                playtime = playtime * 60
            
            #sys.stdout.write(playtime)
            try:
                playtime = int(playtime)
                if output:
                    sys.stdout.write(str1 + "->")
                    print playtime
            except:
                #print "?? " + str1 + "   / " +  str(game.id) + ": "# + game.game_title
                pass
            
            #print str1 + "->" + playtime
        else:
            if str1.isdigit():
                playtime = int(str1)
                if output:
                    sys.stdout.write(str1 + "->")
                    print playtime
            else:
                #print "!! " + str1 + "   / " +  str(game.id) + ": "# + game.game_title    
                playtime = str1

    try:
        playtime = int(playtime)
        game.playtime = playtime
    except:
        game.playtime = -1
        try:
            print "!! " + str1 + "   / " +  str(game.id) + ": " + game.game_title    
        except:
            print "!! " + str1 + "   / " +  str(game.id) + ": "
    if game.words == 0 or not game.words:
        game.words_estimate = game.playtime*200
    else:
        game.words_estimate = game.words
            
    i+=1
    if i>1000:
        break

db.session.commit()
print "Done."
