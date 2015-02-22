from flask import render_template, redirect, url_for, session, flash
from app import app, db
from forms import PoemForm
from models import Poem, Seed_Word
from sqlalchemy import desc
from datetime import datetime

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    form = PoemForm() 
    if form.validate_on_submit():  
        flash("poem added")

        # Create an empty poem (with a unique id)
        poem = Poem(timestamp=datetime.utcnow(),
            generations=form.generations.data,
            mutation_probability=form.mutation_probability.data,
            phonetic_similarity_weight=form.phonetic_similarity_weight.data,
            breeding_fraction=form.breeding_fraction.data,
            starting_population_size=form.starting_population_size.data,
            lines=form.lines.data,
            current_generation=0)

        db.session.add(poem) 

        # Add all the input seedwords 
        seed_word_split = form.seed_words.data.split(',')
        for sw  in seed_word_split:
            seed_word = Seed_Word(word=sw, poem=poem)
            db.session.add(seed_word)
        db.session.commit()

        # Add the poem to the queue
        app.poem_queue.add_poem(poem)

        return redirect(url_for('index'))  

    # Display all poems for testing 
    poems = Poem.query.order_by(desc(Poem.id)).all()
    return render_template('index.html', title='Virgil', form=form, poems=poems)

@app.route('/favorites')
def favorites():
    return render_template('favorites.html')
