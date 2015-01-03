
from pygraph.classes.graph import graph
from nltk.tokenize import word_tokenize, sent_tokenize
import sys

class Word_Graph:
    def __init__(self, tokens, n_size):
        # For internal reference to node payloads 
        self.tuple2node_id = {}
        self.node_id2tuple = {}
        self.node_id_counter = 0
        self.edge2weight = {} # used for keeping track of edge weights as they're updated #TODO: This can be removed

        self.word_graph = graph()
        self.build_graph(tokens, n_size)

        print str(self.word_graph)

    def build_graph(self, tokens, n):
        for i in range(0, len(tokens) - n):
            if 'SENTENCE_START' not in tokens[i:i+n+1]:
                
                cur_state = tuple(tokens[i:i+n])
                next_state = tuple(tokens[i+1:i+n+1])

                if cur_state not in self.tuple2node_id:
                    self.tuple2node_id[cur_state] = self.node_id_counter
                    self.node_id2tuple[self.node_id_counter] = cur_state
                    self.node_id_counter += 1
                
                if next_state not in self.tuple2node_id:
                    self.tuple2node_id[next_state] = self.node_id_counter
                    self.node_id2tuple[self.node_id_counter] = next_state 
                    self.node_id_counter += 1

                # The IDs used by the graph
                cur_state_id = self.tuple2node_id[cur_state]
                next_state_id = self.tuple2node_id[next_state]

                # Increment the edge weight by 1 every time the states (token-tuples) are found adjacent to each other 
                # TODO: refactor edge2weight out
                edge_weight = 1
                if (cur_state_id, next_state_id) in self.edge2weight:
                    edge_weight += self.edge2weight[(cur_state_id, next_state_id)]
                self.edge2weight[(cur_state_id, next_state_id)] = edge_weight

                if not self.word_graph.has_node(cur_state_id):
                    self.word_graph.add_node(cur_state_id)

                if not self.word_graph.has_node(next_state_id):
                    self.word_graph.add_node(next_state_id)

                # If the edge already exists, delete it and add the new edge with incremented weight
                if self.word_graph.has_edge((cur_state_id, next_state_id)):
                    self.word_graph.del_edge((cur_state_id, next_state_id))
                self.word_graph.add_edge((cur_state_id, next_state_id), wt=edge_weight)
