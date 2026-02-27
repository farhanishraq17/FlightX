import random

class Connection:
    def __init__(self, from_node, to_node, weight):
        self.from_node = from_node
        self.to_node = to_node
        self.weight = weight

    def mutate_weight(self):
        if random.uniform(0, 1) < 0.1:
            self.weight = random.uniform(-2, 2)
        else:
            self.weight += random.gauss(0, 1) / 5
            if self.weight > 2:
                self.weight = 2
            if self.weight < -2:
                self.weight = -2

    def clone(self, from_node, to_node):
        clone = Connection(from_node, to_node, self.weight)
        return clone