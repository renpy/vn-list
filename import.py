from app import app, db, views, models
from sqlalchemy import Integer, String, Boolean, Date, Text, DateTime, SmallInteger, and_, or_, desc
from flask import g #,render_template, request, session, redirect, url_for, abort, flash, send_from_directory

import psycopg2, sys

con = None
try:
    print "Importing games."
    con = psycopg2.connect(database='renaius', user='postgres') 
    cur = con.cursor()
    cur.execute('SELECT * FROM games_game')
    rows = cur.fetchall()
    i = 1
    
    #rows = []
    
    for game in rows:
        # print game
    
    #print game

        approved=game[0]
        temp_tag=game[1]
        slug=temp_tag
        game_title=game[2]
        maker=game[3]
        developer_name=maker
        creator_type='person'
        homepage_link_url=game[4]
        description=game[5]
        added=game[6]
        modified=game[7]
        rating=game[8]
        if rating == "all ages":
            age_rating_id = 1
        if rating == "ages 13+":
            age_rating_id = 2
        if rating == "ages 16+":
            age_rating_id = 3
        if rating == "ages 18+":
            age_rating_id = 4
        temp_playtime=game[9]
        #playtime=...
        playtime=0
        words=game[10]
        #words_estimate=...
        words_estimate=words
        
        
        default_screenshot_id=game[11]
        release_date=game[12]
        renaius=game[13]
        listed_on=2 #games.renpy.org only
        if renaius:
            listed_on=3 #both
        renpy_release_date=game[14]
     
        #user_id for game
        cur2 = con.cursor()
        cur2.execute("SELECT * FROM games_game_owner WHERE game_id='" + temp_tag + "'")
        owners = cur2.fetchall()
        for owner in owners:
            user_id = owner[2]

        game = models.Game(game_title=game_title, slug=slug, maker = maker, description = description, age_rating_id=age_rating_id, words = words, words_estimate=words_estimate, playtime = playtime, developer_id=1, user_id=user_id, approved=approved, listed_on=listed_on, temp_playtime=temp_playtime, temp_tag=temp_tag, created=added)
        db.session.add(game)
        db.session.commit()

        #screenshots
        cur2 = con.cursor()
        cur2.execute("SELECT * FROM games_screenshot WHERE game_id='" + temp_tag + "'")
        screenshots = cur2.fetchall()
        for scr in screenshots:
            is_thumb=False
            if default_screenshot_id==scr[0]:
                is_thumb=True
            screens = models.Screenshot(game_id=game.id, filename=scr[3], approved=scr[1], is_thumb=is_thumb)
            db.session.add(screens)
        
        #save developer, if needed
        developer = models.Developer.query.filter(models.Developer.name==developer_name).first()
        if not developer:
            if creator_type=='person':
                type=1
                person = models.Person('')
                db.session.add(person)
                db.session.commit()
                developer = models.Developer (developer_name, type, user_id, person_id=person.id)
            if creator_type=='group':
                type=2
                group = models.Group('')
                db.session.add(group)
                db.session.commit()
                developer = models.Developer (developer_name, type, user_id, group_id=group.id)
            db.session.add(developer)

        #save homepage link to link_game table:
        links_game=models.LinkGame(game_id=game.id, url=homepage_link_url, name = 'Home Page', link_type_id = '1')
        db.session.add(links_game)

        db.session.commit()
        game.developer_id = developer.id
        db.session.commit()
            
        #save the categories to category_game:
        cur2 = con.cursor()
        cur2.execute("SELECT * FROM games_game_categories WHERE game_id='" + temp_tag + "'")
        cats = cur2.fetchall()
        for cat in cats:
            #print cat[2]
            try:
                category_id = models.Category.query.filter(models.Category.slug==cat[2]).one()
            except:
                print cat[2]
            categories_game = models.CategoryGame(game_id=game.id, category_id=category_id.id)
            db.session.add(categories_game)

        cur2 = con.cursor()
        cur2.execute("SELECT * FROM games_release WHERE game_id='" + temp_tag + "'")
        releases = cur2.fetchall()
        for rel in releases:
    #        print rel
            cur3 = con.cursor()
            cur3.execute("SELECT * FROM games_release_owner WHERE release_id=" + str(rel[0]))
            rel_users = cur3.fetchall()
            for rel_user_id in rel_users:
                #print rel_user_id
                rel_user_id = rel_user_id[2]

            if rel[9] == "Ren'Py":
                engine_id = 1
            if rel[9] == "Novelty":
                engine_id = 2
            if rel[9] == "Flash":
                engine_id = 3
            if rel[9] == "Other":
                engine_id = 4
                
            ################
            #game_id=game.id
            #game = db.session.query(models.Game).filter(models.Game.id==game_id).one()            
            if ((game.listed_on==2) or (game.listed_on==3)) and (not (engine_id == 1)):
                game.listed_on=1
                
            release_date=rel[3]
            
 #           from datetime import datetime
#            mydate = datetime.strptime(release_date,'%m/%d/%Y')
            if release_date.year < 1900:
            
                release_date = release_date.replace(year=1901)
#                release_date=mydate.strftime('%d %B %Y')
            
            release = models.Release(game_id=game.id, release_date=release_date, release_version=rel[4], engine_id=engine_id, release_description = rel[10], engine_version = rel[8], user_id=rel_user_id, approved=rel[1])
            db.session.add(release)
            db.session.commit()
            
            if rel[5]:
                db.session.add(models.PlatformRelease(release_id=release.id, platform_id=1))
            if rel[6]:
                db.session.add(models.PlatformRelease(release_id=release.id, platform_id=2))
            if rel[7]:
                db.session.add(models.PlatformRelease(release_id=release.id, platform_id=3))
            if (not rel[5]) and (not rel[6]) and (not rel[7]):
                db.session.add(models.PlatformRelease(release_id=release.id, platform_id=4))
            
            db.session.commit()
        
            cur3 = con.cursor()
            cur3.execute("SELECT * FROM games_file WHERE release_id=" + str(rel[0]))
            game_files = cur3.fetchall()
            for games_file in game_files:
                file = models.File(release_id=release.id, filename=games_file[3][6:], description=games_file[4], approved=games_file[2])
                db.session.add(file)
                #db.session.commit()
        
        db.session.commit()
        if i%100==0:
            print "*"
        i += 1
        
    print "Importing users."
#    cur.execute('SELECT * FROM auth_user LIMIT 10')
    cur.execute('SELECT * FROM auth_user')    
    ROLE_USER = 0
    ROLE_ADMIN = 1
    ROLE_SUPERUSER = 2
    USER_STATUS_ACTIVE = 1
    USER_STATUS_BANNED = 0

    users = cur.fetchall()
    i = 1
    for user in users:
        status = USER_STATUS_BANNED
        role = ROLE_USER
        if user[6]:
            role = ROLE_ADMIN
        if user[8]:
            role = ROLE_SUPERUSER
        if user[7]:
            status = USER_STATUS_ACTIVE
        usr=models.UserAccount(username=user[1], password=user[5], email=user[4], role=role, status=status, last_login=user[9], date_joined=user[10])
        usr.id=user[0]
        db.session.add(usr)
        #print user
        if i%100==0:
            print i
        i += 1
    db.session.commit()

    # fix for a problem with user id autoincrement not working propery after the import
    cur4 = con.cursor()
    cur4.execute("SELECT setval('user_account_id_seq', (SELECT MAX(id) FROM user_account)+1)"
    
except psycopg2.DatabaseError, e:
    print 'Error %s' % e    
    sys.exit(1)
finally:
    if con:
        con.close()
        print "All done."