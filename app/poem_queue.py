
from app import poem_generator, db
from models import Poem 
from config import ENVIRONMENT
import thread

MAX_CONCURRENT_POEMS = 1
class Poem_Queue:

    def __init__(self):
        print "Init poem queue"
        # call static method on virgil code that runs preprocessing etc. with config options 
        poem_generator.Poem_Generator.initialize()
        self.queue = [];
        self.running_count = 0
        self.running = []


    def get_position(self, poemid):
        for p in self.running:
            if p == poemid:
                return 0
        pos = 1
        for queue_poem_id in self.queue:
            if poemid == queue_poem_id:
                return pos
            pos += 1
        return -1 

    def add_poem(self, poem):
        print "adding poem "+str(poem.id)+" with seed words: "+str(poem.seed_words.all())
        self.queue.append(poem.id)
        self.advance()

    def advance(self):
        while self.running_count < MAX_CONCURRENT_POEMS and len(self.queue) > 0:
            poemid = self.queue.pop(0)
            print "poemid: "+str(poemid)
            poem = Poem.query.filter_by(id=poemid).first()
            print "poem about to be advanced:: "+str(poem)
            self.running_count += 1
            self.running.append(poemid)
            print "Starting poem "+str(poem.id)+" with seed words: "+str(poem.seed_words.all())
            pg = poem_generator.Poem_Generator(poem, self)

            if ENVIRONMENT == 'Development':
                thread.start_new_thread(pg.start_poem, (poem.id,))
            elif ENVIRONMENT == 'Production':
                # Throw away unexpected exceptions from the generator in produciton to prevent the queue from breaking 
                thread.start_new_thread(pg.start_poem, (poem.id,))
                #thread.start_new_thread(pg.start_poem_safe, (poem,))

    def end_poem(self, poemid):
        print "Removing poem "+str(poemid)+" from queue"
        self.running_count -= 1
        print self.running
        self.running = [s for s in self.running if s != poemid] 
        print self.running
        self.advance()
