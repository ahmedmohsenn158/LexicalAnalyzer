import json
from operator import ne
import graphviz
import os

from IPython.core.display_functions import display
from collections import deque

import NFA_Deserializer as nfa_tools

def BuildDFA(input_nfa_json, output_dfa_json, output_min_dfa_json):
    try:
        # 1. Deserialize the JSON NFA
        my_nfa = nfa_tools.deserialize_nfa_json(input_nfa_json)
        print(f"Loaded NFA with {len(my_nfa.states)} states.")
        
        # 2. Visualize
        dot = nfa_tools.visualize_nfa(my_nfa, output_filename="nfa_visualization")

        # 3. Display in Notebook
        display(dot)

        # 4. Convert to DFA 
        print("3. Converting NFA to DFA...")
        my_dfa = convert_nfa_to_dfa(my_nfa)
        print(f"   -> Generated DFA with {len(my_dfa.states)} states.")

        # 4. Visualize DFA
        print("4. Visualizing DFA...")
        visualize_graph(my_dfa, "dfa_graph", "DFA")

        # 5. Output JSON
        print("5. DFA JSON Output:")
        print(my_dfa.to_json())
        
        # 6. Save to file
        with open(output_dfa_json, "w") as f:
            f.write(my_dfa.to_json())
        print("   -> Saved to json file")

        min_dfa = minimize_dfa(my_dfa)
        print(f"Minimized DFA has {len(min_dfa.states)} states.")

        # 7. Visualize DFA
        print("4. Visualizing Min-DFA...")
        visualize_graph(min_dfa, "min_dfa_graph", "MIN_DFA")

        # 8. Output JSON
        print("5. MIN_DFA JSON Output:")
        print(min_dfa.to_json())
        
        # 9. Save to file
        with open(output_min_dfa_json, "w") as f:
            f.write(min_dfa.to_json())
        print("  -> Saved to json file")

    except Exception as e:
        print(f"Error: {e}")


class DFA:
    def __init__(self):
        self.start_state = None
        self.states = set()
        self.final_states = set()
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
        self.transitions[from_state][symbol] = to_state

    def to_json(self):
        """
        Formats the DFA to the specific JSON format required 
        """
        output = {
            "startingState": self.start_state
        }

        sorted_states = sorted(list(self.states))

        for state in sorted_states:
            state_data = {
                "isTerminatingState": state in self.final_states
            }

            if state in self.transitions:
                for symbol, target in self.transitions[state].items():
                    state_data[symbol] = target

            output[state] = state_data

        return json.dumps(output, indent=4)


#       THE ALGORITHMS
def get_epsilon_closure(nfa, states_set):
    """
    Finds all states reachable from 'states_set' using only epsilon transitions.
    DFS approach.
    """
    stack = list(states_set)
    # result set starts with the original states
    closure = set(states_set)

    while stack:
        current_state = stack.pop()

        # Check if there are epsilon transitions from this state
        if current_state in nfa.transitions:
            for symbol, targets in nfa.transitions[current_state].items():
                if symbol == "" or symbol.lower() == "epsilon" or symbol == "\u00ce\u00b5" or symbol == "\u03B5":
                    #loop on all the states reachable by epsilon transition
                    for next_state in targets:
                        if next_state not in closure:
                            #add the state to the result and workList
                            closure.add(next_state)
                            stack.append(next_state)
    return closure


def move(nfa, states_set, symbol):
    """
    Finds all states reachable from 'states_set' on a specific input 'symbol'.
    """
    result_states = set()

    for state in states_set:
        if state in nfa.transitions:
            if symbol in nfa.transitions[state]:
                # Add all destinations
                for target in nfa.transitions[state][symbol]:
                    result_states.add(target)

    return result_states


def convert_nfa_to_dfa(nfa):
    """
    Converts an NFA object to a DFA object using Subset Construction.
    """
    dfa = DFA()

    # 1. Determine the Alphabet (all symbols except epsilon)
    alphabet = set()
    for src, trans in nfa.transitions.items():
        for symbol in trans.keys():
            if symbol != "" and symbol.lower() != "epsilon" and symbol != "\u00ce\u00b5" and symbol != "\u03B5":
                alphabet.add(symbol)

    # 2. Calculate Initial State (Start State + Epsilon Closure)
    start_closure = get_epsilon_closure(nfa, {nfa.start_state})

    # Helper to generate consistent names 
    dfa_state_counter = 0
    # a frozen set to store the name of the state in DFA and the corrosponding set of NFA states
    states_map = {}
    # Queue for processing
    worklist = deque()

    # Setup Start State
    start_frozen = frozenset(start_closure)
    states_map[start_frozen] = "S0" 
    worklist.append(start_frozen)

    dfa.start_state = "S0"
    dfa_state_counter += 1

    # Mark if start is final
    is_start_final = any(s in nfa.final_states for s in start_closure)
    dfa.add_state("S0", is_start_final)

    # Keep track of processed states
    processed_sets = set()

    # 3. Main Loop
    while worklist:
        current_set = worklist.popleft()
        current_name = states_map[current_set]

        if current_set in processed_sets:
            continue
        #mark this state as processed
        processed_sets.add(current_set)

        # For every symbol in the alphabet
        for char in sorted(list(alphabet)):
            # A. Move like a normal NFA move
            move_result = move(nfa, current_set, char)

            # B. Epsilon Closure again to get all states that are reachable using epsilon moves
            final_destination_set = get_epsilon_closure(nfa, move_result)

            if not final_destination_set:
                #  Handle Dead State (Empty set) if explicit dead states are required.
                continue

            destination_frozen = frozenset(final_destination_set)

            # C. Check if this state was produced before
            if destination_frozen not in states_map:
                # Create new name
                new_name = f"S{dfa_state_counter}"
                states_map[destination_frozen] = new_name
                dfa_state_counter += 1

                # Determine if final
                is_final = any(s in nfa.final_states for s in destination_frozen)
                dfa.add_state(new_name, is_final)

                # Add to worklist
                worklist.append(destination_frozen)

            # D. Add Transition to the DFA Graph
            dfa.add_transition(current_name, char, states_map[destination_frozen])

    return dfa
def visualize_graph(automaton, filename, title):
    try:
        dot = graphviz.Digraph(comment=title)
        dot.attr(rankdir='LR')
        for state in automaton.states:
            if state in automaton.final_states:
                dot.node(state, shape='doublecircle')
            else:
                dot.node(state, shape='circle')
        
        dot.node('__start__', shape='point')
        dot.edge('__start__', automaton.start_state)
        
        for src, trans in automaton.transitions.items():
            for symbol, targets in trans.items():
                # Handle DFA (target is string) vs NFA (target is list)
                target_list = targets if isinstance(targets, list) else [targets]
                for dst in target_list:
                    label = "ε" if symbol == "" or symbol.lower() == "\u03B5" or symbol == "\u00ce\u00b5" else symbol
                    dot.edge(src, dst, label=label)
        
        output_path = dot.render(filename, format='png', cleanup=True)
        print(f"   -> Image saved to: {output_path}")
    except Exception as e:
        print(f"   -> Graphviz error (ignore if just testing logic): {e}")

def minimize_dfa(dfa):
    """
    Minimizes a DFA using Partition Refinement (same as lecture)
    """
    # 1. GET ALPHABET
    alphabet = set()
    for s in dfa.transitions:
        for char in dfa.transitions[s]:
            alphabet.add(char)
    #alphabet = sorted(list(alphabet))
    # 2. INITIAL PARTITION: [ {Non-Finals}, {Finals} ]
    final_states = set(dfa.final_states)
    non_final_states = dfa.states - final_states

    # a list that stores all partitions
    partitions = []
    if non_final_states: partitions.append(non_final_states)
    if final_states: partitions.append(final_states)

    did_split_occur = True
    while did_split_occur:
        did_split_occur = False
        new_partitions = []

        for group in partitions:
            if len(group) <= 1:
                new_partitions.append(group)
                continue
            
            #select the first group member as a reference state
            group_list = list(group)
            first = group_list[0]

            #split the group into two groups one for states that match the reference transactions 
            #and one for states that don't
            matching_group = {first}
            non_matching_group = set()

            #helper function to get the partition the state belongs to
            def get_partition_index(target_state,current_partitions):
                if target_state is None:
                    return -1
                for idx, part in enumerate(current_partitions):
                    if target_state in part:
                        return idx
                return -1
            
            #chack each state in the group against the reference state
            for i in range(1, len(group_list)):
                state = group_list[i]
                is_matching = True

                for char in alphabet:
                    #where does the group reference go on the current input
                    first_target = dfa.transitions.get(first, {}).get(char)
                    #where does the current state go on the current input
                    state_target = dfa.transitions.get(state, {}).get(char)
                    
                    #which group does the reference go to
                    first_part = get_partition_index(first_target, partitions)
                    #which group does the current state go to
                    state_part = get_partition_index(state_target, partitions)

                    if first_part != state_part:
                        is_matching = False
                        break

                #add the state to the correct group
                if is_matching:
                    matching_group.add(state)
                else:
                    non_matching_group.add(state)
            
            #add the groups to the new partitions
            if non_matching_group:
                new_partitions.append(matching_group)
                new_partitions.append(non_matching_group)
                did_split_occur = True
            else:
                new_partitions.append(group)

        #check for the newely updated partitions
        partitions = new_partitions

        if not did_split_occur:
            break
    
    # 4. reconstruct the DFA from the partitions created
    min_dfa = DFA()
    state_name_map = {}
    # add states and finish states
    for i, group in enumerate(partitions):
        new_state_name = f"S{i}"
        is_final = any(state in dfa.final_states for state in group)
        min_dfa.add_state(new_state_name, is_final)

        #finding the start state
        if dfa.start_state in group:
            min_dfa.start_state = new_state_name

        #map old states to new state names
        for state in group:
            state_name_map[state] = new_state_name
    # add transitions
    for group in partitions:
        #one state of the joined group to represent the whole group
        rep = next(iter(group))
        #new joined state name
        source_name = state_name_map[rep]
        if rep in dfa.transitions:
            for char, target in dfa.transitions[rep].items():
                if target in state_name_map:
                    #add the transition from the new state to the new target state
                    min_dfa.add_transition(source_name, char, state_name_map[target])
    
    return min_dfa

        

