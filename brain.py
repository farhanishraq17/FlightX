import random
import node
import connection


class Brain:
    def __init__(self, inputs, hidden_layers=None, clone=False):
        self.inputs = inputs
        self.hidden_layers = hidden_layers if hidden_layers else []
        self.nodes = []
        self.connections = []
        self.layers = 2 + len(self.hidden_layers)
        self.net = []
        
        # Node IDs - Always calculate these
        self.bias_index = self.inputs
        
        # Calculate output node index based on total nodes
        # Inputs (0 to inputs-1) + Bias (inputs) + Hidden Nodes + Output
        current_id = self.inputs + 1
        for h_count in self.hidden_layers:
            current_id += h_count
        self.output_index = current_id
        
        if not clone:
            # Reset current_id for actual node creation
            current_id = self.inputs + 1
            
            # Input nodes (Layer 0)
            for i in range(self.inputs):
                n = node.Node(i)
                n.layer = 0
                self.nodes.append(n)

            # Bias node (Layer 0)
            n_bias = node.Node(self.bias_index)
            n_bias.layer = 0
            self.nodes.append(n_bias)
            self.bias_node = n_bias

            # Hidden layers
            hidden_node_ids = []
            for i, h_count in enumerate(self.hidden_layers):
                layer_ids = []
                for _ in range(h_count):
                    n = node.Node(current_id)
                    n.layer = i + 1  # 0 is input, so hidden starts at 1
                    self.nodes.append(n)
                    layer_ids.append(current_id)
                    current_id += 1
                hidden_node_ids.append(layer_ids)

            # Output node (Last Layer)
            n_out = node.Node(self.output_index)
            n_out.layer = self.layers - 1
            self.nodes.append(n_out)
            self.output_node = n_out

            # Connections: Fully connected between adjacent layers
            # Layer 0 (Inputs+Bias) -> Layer 1 (First Hidden or Output)
            prev_layer_nodes = [n for n in self.nodes if n.layer == 0]
            
            # Connect through hidden layers
            for i in range(len(self.hidden_layers)):
                current_layer_nodes = [n for n in self.nodes if n.layer == i + 1]
                for prev in prev_layer_nodes:
                    for curr in current_layer_nodes:
                        self.connections.append(
                            connection.Connection(prev, curr, random.uniform(-1, 1))
                        )
                prev_layer_nodes = current_layer_nodes

            # Connect last layer to output
            for prev in prev_layer_nodes:
                self.connections.append(
                    connection.Connection(prev, self.output_node, random.uniform(-1, 1))
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
        clone = Brain(self.inputs, self.hidden_layers, True)

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
