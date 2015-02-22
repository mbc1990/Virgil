import sys
import time
from random import randint
from random import choice
import random
from nltk.corpus import wordnet
from nltk.tokenize import word_tokenize, sent_tokenize
import fuzzy
import Levenshtein as pylev
import os.path
import json
import operator
import math
from random import shuffle
from stat_parser import Parser
parser = Parser()

class Poem_Generator:

    ngram2following_tokens = {} # tuple of ngram -> list of tokens that follow it in the corpus (used in markov chain) 
    token2ngrams = {} # token -> ngrams it is a member of
    height_memo = {} # tuple -> parse height  
    
    def __init__(self, poem):
        print "Poem generator init"
        #TODO: Use the actual paramters here
        self.generations = 5 # Number of selection-breeding processes
        self.breeding_fraction = .35 # Top fraction of candidates selected to breed
        self.mutation_prob = .05 # Probability that a child will be mutated
        self.poem_length = 6 # Number of lines in a poem
        self.starting_population_size = 100 # Number of poems the algorithm begins with 
        self.seed_words = ['cat', 'winter'] # Input "idea"
        self.poem = poem #ORM object that will be updated as the poem is generated

    @staticmethod
    def initialize(config):
        print "Static generator methods initialized!"

    # Load parse height cache
    @staticmethod 
    def load_parse_height_cache():
        if os.path.isfile('parse_height_cache.json'):
            with open('parse_height_cache.json', 'r') as fp:
                height_cache_saved = json.load(fp)
                for key in height_cache_saved['key_map'].keys():
                    tup_key = tuple(height_cache_saved['key_map'][key])
                    height_value = height_cache_saved['saved_cache'][key]
                    height_memo[tup_key] = height_value

    # Save the updated height cache
    @staticmethod
    def dump_parse_height_cache():
        with open('parse_height_cache.json', 'w') as fp:
            key_map_counter = 0
            key_map = {}
            saved_cache = {}
            for key in height_memo.keys():
                key_map[key_map_counter] = key 
                saved_cache[key_map_counter] = height_memo[key]
                key_map_counter += 1
            output = {'key_map': key_map, 'saved_cache': saved_cache}
            json.dump(output, fp)

    def start_poem(self, poem):
        print "Starting new poem"
