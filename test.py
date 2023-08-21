from timeline import from_md

tl = from_md('readme.md')
tl.compile(fontname='meiryo')
tl.render('readme')
