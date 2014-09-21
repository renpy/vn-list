from app import app, db, lm, oid
from flask import render_template, request, session, redirect, url_for, abort, flash, g, send_from_directory



from PIL import Image
#import Image
import os, sys, string, random, datetime, uuid, math, shutil, hashlib, random, time, os.path
import socket, json
import re
from datetime import date, timedelta
from werkzeug import secure_filename
from sqlalchemy.orm import sessionmaker
from flask.ext.login import LoginManager, login_user, logout_user, current_user, login_required
from models import UserAccount, Category, CategoryGroup, CategoryGame, Engine, LinkType, LinkGame, Platform, PlatformRelease, Release, Game, Screenshot, File, Developer, Group, Person, ROLE_USER, ROLE_ADMIN
from config import ADMINS
from config import DOMAIN_ID, RENAI_ARCHIVE_ID, RENPY_LIST_ID
from config_more import START_YEAR, DOMAIN_TITLE, DOMAIN_URLS, DOMAIN_TITLES, DOMAIN_NAMES, START_YEARS
from sqlalchemy import Table, and_, or_, desc
from forms import LoginForm, LoginFormOid, SignupForm, PassResetForm, NewPasswordForm, AdminGameApproveForm, UploadForm, AccountForm, ChangePasswordForm, GameForm, GameFormEdit, ReleaseForm

def allowed_file_img(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS_IMG']

#def allowed_file(filename):
#    return '.' in filename and filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

@lm.user_loader
def load_user(id):
    return UserAccount.query.get(int(id))

@app.before_request
def before_request():
    g.user = current_user

def now():
    return datetime.datetime.utcnow()

####################
def site_data():
    data=dict(title = DOMAIN_TITLE, domain_id=DOMAIN_ID, renai_archive_id=RENAI_ARCHIVE_ID, renpy_list_id=RENPY_LIST_ID, domain_urls=DOMAIN_URLS, titles=DOMAIN_TITLES, start_year=START_YEAR)
    if 'DOMAIN_ID' in session:
        if session['DOMAIN_ID']==str(RENAI_ARCHIVE_ID):
            domain_id=RENAI_ARCHIVE_ID
        if session['DOMAIN_ID']==str(RENPY_LIST_ID):
            domain_id=RENPY_LIST_ID
        #DOMAIN_NAME=DOMAIN_NAMES[domain_id]
        title=DOMAIN_TITLES[domain_id]
        start_year=START_YEARS[domain_id]
        data=dict(title = title, domain_id=domain_id, renai_archive_id=RENAI_ARCHIVE_ID, renpy_list_id=RENPY_LIST_ID, domain_urls=DOMAIN_URLS, titles=DOMAIN_TITLES, start_year=start_year)
    return data

def return_cats(show_in_navigation = False): #False means no filtering (show all categories)
    show_in_nav = show_in_navigation
    res = []
    groups = CategoryGroup.query
    if show_in_navigation:
        groups = groups.filter(CategoryGroup.show_in_navigation==show_in_navigation)
    groups = groups.all()
    for group in groups:
        categories_sql = group.categories_sql
        if show_in_navigation:
            categories_sql = categories_sql.filter(Category.show_in_navigation==show_in_navigation)
        categories = categories_sql.all()
        group.categories = categories
        res.append(group)
    return res

def return_navigation():
    cats = return_cats(True)
    group_name = dict(name = 'By Name')
    group_name['side_only'] = True
    group_name['categories'] = []
    for item in string.ascii_uppercase:
        group_name['categories'].append(dict(slug=item,name=item))
    cats.insert(0, group_name)
    group_year = dict(name = 'By Year')
    group_year['side_only'] = True
    group_year['categories'] = []
    end_year = date.today().year+1
    site_data_var = site_data()
    start_year = site_data_var['start_year']
    for item in  reversed(range(start_year, end_year)):
        item=str(item)
        group_year['categories'].append(dict(slug=item,name=item))
    cats.insert(0, group_year)

    group_other = dict(name = 'Other')
    group_other['categories'] = [dict(slug='macintosh',name='Macintosh'), dict(slug='linux',name='Linux'), dict(slug='all',name='All Games'), dict(slug='quick',name='All Games (brief)'), dict(slug='no_screenshot',name='No Screenshot'), dict(slug='unapproved',name='Unapproved')]
    cats.append(group_other)
    return cats

def return_games(category=None, order=None, game_slug=None, approved=True, platform=None, year=None, letter=None, search=None, no_screenshot=False):
    site_data_var = site_data()
    games = db.session.query(Game)
    if category and not category=='all': #category listing
        category_id = db.session.query(Category.id).filter(Category.slug==category).one().id
        games = games.join(CategoryGame).filter(CategoryGame.category_id==category_id)
    if game_slug: #single game listing
        games = games.filter(Game.slug==game_slug)
    else:
        if approved:
            if site_data_var['domain_id'] == site_data_var['renai_archive_id']:
                games = games.filter(and_(or_(Game.listed_on==site_data_var['domain_id'], Game.listed_on==site_data_var['renai_archive_id']+site_data_var['renpy_list_id']), Game.approved==approved))
                #.having(count(Game.releases.id) > 2) #, Game.releases.files.count() > 0)



            else:
                games = games.filter(and_(or_(Game.listed_on==site_data_var['domain_id'], Game.listed_on==site_data_var['renai_archive_id']+site_data_var['renpy_list_id']), Game.approved==approved))
        else:
            games = games.filter(Game.approved==approved)
    if letter:
        games = games.filter(Game.game_title.op('ilike')(letter+"%"))
    if search:
        search = '%' + search + '%'
        games = games.filter(or_(Game.game_title.op('ilike')(search), Game.description.op('ilike')(search)))
    if year:
        games = games.filter(Game.releases.any(Release.release_date.between(year + '-01-01', year + '-12-31')))
    if platform:
        games = games.filter(Game.releases.any(Release.platforms.any(PlatformRelease.platform_id.in_([platform]))))
    if no_screenshot:
        games = games.filter(Game.screenshots==None)

    if order:
        if order == "title":
            games = games.order_by(Game.game_title)
        if order == "date":
            games = games.join(Release)
            games = games.order_by(Release.release_date)
        if order == "words":
            games = games.order_by(Game.words_estimate)

    if game_slug:
        games = games.one()
    else:
        games = games.all()
    return games

def select_random_games(num):
    site_data_var=site_data()
    screenshots = Screenshot.query.join(Game)
    screenshots = screenshots.filter(and_(or_(Game.listed_on==site_data_var['domain_id'], Game.listed_on==site_data_var['renai_archive_id']+site_data_var['renpy_list_id']), Game.approved==True))
    screenshots = screenshots.filter(Screenshot.is_thumb==True)
    num_screenshots = screenshots.count() #in case there is less screenshots in the db than required
    if num > num_screenshots:
        num = num_screenshots
    screenshots = screenshots.all()
    result = random.sample(screenshots, num)
    screenshots = []
    for res in result:
        game = Game.query.filter(Game.id==res.game_id).one()
        res.game_title = game.game_title
        res.slug = game.slug
        res.developer = game.developer
        res.categories = game.categories
        res.playtime = game.playtime
        res.words = game.words
        res.age_rating = game.age_rating


        screenshots.append(res)
    return screenshots

def select_recent_games(num):
    site_data_var=site_data()
    result = Game.query.join(Release)
    result = result.filter(and_(or_(Game.listed_on==site_data_var['domain_id'], Game.listed_on==site_data_var['renai_archive_id']+site_data_var['renpy_list_id']), Game.approved==True))
#    result = result.add_columns(Release.release_date, Game.game_title, Game.slug, Game.screenshot, Game.description)
    result = result.order_by(Game.id.desc()).limit(num+1)
    return result

@app.route('/')
def index():
    screenshots = select_random_games(5)
    recent_games = select_recent_games(6)
    return render_template('index.html', screenshots=screenshots, recent_games=recent_games, navigation=return_navigation(), site_data=site_data())

@app.route('/name/<filter>')
def show_entries_letter(filter=''):
    valid_category = False
    order = request.args.get('order', None)
    search_by_letter = False
    if filter in string.ascii_uppercase:
        valid_category = True
        search_by_letter = True
        games = return_games(order=order, letter=filter)
    if not valid_category:
        return render_template('404.html', site_data=site_data(), navigation=return_navigation()), 404
    title = "Games starting with: " + filter
    return render_template('show_entries.html', current_slug=filter, navigation=return_navigation(), games=games, site_data=site_data(), title=title)

@app.route('/year/<filter>')
def show_entries_year(filter=''):
    valid_category = False
    order = request.args.get('order', None)
    end_year = date.today().year+1
    site_data_var = site_data()
    start_year = site_data_var['start_year']
    search_by_year = False
    if filter in str(range(start_year, end_year)):
        valid_category = True
        search_by_year = True
        games = return_games(order=order, year=filter)
    if not valid_category:
        return render_template('404.html', site_data=site_data(), navigation=return_navigation()), 404
    title = "Release Year: " + filter
    return render_template('show_entries.html', current_slug=filter, navigation=return_navigation(), games=games, site_data=site_data(), title=title)

@app.route('/category/<filter>')
def show_entries(filter=''):
    valid_category = False
    category_groups=return_cats()
    for cat_group in category_groups:
        for cat in cat_group.categories:
            if filter == cat.slug:
                valid_category = True
    if filter == 'all':
        valid_category = True
    order = request.args.get('order', None)
    if not valid_category:
        return render_template('404.html', site_data=site_data(), navigation=return_navigation()), 404
    games = return_games(category=filter, order=order)
    cat_name = Category.query.filter(Category.slug==filter).one()
    cat_name = cat_name.name
    title = "Category: " + cat_name
    return render_template('show_entries.html', current_slug=filter, navigation=return_navigation(), games=games, site_data=site_data(), title=title)

@app.route('/search')
def search_game():
    search = request.args.get('q', None)
    order = request.args.get('order', None)
    if search:
        games = return_games(search=search, order=order)
    else:
        games = ''
    return render_template('search.html', search=search, navigation=return_navigation(), games=games, site_data=site_data())

@app.route('/special/<special>')
def show_entries_special(special=''):
    valid_option = False
    order = request.args.get('order', None)
    title = ""
    if special == 'unapproved':
        games = return_games(approved=False, order=order)
        valid_option = True
    if special == 'no_screenshot':
        games = return_games(order=order, no_screenshot=True)
        valid_option = True
    if special == 'macintosh' or special == 'linux':
        if special == 'macintosh':
            platform_id=2
        if special == 'linux':
            platform_id=3
        games = return_games(order=order, platform=platform_id)
        valid_option = True
    if special == 'all':
        games = return_games(category="all", order=order)
        title = "All Games"
        valid_option = True
    if special == 'quick':
        games = Game.query.order_by(Game.id)
        return render_template('show_entries_brief.html', navigation=return_navigation(), games=games, site_data=site_data())
    if special == 'compact':
        games = return_games(category="all", order=order)
        return render_template('show_entries_compact.html', navigation=return_navigation(), games=games, site_data=site_data())
    if valid_option:
        return render_template('show_entries.html', current_slug=special, navigation=return_navigation(), games=games, site_data=site_data(), title=title)
    else:
        return render_template('404.html', site_data=site_data(), navigation=return_navigation()), 404

@app.route('/game/<game_slug>.shtml', methods=['GET', 'POST'])
def game_details(game_slug=''):
    game = return_games(category=None, game_slug=game_slug)
    form = AdminGameApproveForm()
    if form.validate_on_submit():
        game.approved = False
        if form.approved.data>0:
            game.approved = True
        game.listed_on = form.approved.data
        db.session.commit()
        flash('Saved.')
    form.approved.data = str(game.listed_on)
    return render_template('game.html', game=game, form=form, navigation=return_navigation(), site_data=site_data())

@app.route('/statistics')
def statistics():
    total = Game.query.count()
    site_data_var = site_data()
    here = Game.query.filter(or_(Game.listed_on==site_data_var['domain_id'], Game.listed_on==site_data_var['renai_archive_id']+site_data_var['renpy_list_id'])).count()
    here_unique = Game.query.filter(Game.listed_on==site_data_var['domain_id']).count()
    if site_data_var['renai_archive_id'] == site_data_var['domain_id']:
        there_id = site_data_var['renpy_list_id']
    else:
        there_id = site_data_var['renai_archive_id']
    there = Game.query.filter(or_(Game.listed_on==there_id, Game.listed_on==site_data_var['renai_archive_id']+site_data_var['renpy_list_id'])).count()
    there_unique = Game.query.filter(Game.listed_on==there_id).count()
    stats = dict(total = total, here=here, there=there, here_unique=here_unique, there_unique=there_unique)
    return render_template('statistics.html', stats=stats, other_id=there_id, navigation=return_navigation(), site_data=site_data())

@app.route('/edit/<game_slug>.shtml', methods=['GET', 'POST'])
@login_required
def edit_game(game_slug):
    game = db.session.query(Game).filter(Game.slug==game_slug).one()
    error = None
    form = GameFormEdit()
    if form.validate_on_submit():
        game.game_title = form.game_title.data
        game.creator_type = form.creator_type.data
        game.description = form.description_.data
        game.age_rating_id = form.age_rating_id.data

        words = form.words.data
        words = words.replace(",", "")
        words = words.replace(".", "")
        try:
            words = int(re.search(r'(0|(-?[1-9][0-9]*))', words).group(0))
        except: # Catch exception if re.search returns None
            words = 0

        if not words:
            words = 0
        game.words = words

        playtime = 0
        if form.playtime.data:
            try:
                playtime = float(form.playtime.data)
            except TypeError:
                try:
                    playtime = int(re.search(r'(0|(-?[1-9][0-9]*))', form.playtime.data).group(0))
                except TypeError: # Catch exception if re.search returns None
                    playtime = 0
            #playtime = float(form.playtime.data)
            if form.playtime_unit.data == 'hours':
                playtime = playtime * 60
                game.playtime = int(math.ceil(playtime))
            else:
                #game.playtime = 0
                #game.playtime = form.playtime.data
                game.playtime = playtime
        if game.words == 0:
            game.words_estimate = playtime*200
        else:
            game.words_estimate = game.words

        #save new creator if it doesn't exists:
        developer_name = form.creator.data
        developer_name = developer_name.replace("'", "")
        developer = Developer.query.filter(Developer.name==developer_name).first()
        if not developer:
            if creator_type=='person':
                type=1
                person = Person('')
                db.session.add(person)
                db.session.commit()
                developer = Developer (developer_name, type, g.user.id, person_id=person.id)
            if creator_type=='group':
                type=2
                group = Group('')
                db.session.add(group)
                db.session.commit()
                developer = Developer (developer_name, type, g.user.id, group_id=group.id)
            db.session.add(developer)
        game.developer_id = developer.id

        #save homepage link to link_game table:
        li = LinkGame.query.filter_by(game_id=game.id).first()
        if not li.url==form.homepage_link_url.data:
            db.session.delete(li)
            li = LinkGame(game_id=game.id, url=form.homepage_link_url.data, name = 'Home Page', link_type_id = '1')
            db.session.add(li)
        categories = []
        for category in game.categories:
            if not category.category_id in form.categories.data:
                ca = CategoryGame.query.filter_by(id=category.id).first()
                db.session.delete(ca)
            categories.append(category.category_id)
        for category in form.categories.data:
            if not category in categories:
                db.session.add(CategoryGame(category_id=category, game_id=game.id))
        db.session.commit()

        flash('Release data was saved.')
        return redirect(url_for('game_details', game_slug=game_slug))
    else:
        form.game_title.data = game.game_title
        form.homepage_link_url.data = game.link.url
        form.description_.data = game.description
        form.age_rating_id.data = game.age_rating_id
        form.words.data = game.words
        form.playtime.data = game.playtime
        form.categories.data = []
        for category in game.categories:
            form.categories.data.append(category.category_id)
        dev = db.session.query(Developer).filter(Developer.id==game.developer_id).one()
        if dev.type==1:
            form.creator_type.data = "person"
        else:
            form.creator_type.data = "group"
        form.creator.data = dev.name

    developers = '['
    for developer in Developer.query.filter(Developer.id>0).order_by(Developer.type):
        developer.name = developer.name.replace("'", "")
        developers += '"'+developer.name+'",'
    developers = developers[:-1]
    developers += ']'

    return render_template('add_game.html', navigation=return_navigation(), site_data=site_data(), form=form, developers=developers, edit=True)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_game():
    form = GameForm()
    error = ''
    developers = '['
    for developer in Developer.query.filter(Developer.id>0).order_by(Developer.type):
        developer.name = developer.name.replace("'", "\\'")
        developer.name = developer.name.replace('"', '\\"')
        developers += '"'+developer.name+'",'
    developers = developers[:-1]
    developers += ']'
    #creators = '["PunkCabbageRabbit","Akane","flowerthief","Lemma Soft","Zeiva Inc.","ATP Projects","Grey","American Bishoujo","Ren\'Ai Games","Chronoluminaire","Gloranor"]'

    if form.validate_on_submit():
        game_title=form.game_title.data
        slug=form.slug.data
        homepage_link_url=form.homepage_link_url.data
        developer_name=form.creator.data
        maker=developer_name
        creator_type=form.creator_type.data
        description = form.description_.data
        age_rating_id=str(form.age_rating_id.data)
        categories = form.categories.data
        words = form.words.data
        words = words.replace(",", "")
        words = words.replace(".", "")
        try:
            words = int(re.search(r'(0|(-?[1-9][0-9]*))', words).group(0))
        except: # Catch exception if re.search returns None
            words = 0
        if not words:
            words = 0

        playtime = 0
        if form.playtime.data:
            try:
                playtime = float(form.playtime.data)
            except TypeError:
                try:
                    playtime = int(re.search(r'(0|(-?[1-9][0-9]*))', form.playtime.data).group(0))
                except TypeError: # Catch exception if re.search returns None
                    playtime = 0
            if form.playtime_unit.data == 'hours':
                playtime = playtime * 60
                playtime = int(math.ceil(playtime))
            else:
                playtime = playtime


        if words == 0:
            words_estimate = playtime*200
        else:
            words_estimate = words
        listed_on = form.listed_on.data
        if listed_on:
            listed_on = 3 # both
        else:
            listed_on = 2 # games.renpy.org only

        game = Game(game_title=game_title, slug=slug, maker = maker, description = description, age_rating_id=age_rating_id, words = words, words_estimate=words_estimate, playtime = playtime, developer_id=1, user_id=g.user.id, approved=False, listed_on=listed_on)
        db.session.add(game)
        db.session.commit()

        release = Release(game_id=game.id, release_date=form.release_date.data, release_version=form.release_version.data, engine_id=form.engine_id.data, release_description = form.release_description.data, engine_version = form.engine_version.data, user_id=g.user.id)
        save_release(release, form.platforms.data)

        #save new creator if it doesn't exists:
        developer_name = developer_name.replace("'", "")
        developer = Developer.query.filter(Developer.name==developer_name).first()

        if not developer:
            if creator_type=='person':
                type=1
                person = Person('')
                db.session.add(person)
                db.session.commit()
                developer = Developer (developer_name, type, g.user.id, person_id=person.id)
            if creator_type=='group':
                type=2
                group = Group('')
                db.session.add(group)
                db.session.commit()
                developer = Developer (developer_name, type, g.user.id, group_id=group.id)
            db.session.add(developer)

        #save homepage link to link_game table:
        links_game= LinkGame(game_id=game.id, url=homepage_link_url, name = 'Home Page', link_type_id = '1')
        db.session.add(links_game)

        #save the categories to category_game:
        for category_id in categories:
            categories_game = CategoryGame(game_id=game.id, category_id=category_id)
            db.session.add(categories_game)

        db.session.commit()
        game.developer_id = developer.id
        db.session.commit()

        flash('New game was successfully added. The game must be approved by a moderator, before it will show up on the site. This might take a couple of days, depending on how busy we are.')
        return redirect(url_for("index"))
    return render_template('add_game.html', navigation=return_navigation(), error=error, site_data=site_data(), form=form, developers=developers, edit=False)

def save_release(release, selected_platforms):
    db.session.add(release)
    db.session.commit()
    for platform in selected_platforms:
        db.session.add(PlatformRelease(release_id=release.id, platform_id=platform))
    return True

@app.route('/add/<game_slug>/release', methods=['GET', 'POST'])
@login_required
def add_release(game_slug=""):
    form = ReleaseForm()
    error = None
    game = Game.query.filter(Game.slug==game_slug).one()
    if form.validate_on_submit():
        release = Release(game_id=game.id, release_date=form.release_date.data, release_version=form.release_version.data, engine_id=form.engine_id.data, release_description = form.release_description.data, engine_version = form.engine_version.data, user_id=g.user.id)
        save_release(release, form.platforms.data)
        db.session.commit()
        flash('New release data was added.')
        return redirect(url_for("upload_file", game_slug=game_slug)+'?release='+str(release.id))
    return render_template('add_release.html', game=game, navigation=return_navigation(), error=error, site_data=site_data(), form=form)

@app.route('/edit/<game_slug>/release/<release_id>', methods=['GET', 'POST'])
@login_required
def edit_release(game_slug="", release_id=""):
    form = ReleaseForm()
    error = None
    game = Game.query.filter(Game.slug==game_slug).one()
    release = db.session.query(Release).filter(Release.id==release_id).one()

    if form.validate_on_submit():
        release.release_date = form.release_date.data
        release.release_version = form.release_version.data
        release.engine_id = form.engine_id.data
        release.release_description = form.release_description.data
        release.engine_version = form.engine_version.data
        platforms = []
        for platform in release.platforms:
            if not platform.platform_id in form.platforms.data:
                pl = PlatformRelease.query.filter_by(id=platform.id).first()
                db.session.delete(pl)
            platforms.append(platform.platform_id)
        for platform in form.platforms.data:
            if not platform in platforms:
                db.session.add(PlatformRelease(release_id=release.id, platform_id=platform))
        db.session.commit()
        flash('Release data was saved.')
        return redirect(url_for('game_details', game_slug=game_slug))
    else:
        form.release_date.data = release.release_date
        form.release_version.data = release.release_version
        form.engine_id.data = release.engine_id
        form.release_description.data = release.release_description
        form.engine_version.data = release.engine_version

        form.platforms.data = []
        for platform in release.platforms:
            form.platforms.data.append(platform.platform_id)
    return render_template('add_release.html', game=game, navigation=return_navigation(), error=error, site_data=site_data(), form=form)


@app.route('/add/<game_slug>/screenshot', methods=['GET', 'POST'])
@login_required
def add_screenshot(game_slug=''):
    is_thumb = False
    game = return_games(game_slug=game_slug)
    if not game.screenshots:
        is_thumb = True
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file_img(file.filename):
            filename = secure_filename(file.filename)
            game_id = game.id
            filename = game_slug + "-" + filename

            filename2 = os.path.join(app.config['IMAGE_UPLOAD_FOLDER'], filename)
            #filename2 = filename.replace('\\', '/')
            
            if os.path.isfile(filename2):
                fileName, fileExtension = os.path.splitext(filename2)
                filename2 = fileName + '-' + time.strftime("%Y%m%d-%H%M%S") + fileExtension
            
            file.save(filename2)
            outfilename = resize_image(filename, game_slug)
            try:
                is_thumb = request.form['is_thumb']
                if is_thumb:
                    is_thumb = True
            except:
                is_thumb = False
            screenshot = Screenshot(game_id=game_id, filename=outfilename, caption=request.form['caption'], is_thumb=is_thumb)
            db.session.add(screenshot)
            db.session.commit()

            return redirect(url_for('add_screenshot', game_slug=game_slug))
    return render_template('add_screenshot.html', game=game, navigation=return_navigation(), is_thumb=is_thumb, site_data=site_data())

def resize_image(filename, game_slug):
    sizes = dict(normal = app.config['IMAGE_SIZE_NORMAL'], small = app.config['IMAGE_SIZE_SMALL'], medium = app.config['IMAGE_SIZE_MEDIUM'])
    dirs = dict(normal = app.config['IMAGE_UPLOAD_FOLDER'], small = app.config['IMAGE_UPLOAD_FOLDER_SMALL'], medium = app.config['IMAGE_UPLOAD_FOLDER_MEDIUM'])
    for s in ['normal','small','medium']:
        infile = dirs['normal'] + '/' + filename
        size = sizes[s]
        #do_resize = False
        do_resize = True
        if do_resize:
            outfilename = os.path.splitext(filename)[0] + ".jpg"
        else:
            outfilename = filename
        outfile = dirs[s] + '/' + outfilename
        if infile != outfile:
            if do_resize:
                im = Image.open(infile)
                width, height = im.size
                size1 = size
                if width<size[0]:
                    #size[0]=width
                    size1 = (width, size[1])
                im.thumbnail(size1, Image.ANTIALIAS)
                bg = Image.new('RGBA', size, (255, 255, 255, 0))
                bg.paste(im,((size[0] - im.size[0]) / 2, (size[1] - im.size[1]) / 2))

                if do_resize:
                    bg.save(outfile, "JPEG")
                else:
                    im.save(outfile)
            else:
                shutil.copy(infile, outfile)
    return outfilename

def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
app.add_url_rule(app.config['UPLOAD_URL']+'<filename>', 'uploaded_file', uploaded_file)

def image_normal(filename):
    return send_from_directory(app.config['IMAGE_UPLOAD_FOLDER'], filename)
app.add_url_rule(app.config['IMAGE_UPLOAD_URL']+'<filename>', 'image_normal', image_normal)

def image_medium(filename):
    return send_from_directory(app.config['IMAGE_UPLOAD_FOLDER_MEDIUM'], filename)
app.add_url_rule(app.config['IMAGE_UPLOAD_URL_MEDIUM']+'<filename>', 'image_medium', image_medium)

def image_small(filename):
    return send_from_directory(app.config['IMAGE_UPLOAD_FOLDER_SMALL'], filename)
app.add_url_rule(app.config['IMAGE_UPLOAD_URL_SMALL']+'<filename>', 'image_small', image_small)

@app.route('/account/login/', methods=['GET', 'POST'])
@oid.loginhandler
def login():
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('index'))
    form = LoginForm()
    formoid = LoginFormOid()
    error = ''
    if formoid.validate_on_submit():
        session['remember_me'] = formoid.remember_me.data
        return oid.try_login(formoid.openid.data, ask_for = ['nickname', 'email'])
    if form.validate_on_submit():

        #password = md5.md5(form.password.data).hexdigest()

        user = UserAccount.query.filter(UserAccount.username==form.username.data).first()
        salt = user.password.split('$')
        salt = salt[1]
        #print salt
        password = 'sha1$'+salt+'$'+hashlib.sha1(salt + form.password.data).hexdigest()
#        password = hashlib.sha1(form.password.data).hexdigest()
        user = UserAccount.query.filter(and_(UserAccount.username==form.username.data, UserAccount.password==password)).first()
        if not user:
            error = 'Invalid username or password.'
        else:
            login_user(user, remember = form.remember_me.data)
            flash("Logged in successfully.")
            return redirect(request.args.get("next") or url_for("index"))
    return render_template('login.html', form=form, formoid=formoid, help_email=ADMINS[0], error=error, navigation=return_navigation(), providers = app.config['OPENID_PROVIDERS'], site_data=site_data())

@oid.after_login
def after_login(resp):
    if resp.email is None or resp.email == "":
        flash('Invalid login. Please try again.')
        redirect(url_for('login'))
    user = UserAccount.query.filter_by(email = resp.email).first()
    if user is None:
        username = resp.nickname
        if username is None or username == "":
            username = resp.email.split('@')[0]
        user = UserAccount(username = username, password='', email = resp.email, role = ROLE_USER)
        db.session.add(user)
        db.session.commit()
    remember_me = False
    if 'remember_me' in session:
        remember_me = session['remember_me']
        session.pop('remember_me', None)
    flash("Logged in successfully.")
    login_user(user, remember = remember_me)
    return redirect(request.args.get('next') or url_for('index'))

@app.route('/account/logout/')
def logout():
    logout_user()
    flash('You are logged out.')
    return redirect(url_for('index'))

@app.route('/account/signup/', methods=['GET', 'POST'])
def signup():
    error = ''
    form = SignupForm()
    if form.validate_on_submit():
        chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
        salt = ''.join(random.choice(chars) for x in range(5))

        password = password = 'sha1$'+salt+'$'+hashlib.sha1(salt + form.password.data).hexdigest()
#        user = UserAccount(username=form.username.data, password=md5.md5(form.password.data).hexdigest(), email = form.email.data, role = ROLE_USER)
        user = UserAccount(username=form.username.data, password=password, email = form.email.data, role = ROLE_USER)
        db.session.add(user)
        db.session.commit()
        flash('You have signed up successfully. Please log in.')
        return redirect(url_for('login'))
    return render_template('signup.html', form=form, error=error, help_email=ADMINS[0], navigation=return_navigation(), site_data=site_data())

@app.route('/account/password_reset/', methods=['GET', 'POST'])
def password_reset():
    from emails import password_reset_request
    error = ''
    form = PassResetForm()
    if form.validate_on_submit():
        user = UserAccount.query.filter(UserAccount.email==form.email.data).first()
        if user:
            password_reset_token = str(uuid.uuid4())
            user.password_reset_token=password_reset_token
            user.password_reset_expiration=now()+timedelta(days=7)
            db.session.commit()
            password_reset_url = url_for('new_password', _external = True) + '?token=' + password_reset_token
            password_reset_request(user, password_reset_url)
            flash('Email to reset your password has been sent.')
        else:
            error = 'User with that email does not exists.'
    return render_template('password_reset.html', form=form, error=error, navigation=return_navigation(), site_data=site_data())

@app.route('/account/new_password/', methods=['GET', 'POST'])
def new_password():
    error = ''
    token = request.args.get('token', None)
    user = UserAccount.query.filter(and_(UserAccount.password_reset_token==token, now()<UserAccount.password_reset_expiration)).first()
    if not user:
        flash('Invalid or expired password reset token.')
        return redirect(url_for('index'))
    form = NewPasswordForm()
    if form.validate_on_submit():
        user = UserAccount.query.filter(and_(UserAccount.password_reset_token==token, now()<UserAccount.password_reset_expiration)).first()
        user.password=md5.md5(form.password.data).hexdigest()
        user.password_reset_token=''
        db.session.commit()
        flash('Password has been changed.')
        return redirect(url_for('login'))
    return render_template('new_password.html', form=form, error=error, help_email=ADMINS[0], navigation=return_navigation(), site_data=site_data())

@app.errorhandler(404)
def internal_error(error):
    return render_template('404.html', site_data=site_data()), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html', site_data=site_data()), 500

@login_required
@app.route('/add/<game_slug>/files/', methods=['GET', 'POST'])
def upload_file(game_slug):
    release_id = request.args.get('release', None)
    file_id = request.args.get('file', None)

    if file_id:
        file = db.session.query(File).filter(File.id==file_id).one()
        form = UploadForm()
        form.edit.data = "True"
    else:
        form = UploadForm()
        form.edit.data = ""

    if form.validate_on_submit():
        uploaded_file = form.uploaded_file.data
        if uploaded_file: # and allowed_file(uploaded_file.filename):
            filename = secure_filename(uploaded_file.filename)
            if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
                fileName, fileExtension = os.path.splitext(filename)
                filename = fileName + '-' + time.strftime("%Y%m%d-%H%M%S") + fileExtension
            uploaded_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        if form.edit.data:
            if uploaded_file:
                file.filename=filename

            file.description=form.description.data
        else:
            if uploaded_file:
#                release = Release.query.filter(Release.id==release_id).one()
                file = File(release_id=release_id, filename=filename, description=form.description.data)
                db.session.add(file)
        if uploaded_file or form.edit.data:
            db.session.commit()
            if not form.edit.data:
                form.description.data=None
        if form.edit.data:
            flash('File changed!')
        else:
            if uploaded_file:
                flash('File uploaded!')
    else:
        if form.edit.data:
            form.description.data=file.description

    return render_template('add_file.html', form=form, site_data=site_data(), navigation=return_navigation())

@app.route('/account/settings/', methods=['GET', 'POST'])
@login_required
def account_settings():
    form = AccountForm()
    formpass = ChangePasswordForm()
    error = ''
    sel_tab = 1
    user = UserAccount.query.filter(UserAccount.id==g.user.id).one()
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        db.session.add(user)
        db.session.commit()
        flash ('Changes saved.')
    form.username.data = user.username
    form.email.data = user.email

    if request.method == 'POST' and formpass.submit_pass:
        sel_tab = 2
    if formpass.validate_on_submit():

        password = md5.md5(formpass.password.data).hexdigest()
        user1 = UserAccount.query.filter(and_(UserAccount.id==g.user.id, UserAccount.password==password)).first()
        if not user1:
            error = 'Invalid  password.'
        else:
            newpassword = md5.md5(formpass.newpassword.data).hexdigest()
            user1.password = newpassword
            db.session.add(user1)
            db.session.commit()
            flash ('New password saved.')
    return render_template('account.html', form=form, formpass=formpass, site_data=site_data(), navigation=return_navigation(), error=error, sel_tab=sel_tab)

@app.route('/developer/<developer>')
def developer_info(developer):
    games = Game.query.filter(Game.developer_id==developer).all()
    num_of_games = len(games)
    developer = Developer.query.filter(Developer.id==developer).one()
    return render_template('developer.html', num_of_games=num_of_games, developer=developer, games=games, navigation=return_navigation(), site_data=site_data())

@app.route('/test/domain/<domain_id>')
def change_domain_testing(domain_id):
    if str(domain_id)==str(RENAI_ARCHIVE_ID):
        session['DOMAIN_ID']=str(RENAI_ARCHIVE_ID)
        flash ('Domain changed.')
    if str(domain_id)==str(RENPY_LIST_ID):
        session['DOMAIN_ID']=str(RENPY_LIST_ID)
        flash ('Domain changed.')
    if str(domain_id)==str(0):
        session.pop('DOMAIN_ID', None)
        flash ('Domain restored.')
    screenshots = ''
    recent_games = ''
    return redirect(url_for('index'))

@app.route('/approve/file/<id>/<slug>')
def approve_file(id, slug):
    file = db.session.query(File).filter(File.id==id).one()
    file.approved = True
    db.session.commit()
    return redirect(url_for('game_details', game_slug=slug))

@app.route('/approve/release/<id>/<slug>')
def approve_release(id, slug):
    release = db.session.query(Release).filter(Release.id==id).one()
    release.approved = True
    db.session.commit()
    return redirect(url_for('game_details', game_slug=slug))

@app.route('/approve/game/<id>/<slug>')
def approve_game(id, slug):
    game = db.session.query(Game).filter(Game.id==id).one()
    game.approved = True
    db.session.commit()
    return redirect(url_for('game_details', game_slug=slug))

@app.route('/delete_screenshot/<slug>/<id>')
def delete_screenshot(slug, id):
    screenshot = Screenshot.query.filter_by(id=id).first()
    filename = screenshot.filename
    os.remove(os.path.join(app.config['IMAGE_UPLOAD_FOLDER'], filename))
    os.remove(os.path.join(app.config['IMAGE_UPLOAD_FOLDER_SMALL'], filename))
    os.remove(os.path.join(app.config['IMAGE_UPLOAD_FOLDER_MEDIUM'], filename))
    db.session.delete(screenshot)
    db.session.commit()
    return redirect(url_for('add_screenshot', game_slug=slug))

@app.route('/delete_file/<slug>/<id>')
def delete_file(slug, id):
    file = File.query.filter_by(id=id).first()
    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
    db.session.delete(file)
    db.session.commit()
    return redirect(url_for('game_details', game_slug=slug))

@app.route('/set_thumbnail/<slug>/<id>', methods=['GET', 'POST'])
def set_thumbnail(slug, id):
    screenshots = Game.query.filter_by(slug=slug).first().screenshots
    for screenshot in screenshots:
        screenshot.is_thumb = False
    screenshot = Screenshot.query.filter_by(id=id).first()
    screenshot.is_thumb = True

    db.session.commit()
    return redirect(url_for('add_screenshot', game_slug=slug))

@app.route('/delete_release/<slug>/<id>')
def delete_release(slug, id):
    release = Release.query.filter_by(id=id).first()
    for file in release.files:
        file = File.query.filter_by(id=file.id).first()
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
        db.session.delete(file)
    db.session.delete(release)
    db.session.commit()
    return redirect(url_for('game_details', game_slug=slug))

@app.route('/delete_game/<slug>')
def delete_game(slug):
    game = Game.query.filter_by(slug=slug).first()
    for release in game.releases:
        delete_release(slug, release.id)
    db.session.delete(game)
    db.session.commit()
    return redirect(url_for('/'))
    
    
# @app.route('/getvndb/<slug>')
# def get_vndb(slug):
    ##http://thomasfischer.biz/?p=622
    # game = Game.query.filter(Game.slug==slug).one()
    # title=game.game_title
    # form = ReleaseForm()
    # error = None
    # s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # s.settimeout(3)
    # host = 'api.vndb.org'
    # host = socket.gethostbyname(host)
    # s.connect((host, 19534))
    # print "connected"
    # data = {"protocol":1,"client":"test","clientver":0.1,"username":"leonz","password":"ZOTVfsjw68t9"}
    # data = "login " + json.dumps(data) + "\x04"
    # s.send(data)
    # print "data sent"

    # data_rec = s.recv(1024)
    # print "data received"
    # print data_rec
    # s.send('get vn basic (title="' +title+ '")' + "\x04")
    # data_rec = s.recv(1024)
    # data_rec = data_rec.replace('results ', '')[:-1]
    # print data_rec
    # result = json.loads(data_rec)
    # print result
    # num = result['num']
    # s.close()
    # if num > 0:
        # exists=True
    # else:
        # exists=False
    # return render_template('vndb.html', exists=exists, game=game, site_data=site_data(), navigation=return_navigation(), error=error)

