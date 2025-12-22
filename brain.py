import random
import node
import connection


class Brain:
    def __init__(self, inputs, clone=False):
        self.inputs = inputs
        self.nodes = []
        self.connections = []
        self.layers = 2
        self.net = []
        self.bias_index = self.inputs
        self.output_index = self.inputs + 1
        self.bias_node = None
        self.output_node = None

        if not clone:
            # Input nodes
            for i in range(self.inputs):
                self.nodes.append(node.Node(i))
                self.nodes[i].layer = 0

            # Bias node
            self.nodes.append(node.Node(self.bias_index))
            self.nodes[self.bias_index].layer = 0
            self.bias_node = self.nodes[self.bias_index]

            # Output node
            self.nodes.append(node.Node(self.output_index))
            self.nodes[self.output_index].layer = 1
            self.output_node = self.nodes[self.output_index]

            # Connections
            for i in range(self.output_index + 1):
                self.connections.append(
                    connection.Connection(self.nodes[i], self.output_node, random.uniform(-1, 1))
                )

    def connect_nodes(self):
        for n in self.nodes:
            n.connections = []

        for c in self.connections:
            c.from_node.connections.append(c)

    def generate_net(self):
        self.connect_nodes()
        self.net = []
        for l in range(self.layers):
            for n in self.nodes:
                if n.layer == l:
                    self.net.append(n)

    def feed_forward(self, vision):
        for i in range(self.inputs):
            self.nodes[i].output_value = vision[i]

        bias = self.bias_node if self.bias_node else self.get_node(self.bias_index)
        bias.output_value = 1

        for n in self.net:
            n.activate()

        output_node = self.output_node if self.output_node else self.get_node(self.output_index)
        output = output_node.output_value

        for n in self.nodes:
            n.input_value = 0

        return output

    def clone(self):
        clone = Brain(self.inputs, True)

        for n in self.nodes:
            clone.nodes.append(n.clone())

        for c in self.connections:
            clone.connections.append(
                c.clone(
                    clone.get_node(c.from_node.id),
                    clone.get_node(c.to_node.id),
                )
            )

        clone.layers = self.layers
        clone.bias_node = clone.get_node(self.bias_index)
        clone.output_node = clone.get_node(self.output_index)
        clone.generate_net()
        return clone

    def get_node(self, node_id):
        for n in self.nodes:
            if n.id == node_id:
                return n

    def mutate(self):
        if random.random() < 0.8:
            for c in self.connections:
                c.mutate_weight()
