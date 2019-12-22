import math
import matplotlib.pyplot as plt
import re

from io import StringIO

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from sapy import displmethod
from sapy import element
from sapy import gmsh
from sapy import structure
from sapy import plotter



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

    def add_node(self, node):
        self.num_nodes += 1
        self.num_displacements += int(node.support_x) + int(node.support_y)
        self.nodes.append(node)
    
    def remove_node(self, node):
        self.num_nodes -= 1
        self.nodes.remove(node)

    def add_member(self, member):
        self.num_members += 1
        self.members.append(member)

    def remove_member(self, member):
        self.num_members -= 1
        self.members.remove(member)

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


    def solve(self):
        # Make sure that there are at least two vertical supports on either side
        assert(self.left_node.get_support_y() and self.right_node.get_support_y())

        
        mesh = ''
        nodes = {}
        # Parse Nodes
        count = 1
        for node in self.get_nodes():
            mesh += ('Point(' + str(count) + ') = {' + str(node.get_x()) + ', ' + str(node.get_y()) + ', 0};\n')
            nodes[(node.get_x(), node.get_y())] = count
            count += 1
        mesh += '\n'

        # Parse Members
        count = 1
        for member in self.get_members():
            node_a = member.get_nodeA()
            node_b = member.get_nodeB()
            node_a_coords = (node_a.get_x(), node_a.get_y())
            node_b_coords = (node_b.get_x(), node_b.get_y())
            mesh += 'Line(' + str(count) + ') = {' + str(nodes[node_a_coords]) + ', ' + str(nodes[node_b_coords]) + '};\n'

        # Create the mesh
        # mesh = gmsh.Parse(StringIO(mesh))

        # Parse the supports
        left_coords = (self.left_node.get_x(), self.left_node.get_y())
        right_coords = (self.right_node.get_x(), self.right_node.get_y())

        bound = {
                    nodes[left_coords]: [int(self.left_node.get_support_x()), int(self.left_node.get_support_y())],
                    nodes[right_coords]: [int(self.right_node.get_support_x()), int(self.right_node.get_support_y())]
                }

        print(bound)
    



        
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
        assert val > 0
        self.load = val

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

    def __str__(self):
        # return 'MEMBER BETWEEN THE FOLLOWING NODES:\n' + str(self.A) + str(self.B)

        return 'Length:' + str(self.get_length())

        
if __name__ == '__main__':
    bridge = Bridge()
    bridge.load_from_file('../../Statics_Project/simple.txt')
    bridge.get_load_nodes()

    for node in bridge.get_load_nodes():
        node.set_load_angle(-1.5707963267948966)


    bridge.solve()
    # print(bridge.is_solvable())
