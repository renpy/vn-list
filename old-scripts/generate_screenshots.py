import os
from PIL import Image
import shutil

def resize_image(filename):

    if not os.path.isfile(filename):
        return

    widths = dict(
        normal = 1024, # app.config['IMAGE_SIZE_NORMAL'],
        small = 240, # app.config['IMAGE_SIZE_SMALL'],
        medium = 320, # app.config['IMAGE_SIZE_MEDIUM'],
        )

    dirs = dict(
        normal = ".",
        small = "small",
        medium = "medium",
        )

    infile = dirs['normal'] + '/' + filename
    original_fn = os.path.join("original", filename)
    os.rename(infile, original_fn)

    if filename.endswith(".jpg"):
        outfilename = filename
    else:
        outfilename = filename + ".jpg"

    # outfilename = os.path.splitext(filename)[0] + ".jpg"

    for s in ['small', 'medium', 'normal', ]:

        outfile = dirs[s] + '/' + outfilename

        im = Image.open(original_fn)
        old_width, old_height = im.size

        new_width = widths[s]
        new_height = int(old_height * new_width / old_width)

        im2 = im.resize((new_width, new_height), Image.ANTIALIAS)
        im2.save(outfile, "JPEG")

    return outfilename

for fn in os.listdir("."):
    try:
        resize_image(fn)
    except:
        print(fn, "failed.")

#         if fn.endswith(".png") or fn.endswith(".jpg"):
#             raise
