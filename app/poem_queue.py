
from app import poem_generator
import thread

MAX_CONCURRENT_POEMS = 10
class Poem_Queue:
    def __init__(self):
        print "Init poem queue"
        # call static method on virgil code that runs preprocessing etc. with config options 
        poem_generator.Poem_Generator.initialize('testing')
        self.queue = [];
        self.running_count = 0

    def add_poem(self, poem):
        print MAX_CONCURRENT_POEMS
        print "adding: "+str(poem)
        self.queue.append(poem)
        print "Queue: "+str(self.queue)
        self.advance()

    #TODO: decrement running count when poem is done 
    def advance(self):
        print "Self.queue in advance: "+str(self.queue)
        while( (self.running_count < MAX_CONCURRENT_POEMS) and (len(self.queue) > 0)):
            poem = self.queue.pop(0)
            self.running_count += 1
            pg = poem_generator.Poem_Generator(poem)
            thread.start_new_thread(pg.start_poem, (poem,))

    def start_poem(self, poem):
        pg = poem_generator.Poem_Generator(poem)
        pg.start_poem(poem)

    def get_position(self, poem):
        #TODO: Actually keep track of position somehow for reporting to the user (either here or in the model)
        return 5
