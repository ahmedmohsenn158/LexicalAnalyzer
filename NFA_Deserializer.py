import json
import graphviz
import os

class NFA:
    def __init__(self, start_state):
        self.start_state = start_state
        self.states = set()
        self.final_states = set()
        # Transitions format: {state: {symbol: [next_states]}}
        self.transitions = {}

    def add_state(self, state_name, is_final=False):
        self.states.add(state_name)
        if is_final:
            self.final_states.add(state_name)
        if state_name not in self.transitions:
            self.transitions[state_name] = {}

    def add_transition(self, from_state, symbol, to_state):
        if from_state not in self.transitions:
            self.transitions[from_state] = {}
        
        if symbol not in self.transitions[from_state]:
            self.transitions[from_state][symbol] = []
            
        # Avoid duplicates
        if to_state not in self.transitions[from_state][symbol]:
            self.transitions[from_state][symbol].append(to_state)

def deserialize_nfa_json(file_path):
    """
    Reads a JSON file in the format specified by the CMPS403 assignment
    and returns an NFA object.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, 'r') as f:
        data = json.load(f)

    # 1. Parse Starting State
    if "startingState" not in data:
        raise ValueError("JSON invalid: Missing 'startingState' key.")
    
    start_state = data["startingState"]
    nfa = NFA(start_state)

    # 2. Iterate over keys to find state definitions
    # The JSON structure mixes metadata ("startingState") with state keys ("S0", "S1", etc.)
    for key, value in data.items():
        if key == "startingState":
            continue
        
        state_name = key
        state_data = value
        
        # 3. Parse isTerminatingState
        is_final = state_data.get("isTerminatingState", False)
        nfa.add_state(state_name, is_final)

        # 4. Parse Transitions
        # Any key inside the state object that isn't 'isTerminatingState' is a transition symbol
        for symbol, target in state_data.items():
            if symbol == "isTerminatingState":
                continue
            
            # Thompson's construction (Part 1) will produce NFA logic.
            # We handle both single string targets "S1" and list targets ["S1", "S2"]
            if isinstance(target, list):
                for t_state in target:
                    nfa.add_transition(state_name, symbol, t_state)
            else:
                nfa.add_transition(state_name, symbol, target)
                
    return nfa
def visualize_nfa(nfa, output_filename="nfa_graph"):
    """
    Generates an image of the NFA using Graphviz.
    Arguments:
        nfa: The NFA object returned by deserialize_nfa_json
        output_filename: The base name for the output file (without extension)
    """
    # Create a directed graph
    dot = graphviz.Digraph(comment='NFA Graph')
    dot.attr(rankdir='LR') # Left-to-Right layout

    # 1. Define Nodes
    for state in nfa.states:
        if state in nfa.final_states:
            dot.node(state, shape='doublecircle', style='filled', fillcolor='lightgrey')
        else:
            dot.node(state, shape='circle')

    # 2. Define invisible start node
    dot.node('__start__', shape='point')
    
    # --- THE FIX: FORCE START TO LEFT ---
    # We group the invisible start node and the actual start state 
    # into a "rank=source" block. This forces them to be at the very beginning.
    with dot.subgraph() as s:
        s.attr(rank='source')
        s.node('__start__')
        s.node(nfa.start_state)
    # ------------------------------------

    dot.edge('__start__', nfa.start_state)

    # 3. Define Edges (Transitions)
    for src, transitions in nfa.transitions.items():
        for symbol, targets in transitions.items():
            for dst in targets:
                label = symbol
                # Handle all epsilon variations
                if symbol == "" or symbol.lower() == "epsilon" or symbol == "ε" or symbol == "\u00ce\u00b5":
                    label = "ε"
                
                dot.edge(src, dst, label=label)

    # Render
    output_path = dot.render(output_filename, format='png', cleanup=True)
    print(f"Graph generated: {output_path}")
    return dot