import math
import pandas as pd
import matplotlib.pyplot as plt

import numpy as np
import numpy.linalg as lin


class Bridge():
    def __init__(self):
        self.name = 'Bridge'
        self.nodes = []
        self.members = []
        self.num_nodes = 0
        self.num_members = 0
        self.num_displacements = 0
        self.left_node = None
        self.right_node = None
        
        self.is_solved = False        
        self.load = 0
        self.internal_forces = None
        self.efficiency = 0      
        self.broken_members = None  


    def add_node(self, node):
        self.num_nodes += 1
        self.num_displacements += int(node.support_x) + int(node.support_y)
        self.nodes.append(node)
    
    def remove_node(self, node):
        self.num_nodes -= 1
        self.nodes.remove(node)

    def add_member(self, member):
        self.num_members += 1
        if member not in self.members:
            self.members.append(member)

    def remove_member(self, member):
        self.num_members -= 1
        self.members.remove(member)

    def set_members(self, list_of_members):
        self.members = list_of_members

    def get_members(self):
        return self.members

    def get_nodes(self):
        return self.nodes

    def set_name(self, value):
        self.name = value

    def get_name(self):
        return self.name

    def get_node(self, node_id):
        for node in self.get_nodes():
            if node.get_id() == node_id:
                return node

    def get_member(self, node_a, node_b):
        for member in self.get_members():
            if node_a.get_id() == member.get_nodeA().get_id() and node_b.get_id() == member.get_nodeB().get_id() or node_a.get_id() == member.get_nodeB().get_id() and node_b.get_id() == member.get_nodeA().get_id():
                return member

    def get_member_by_id(self, id):
        for member in self.get_members():
            if member.get_id() == id:
                return member
            
    def load_from_file(self, filename):
        # Load the file into an array of lines
        with open(filename, 'r') as file:
            lines = file.readlines()
        
        # Set the bridge name (from the first line of the input file)
        name = lines[0].split(' ')[0]
        self.set_name(name)

        # Get the number of nodes and members
        num_nodes = lines[1].split(' ')[0]
        num_members = lines[2].split(' ')[0]


        # Search for Locations of Key Inputs
        for i, s in enumerate(lines):
            if 'Node position' in s:  # Location of Nodes
                node_position = i
            elif 'Elements' in s:  # Location of Members
                element_position = i
            elif 'Displacements' in s:  # Location of X-Y Displacements
                displacement_position = i
        

        # Add Nodes
        for i in range(node_position+2, node_position+2+int(num_nodes)):
            row = lines[i].split('\t')
            node = Node(str(row[0]), int(row[1]), int(row[2]), False, False)
            self.add_node(node)


        # Add Members            
        for i in range(element_position+2, element_position+2+int(num_members)):
            row = lines[i].split('\t')

            nodeA = self.get_node(row[1].strip())
            nodeB = self.get_node(row[2].strip())
            member = Member(row[0], nodeA, nodeB)
            self.add_member(member)


        # Add Displacements
        num_displacements = int(lines[displacement_position+1].split(' ')[0])
        for i in range(displacement_position+3, displacement_position + 3 + num_displacements):
            row = lines[i].split('\t')
            node = self.get_node(row[0])
            if row[1] == '1':
                node.set_support_x(True)
                self.num_displacements += 1
            elif row[1] == '2':
                node.set_support_y(True)
                self.num_displacements += 1

    def save_to_file(self, outfile):
        with open(outfile, 'w') as file:
            file.write(str(self.name) + ' ' + '% Your Names\n')
            file.write(str(self.num_nodes) + ' ' + '% Number of Nodes\n')
            file.write(str(self.num_members) + ' ' + '% Number of Elements\n\n\n')
            file.write('Node position\nnumber\txvalue\tyvalue\n')
            for node in self.nodes:
                file.write(str(node.id) + '\t' + str(node.x) + '\t' + str(node.y) + '\n')
            
            file.write('\n\n\nElements\nnumber\tnode1\tnode2\n')
            for member in self.members:
                file.write(str(member.id) + '\t' + str(member.A.get_id()) + '\t' + str(member.B.get_id()) + '\n')

            file.write('\n\n\nDisplacements\n' + str(self.num_displacements) + ' % Number of displacement boundary conditions\n')
            file.write('node#\t(x=1, y=2)\tvalue\n')
            for node in self.nodes:
                if node.get_support_x():
                    file.write(str(node.get_id()) + '\t' + '1\t0' + '\n')
                if node.get_support_y():
                    file.write(str(node.get_id()) + '\t' + '2\t0' + '\n')

    def get_load_nodes(self):
        # The load is distributed on every node along the roadway of the truss, except for the far left and far right nodes
        smallest_val = float('inf')
        smallest_node = None

        biggest_val = float('-inf')
        biggest_node = None

        for node in self.get_nodes():
            if node.get_y() == 0:
                if node.get_x() < smallest_val:
                    smallest_val = node.get_x()
                    smallest_node = node
                elif node.get_x() > biggest_val:
                    biggest_val = node.get_x()
                    biggest_node = node

        self.left_node = smallest_node
        self.right_node = biggest_node
        return [node for node in self.get_nodes() if node is not biggest_node and node is not smallest_node and node.get_y() == 0]

    def get_left_node(self):
        return self.left_node

    def get_right_node(self):
        return self.right_node

    def get_total_length(self):
        total = 0
        for member in self.get_members():
            total += member.get_length()
        return total

    def get_neighbor_nodes(self, node):
        nodes = []
        for member in self.get_members():
            if member.get_nodeA().get_id() == node.get_id():
                nodes.append(member.get_nodeB())
            elif member.get_nodeB().get_id() == node.get_id():
                nodes.append(member.get_nodeA())
        return nodes

    def apply_load_to_nodes(self):
        for node in self.load_nodes:
            node.set_load(self.bridge_load / len(self.load_nodes))  # distribute the load equally over each loading node
        
    
    def solve(self):
        self.load_nodes = self.get_load_nodes()
        self.bridge_load = 0  # Set the initial load        
        # Construct the matrix (excluding the constraints)
        matrix_headers = []
        for node in self.get_nodes():
            matrix_headers.append(str(node.get_id()) + 'x')
            matrix_headers.append(str(node.get_id()) + 'y')
        
        # matrix = pd.DataFrame(columns=[i+1 for i in range(len(self.nodes))], index=[i+1 for i in range(len(self.nodes))])
        columns = ['F' + str(i.get_id()) for i in self.members]
        
        matrix = pd.DataFrame(0, columns=columns, index=matrix_headers)

        # Add the support reactions to the matrix (vertical and horizontal get different reactions)

        for node in self.get_nodes():
            if node.get_support_x():
                columns.append('R' + str(node.get_id()) + 'x')
                matrix.loc[node.get_id() + 'x', 'R' + str(node.get_id()) + 'x'] = 1
            if node.get_support_y():
                columns.append('R' + str(node.get_id()) + 'x')
                matrix.loc[node.get_id() + 'y', 'R' + str(node.get_id()) + 'y'] = 1

        matrix = matrix.fillna(0)

        for member in self.members:
            a = member.get_nodeA()
            b = member.get_nodeB()

            a_horizontal = (b.get_x() - a.get_x()) / member.get_length()            
            a_vertical = (b.get_y() - a.get_y()) / member.get_length()
            
            b_horizontal = (a.get_x() - b.get_x()) / member.get_length()
            b_vertical = (a.get_y() - b.get_y()) / member.get_length()
            
            matrix.loc[a.get_id() + 'x', 'F' + str(member.get_id())] = a_horizontal
            matrix.loc[a.get_id() + 'y', 'F' + str(member.get_id())] = a_vertical
            
            matrix.loc[b.get_id() + 'x', 'F' + str(member.get_id())] = b_horizontal
            matrix.loc[b.get_id() + 'y', 'F' + str(member.get_id())] = b_vertical

        load_matrix = pd.Series(0, index=matrix.index)
        for node in self.get_load_nodes():
            load_matrix.loc[node.get_id() + 'y'] = 1 / len(self.load_nodes)

        result = pd.Series(np.linalg.lstsq(matrix,load_matrix, rcond=None)[0], index=columns).filter(like='F')

        broken_members = result.where(np.isclose(result.abs(), result.abs().max(), rtol=1e-03, atol=1e-03, equal_nan=False)).dropna()

        total_load = 500000 / abs(broken_members.max())
      
        self.load = total_load

        self.is_solved = True
        self.internal_forces = result * total_load
        self.efficiency = self.load / self.get_total_length()
        self.broken_members = broken_members
        return
        # return self.internal_forces, efficiency



class Node():
    def __init__(self, node_id, xCoord, yCoord, xSupport, ySupport):
        assert 0 <= xSupport <= 1 and 0 <= ySupport <= 1 
        self.id = str(node_id)
        self.load = 0
        self.x = int(xCoord)
        self.y = int(yCoord)
        self.support_x = xSupport
        self.support_y = ySupport
        self.load_angle = None

    def set_x(self, x_coord):
        self.x = x_coord

    def set_y(self, y_coord):
        self.y = y_coord

    def set_support_x(self, val):
        assert(val == False or val == True)
        self.support_x = val

    def set_support_y(self, val):
        assert(val == False or val == True)
        self.support_y = val

    def get_support_x(self):
        return self.support_x

    def get_support_y(self):
        return self.support_y

    def set_load(self, val):
        assert val >= 0
        self.load = val

    def get_load(self):
        return self.load

    def set_load_angle(self, angle):
        self.load_angle = angle

    def get_x(self):
        return self.x

    def get_y(self):
        return self.y

    def get_id(self):
        return self.id

    def __str__(self):
        return 'Node (ID: ' + self.get_id() + ') at (' + str(self.x) + ',' + str(self.y) +')\nLoad: ' + str(self.load) + '\nX-Support: ' + str(self.support_x) + '\nY-Support: ' + str(self.support_y) + '\n\n'


class Member():
    def __init__(self, member_id, nodeA, nodeB):
        self.id = member_id
        self.A = nodeA
        self.B = nodeB
        self.length = self.get_length
        self.angle = self.get_angle

    def get_length(self):
        return math.sqrt(pow(self.B.y - self.A.y, 2) + pow(self.B.x - self.A.x, 2))

    def get_angle(self):
        A = self.A
        B = self.B

        return math.atan( (B.y - A.y) / (B.x - A.x) )

    def get_nodeA(self):
        return self.A

    def get_nodeB(self):
        return self.B

    def get_id(self):
        return self.id 

    def __str__(self):
        # return 'MEMBER BETWEEN THE FOLLOWING NODES:\n' + str(self.A) + str(self.B)

        return 'Length:' + str(self.get_length())