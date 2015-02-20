from flask import render_template
from app import app
from forms import PoemForm

@app.route('/')
@app.route('/index')
def index():
    form = PoemForm() 
    return render_template('index.html', title='Virgil', form=form)

@app.route('/favorites')
def favorites():
    return render_template('favorites.html')
