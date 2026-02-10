import math


class Node:
    def __init__(self, id_number):
        self.id = id_number
        self.layer = 0
        self.input_value = 0
        self.output_value = 0
        self.connections = []

    def activate(self):
        def sigmoid(x):
            return 1 / (1 + math.exp(-x))

        if self.layer > 0:
            self.output_value = sigmoid(self.input_value)

        for c in self.connections:
            c.to_node.input_value += c.weight * self.output_value

    def clone(self):
        clone = Node(self.id)
        clone.layer = self.layer
        return clone
