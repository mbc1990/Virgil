from flask import render_template, redirect, url_for, session, flash
from app import app, db, poem_queue
from forms import PoemForm
from models import Poem, Seed_Word
from sqlalchemy import desc
from datetime import datetime

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    form = PoemForm() 
    if form.validate_on_submit():  
        # Create an empty poem (with a unique id)
        poem = Poem(timestamp=datetime.utcnow(),
            generations=form.generations.data,
            mutation_probability=form.mutation_probability.data,
            #phonetic_similarity_weight=form.phonetic_similarity_weight.data,
            phonetic_similarity_weight=1.0,
            breeding_fraction=form.breeding_fraction.data,
            starting_population_size=form.starting_population_size.data,
            lines=form.lines.data,
            current_generation=0,
            progress=0)

        db.session.add(poem) 
        db.session.commit()

        # Add all the input seedwords 
        seed_words = form.seed_words.data.replace(', ',',')
        seed_word_split = seed_words.split(',')
        for sw  in seed_word_split:
            seed_word = Seed_Word(word=sw, poem=poem)
            db.session.add(seed_word)
            db.session.commit()

        # Add the poem to the queue
        app.poem_queue.add_poem(poem)

        # Keep track of poem id 
        session['poem_id'] = poem.id 
        print "Poem "+str(poem.id)+" added"

        return redirect(url_for('index'))  

    poems = []
    queue_position = -1
    if 'poem_id' in session:
        poem = Poem.query.filter_by(id=session['poem_id']).first()
        queue_position = app.poem_queue.get_position(poem)
        poems = [poem]
    
    # Correct class for queue position 
    qp_class = "qp-waiting"
    if queue_position == 0:
        qp_class = "qp-current"
    elif queue_position < 0:
        qp_class = "qp-none"

    return render_template('index.html', title='Virgil', form=form, poems=poems, queue_position=queue_position, qp_class=qp_class, cb_class="active")

@app.route('/about', methods=['GET'])
def about():
    queue_position = -1
    if 'poem_id' in session:
        poem = Poem.query.filter_by(id=session['poem_id']).first()
        queue_position = app.poem_queue.get_position(poem)
    queue_position = -1

    if 'poem_id' in session:
        poem = Poem.query.filter_by(id=session['poem_id']).first()
        queue_position = app.poem_queue.get_position(poem)
        poems = [poem]

    # Correct class for queue position 
    qp_class = "qp-waiting"
    if queue_position == 0:
        qp_class = "qp-current"
    elif queue_position < 0:
        qp_class = "qp-none"

    return render_template('about.html', title='Virgil - About', queue_position=queue_position, qp_class=qp_class, ab_class="active") 


@app.route('/poem/<poemid>', methods=['GET', 'POST'])
def poem(poemid):
   poem = Poem.query.filter_by(id=poemid).first()
   return render_template('poem.html', poem=poem)

@app.route('/session_poem', methods=['GET', 'POST'])
def session_poem():
   poemid = session['poem_id']
   print 'session poem id: '+str(poemid)
   poem = Poem.query.filter_by(id=poemid).first()
   return render_template('poem.html', poem=poem)
   #return '{current_generation:'+str(poem.current_generation)+', poem:"'+render_template('poem.html', poem=poem)+'"}'

@app.route('/queue_position', methods=['GET', 'POST'])
def queue_position():
    poem = Poem.query.filter_by(id=session['poem_id']).first()
    position = app.poem_queue.get_position(poem)
    return str(position)

#@app.route('/favorites')
#def favorites():
    #return render_template('favorites.html')
