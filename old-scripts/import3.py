from app import app, db, views, models
from sqlalchemy import Integer, String, Boolean, Date, Text, DateTime, SmallInteger, and_, or_, desc
from flask import g #,render_template, request, session, redirect, url_for, abort, flash, send_from_directory
import sys
import os

files = db.session.query(models.File).all()
for file in files:
    fn = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)

    if os.path.exists(fn):
        statinfo = os.stat(fn)
        file.size=statinfo.st_size
    else:
        print("Bad fn", fn)
db.session.commit()
print "Done."
