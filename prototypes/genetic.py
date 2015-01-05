
import time
from random import randint
from random import choice
import random
import nltk
from nltk.corpus import wordnet
from nltk.tokenize import word_tokenize, sent_tokenize
import fuzzy # phonetic representation 
import Levenshtein as pylev
import bisect
import os.path
import sys
import json
import operator

# Generates an outline, against which the candidate poems are measured 
def generate_outline():
    return ['winter', 'owl', 'snow', 'sadness']

tmap = {}
token2ngrams = {}
def build_markov_model(tokens, n):
    global tmap
    global token2ngrams
    for i in range(0, len(tokens) - n):
        if 'SENTENCE_START' not in tokens[i:i+n+1]:
            if tuple(tokens[i:i+n]) not in tmap:
                tmap[tuple(tokens[i:i+n])] = []
            tmap[tuple(tokens[i:i+n])].append(tokens[i+n])

            # ngrams for generating starting "seeds"
            toks = tokens[i:i+n]
            for k in toks:
                if k not in token2ngrams:
                    token2ngrams[k] = []
                token2ngrams[k].append(toks)

def get_tokens():
    symbol_stopwords = ['(', ')', '&', '$', '%', '#', '@', '*', '^', '-', '+', '_', '[',']','/', '\\', '=', '|']
    if os.path.isfile('saved_tokens.json'):
        print "loading tokens"
        with open('saved_tokens.json') as toks:
            tokens = json.load(toks)
            return tokens
    else:
        print "making tokens"
        tokens = []
        for c in corpuses:
            with open(c) as fd:
                content = fd.read()
                sentences = sent_tokenize(content)
                for s in sentences:
                    tokens.append('SENTENCE_START')
                    tokens += [word for word in word_tokenize(s) if word not in symbol_stopwords]
        with open('saved_tokens.json', 'w') as outfile:
            json.dump(tokens, outfile)
        return tokens

# Generates a candidate 
def generate_candidate_line(keyword, n, min_length, max_length):
    print "Getting starter tokens"
    rand = randint(0, len(token2ngrams[keyword])-1)
    starter_ngram = token2ngrams[keyword][rand]
    line_length = randint(min_length, max_length)
    line = list(starter_ngram)
    while len(line) < line_length:
        ngram = tuple(line[-n:]) 
        # Handle sentence ending tokens with no candidates by terminating the line
        if ngram not in tmap:
            return line
        candidates = tmap[ngram]
        nextToken = choice(candidates)
        line.append(nextToken)
    return line

# Fitness function for an individual poem 
def poem_fitness(poem):
    # Sum of parse depth for each line
    # Sum of parse depth for each pair of lines
    # Parse depth overall? Probably too slow 
    # Alliteration factor
    # Phonetic/levenshtein factor for positionally aligned (beginning, end) members of line 
    # Something involving wordnet? Comparison to outline? 
    return 1


def main():
    # initialize corpus
    tokens = get_tokens()

    print("building model 1")
    build_markov_model(tokens, 1)
    print("building model 2")
    build_markov_model(tokens, 2)
    
    # This will eventually use WordNet to turn the 1-5 word outline into 10-50 words 
    outline = generate_outline()

    start_time = time.time()
    cur_poem = []
    candidates = []
    poem_length = 8 # Number of lines in a poem
    for i in range(0,50):
        outline_word = choice(outline)
        candidate_line = generate_candidate_line(outline_word, 2, 2, 10)
        if len(cur_poem) < poem_length:
            cur_poem.append(candidate_line)
        else:
            candidates.append(cur_poem)
            cur_poem = []
    print str(len(candidates))+" candidate poems"
        
    print str(time.time() - start_time)+" seconds"
    for c in candidates:
        print c
        print ""

    generations = 10
    while generations > 0:
        # Get a fitness score for each poem 
        scored_candidates = []
        for candidate in candidates:
            fitness = poem_fitness(candidate)
            scored_candidates.append((candidate, fitness))
            
        # Sort poems by fitness 
        scored_candidates.sort(key=operator.itemgetter(1))


        # Select the top 1/n for some n for breeding
        # Separate the selected parents into pairs, and with some probability do 1 or 2 point crossover 
        # For each child, with some probability, do a mutation 
        # Repeat 
        
        generations -= 1
        


if __name__ == "__main__":
    main()

