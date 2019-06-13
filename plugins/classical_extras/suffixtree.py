# -*- coding: utf-8

"""
Search longest common substrings using generalized suffix trees built with Ukkonen's algorithm

Author: Ilya Stepanov <code at ilyastepanov.com>

(c) 2013

Modified by <a href="https://github.com/MetaTunes">Mark Evens</a> as part of Picard Classical Extras project
Not for stand-alone use - use the original code
Accepts list or string inputs, but returns list outputs
Changed to allow a range of different special characters in case $ is in a string
(c) 2018
"""

import sys

END_OF_STRING = sys.maxsize

class SuffixTreeNode:
    """
    Suffix tree node class. Actually, it also respresents a tree edge that points to this node.
    """
    new_identifier = 0

    def __init__(self, start=0, end=END_OF_STRING):
        self.identifier = SuffixTreeNode.new_identifier
        SuffixTreeNode.new_identifier += 1

        # suffix link is required by Ukkonen's algorithm
        self.suffix_link = None

        # child edges/nodes, each dict key represents the first letter of an edge
        self.edges = {}

        # stores reference to parent
        self.parent = None

        # bit vector shows to which strings this node belongs
        self.bit_vector = 0

        # edge info: start index and end index
        self.start = start
        self.end = end

    def add_child(self, key, start, end):
        """
        Create a new child node

        Agrs:
            key: a char that will be used during active edge searching
            start, end: node's edge start and end indices

        Returns:
            created child node

        """
        child = SuffixTreeNode(start=start, end=end)
        child.parent = self
        self.edges[key] = child
        return child

    def add_exisiting_node_as_child(self, key, node):
        """
        Add an existing node as a child

        Args:
            key: a char that will be used during active edge searching
            node: a node that will be added as a child
        """
        node.parent = self
        self.edges[key] = node

    def get_edge_length(self, current_index):
        """
        Get length of an edge that points to this node

        Args:
            current_index: index of current processing symbol (usefull for leaf nodes that have "infinity" end index)
        """
        return min(self.end, current_index + 1) - self.start

    def __str__(self):
        return 'id=' + str(self.identifier)


class SuffixTree:
    """
    Generalized suffix tree
    """

    def __init__(self):
        # the root node
        self.root = SuffixTreeNode()

        # all strings are concatenaited together. Tree's nodes stores only indices
        self.input_string = []

        # number of strings stored by this tree
        self.strings_count = 0

        # list of tree leaves
        self.leaves = []

    def append_string(self, input_string, special_char):
        """
        Add new string to the suffix tree
        """
        start_index = len(self.input_string)
        current_string_index = self.strings_count

        # each sting should have a unique ending
        input_string += special_char + str(current_string_index)

        # gathering 'em all together
        self.input_string += input_string
        self.strings_count += 1

        # these 3 variables represents current "active point"
        active_node = self.root
        active_edge = 0
        active_length = 0

        # shows how many
        remainder = 0

        # new leaves appended to tree
        new_leaves = []

        # main circle
        for index in range(start_index, len(self.input_string)):
            previous_node = None
            remainder += 1
            while remainder > 0:
                if active_length == 0:
                    active_edge = index

                if self.input_string[active_edge] not in active_node.edges:
                    # no edge starting with current char, so creating a new leaf node
                    leaf_node = active_node.add_child(self.input_string[active_edge], index, END_OF_STRING)

                    # a leaf node will always be leaf node belonging to only one string
                    # (because each string has different termination)
                    leaf_node.bit_vector = 1 << current_string_index
                    new_leaves.append(leaf_node)

                    # doing suffix link magic
                    if previous_node is not None:
                        previous_node.suffix_link = active_node
                    previous_node = active_node
                else:
                    # ok, we've got an active edge
                    next_node = active_node.edges[self.input_string[active_edge]]

                    # walking down through edges (if active_length is bigger than edge length)
                    next_edge_length = next_node.get_edge_length(index)
                    if active_length >= next_node.get_edge_length(index):
                        active_edge += next_edge_length
                        active_length -= next_edge_length
                        active_node = next_node
                        continue

                    # current edge already contains the suffix we need to insert.
                    # Increase the active_length and go forward
                    if self.input_string[next_node.start + active_length] == self.input_string[index]:
                        active_length += 1
                        if previous_node is not None:
                            previous_node.suffix_link = active_node
                        previous_node = active_node
                        break

                    # splitting edge
                    split_node = active_node.add_child(
                        self.input_string[active_edge],
                        next_node.start,
                        next_node.start + active_length
                    )
                    next_node.start += active_length
                    split_node.add_exisiting_node_as_child(self.input_string[next_node.start], next_node)
                    leaf_node = split_node.add_child(self.input_string[index], index, END_OF_STRING)
                    leaf_node.bit_vector = 1 << current_string_index
                    new_leaves.append(leaf_node)

                    # suffix link magic again
                    if previous_node is not None:
                        previous_node.suffix_link = split_node
                    previous_node = split_node

                remainder -= 1

                # follow suffix link (if exists) or go to root
                if active_node == self.root and active_length > 0:
                    active_length -= 1
                    active_edge = index - remainder + 1
                else:
                    active_node = active_node.suffix_link if active_node.suffix_link is not None else self.root

        # update leaves ends from "infinity" to actual string end
        for leaf in new_leaves:
            leaf.end = len(self.input_string)
        self.leaves.extend(new_leaves)

    def find_longest_common_substrings(self, special_char):
        """
        Search longest common substrings in the tree by locating lowest common ancestors that belong to all strings
        """

        # all bits are set
        success_bit_vector = 2 ** self.strings_count - 1

        lowest_common_ancestors = []

        # going up to the root
        for leaf in self.leaves:
            node = leaf
            while node.parent is not None:
                if node.bit_vector != success_bit_vector:
                    # updating parent's bit vector
                    node.parent.bit_vector |= node.bit_vector
                    node = node.parent
                else:
                    # hey, we've found a lowest common ancestor!
                    lowest_common_ancestors.append(node)
                    break

        longest_common_substrings = []
        longest_length = 0

        # need to filter the result array and get the longest common strings
        for common_ancestor in lowest_common_ancestors:
            common_substring = []
            node = common_ancestor
            while node.parent is not None:
                label = self.input_string[node.start:node.end]
                common_substring = label + common_substring
                node = node.parent
            # remove unique endings (<special_char><number>), we don't need them anymore ...
            if special_char in common_substring:
                common_substring = common_substring[:common_substring.index(special_char)]
            # ... also in input strings to avoid mutation problems
            if len(common_substring) > longest_length:
                longest_length = len(common_substring)
                longest_common_substrings = [common_substring]
            elif len(common_substring) == longest_length and common_substring not in longest_common_substrings:
                longest_common_substrings.append(common_substring)

        return longest_common_substrings


def multi_lcs(strings_list):
    """
    Returns longest common string (or list) for a list of strings (or lists)
    :param strings_list: a list of lists or a list of strings
    :return: a list of longest common strings (or lists)
    (more than one is possible if they are distinct and of the same length)
    """

    if not isinstance(strings_list, list):
        return {'response': [], 'error': 'Argument is not a list'}
    arg_type = type(strings_list[0])
    for item in strings_list:
        if not isinstance(item, arg_type):
            return {'response': [], 'error': 'List members are not of the same type'}
    if arg_type is not list and arg_type is not str:
        return {'response': [], 'error': 'List members are not lists or strings'}

    suffix_tree = SuffixTree()
    special_char = None
    for char in ['|', '$', '#', '%', '@', '_']:
        test_strings = [x for x in strings_list if char in x]
        if not test_strings:
            special_char = char
            break
    if special_char:
        # print special_char
        for s in strings_list:
            if arg_type is list:
                s_copy = s[:]   # to avoid mutating input lists
            else:
                s_copy = s
            suffix_tree.append_string(s_copy, special_char)
        lcs = suffix_tree.find_longest_common_substrings(special_char)
    else:
        return {'response': [], 'error': 'Too many special characters'}
    if arg_type is list:
        if lcs:
            return {'response': lcs[0]}
        else:
            return {'response': [], 'error': 'Internal suffix tree problems'}
    else:
        if lcs:
            return {'response': [''.join(x) for x in lcs[0]]}
        else:
            return {'response': [], 'error': 'Internal suffix tree problems'}

