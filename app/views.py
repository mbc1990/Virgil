from flask import render_template, redirect, url_for, session
from app import app, db
from forms import PoemForm
from models import Poem, Seed_Word

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    form = PoemForm() 
    if form.validate_on_submit():  
        # Create an empty poem (with a unique id)
        poem = Poem()
        db.session.add(poem) 

        # Add all the input seedwords 
        seed_word_split = form.seed_words.data.split(',')
        for sw  in seed_word_split:
            seed_word = Seed_Word(word=sw, poem=poem)
            db.session.add(seed_word)
        db.session.commit()
        return redirect(url_for('index'))  

    # Display all poems for testing 
    poems = Poem.query.all()
    return render_template('index.html', title='Virgil', form=form, poems=poems)

@app.route('/favorites')
def favorites():
    return render_template('favorites.html')
