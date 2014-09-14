from config import SQLALCHEMY_DATABASE_URI
from app import db
from app import models

if 1==1:
    print "dropping tables"
    db.drop_all()
    
print "creating tables"
db.create_all()

if 1==1:
      db.session.add_all([
        models.Category('Visual Novel', 1, True, 'vn'),
        models.Category('Kinetic Novel', 1, True, 'kn'),
        models.Category('Role-Playing Game', 1, True, 'rpg'),
        models.Category('Simulation', 1, True, 'sim'),
        models.Category('Tactics', 1, False, 'tactics'),
        models.Category('Other Gameplay', 1, True, 'uncategorized'),
        models.Category('Boy pursues Girl', 2, True, 'BxG'),
        models.Category('Boy pursues Boy', 2, True, 'BxB'),
        models.Category('Girl pursues Boy', 2, True, 'GxB'),
        models.Category('Girl pursues Girl', 2, True, 'GxG'),
        models.Category('Mystery', 3, True, 'mystery'),
        models.Category('Parody', 3, True, 'parody'),
        models.Category('Commercial', 4, False, 'commercial'),
        models.Category('NaNoRenO', 4, False, 'nanoreno'),
        models.Category('Teacup Festival', 4, False, 'teacup')])

      db.session.add_all([
        models.CategoryGroup('By Gameplay', True),
        models.CategoryGroup('By Relationship', True),
        models.CategoryGroup('By Genre', True),
        models.CategoryGroup('Extra', False)])

      renpy = "Ren'Py"
      db.session.add_all([
        models.Engine(renpy),
        models.Engine('Novelty'),
        models.Engine('Flash'),
        models.Engine('Other')])
	
      db.session.add_all([
        models.LinkType('homepage')])

      db.session.add_all([
        models.Platform('Windows'),
        models.Platform('Mac OS X'),
        models.Platform('Linux'),
        models.Platform('Other')])

#      db.session.add_all([
#        models.UserAccount('admin', '21232f297a57a5a743894a0e4a801fc3', '', 1, 1)]) #TEST. REMOVE THIS!

      db.session.add_all([
        models.AgeRating('All ages', 'All ages, no sexual content', False),
        models.AgeRating('13+', 'Perhaps some sexual themes, no nudity', False),
        models.AgeRating('16+', 'Nonexplicit nudity, off-camera sex', False),
        models.AgeRating('18+', 'Adult, anything goes', True)
        ])

      db.session.add_all([
        models.Group('undefined')])
        
      db.session.add_all([
        models.Person('undefined')])

      db.session.add_all([
        models.Developer('undefined')])
        
print "commiting changes"
db.session.commit()
