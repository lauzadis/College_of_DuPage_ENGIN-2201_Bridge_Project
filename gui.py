import sys  # To exit the program
import numpy as np  # To do matrix calculations
import time  # To sleep to get 30 frames per second in the animation

# To add GUI elements
from PyQt5.QtGui     import *
from PyQt5.QtCore    import *
from PyQt5.QtWidgets import *


# To embed Matplotlib in the PyQT Application
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from matplotlib.lines import Line2D  # To detect clicks on nodes
import matplotlib.pyplot as plt

from bridge import Bridge, Node, Member


class MainWindow(QMainWindow):    
    def __init__(self):
        super().__init__()
        self.title = 'College of DuPage ENGIN-2201 Bridge Project'
        self.bridge = Bridge()
        self.InitUI()


    def InitUI(self):
        self.setWindowTitle(self.title)

        centralWidget = QWidget(self)
        self.setCentralWidget(centralWidget)

        grid =  QGridLayout()
        
        # Embed MatplotLib Plot
        plt.grid(True)
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)                
        self.toolbar = CustomNavigationToolbar(self.canvas, self)
        self.ax = self.canvas.figure.subplots()
        
        # Initial plot of members and nodes (if they exist)
        self.plot_bridge()
        self.selected_node = None

        grid.addWidget(self.toolbar, 3, 0)
        grid.addWidget(self.canvas, 0, 0)

        # Implement Zoom
        self.canvas.mpl_connect('scroll_event', self.zoom)
        
        # Implement Clicks
        self.canvas.mpl_connect('pick_event', self.onpick_node)

        # BRIDGE MODIFICATION        
        right_subgrid = QGridLayout()
        
        # MEMBERS
        member_vbox = QVBoxLayout()
            # Add Member
        add_member_button = QPushButton('Add Member', self)
        add_member_button.clicked.connect(self.add_member)
        member_vbox.addWidget(add_member_button)
            # Remove Member
        remove_member_button = QPushButton('Remove Member', self)
        remove_member_button.clicked.connect(self.remove_member)
        member_vbox.addWidget(remove_member_button)
        
        member_nodes_hbox = QHBoxLayout()
            # Node A
        self.node_a = QLineEdit()
        self.node_a.setPlaceholderText('Node A')
        self.node_a.returnPressed.connect(self.member_on_return_pressed)
        member_nodes_hbox.addWidget(self.node_a)
            # Node B
        self.node_b = QLineEdit()
        self.node_b.setPlaceholderText('Node B')
        self.node_b.returnPressed.connect(self.member_on_return_pressed)
        member_nodes_hbox.addWidget(self.node_b)
        member_vbox.addLayout(member_nodes_hbox)
        right_subgrid.addLayout(member_vbox, 0, 0)

        # NODES
        add_node_vbox = QVBoxLayout()
            # Add Node
        add_node_button = QPushButton('Add Node', self)        
        add_node_button.clicked.connect(self.add_node)
        add_node_vbox.addWidget(add_node_button)
            
            # Coordinate Input
        coords_hbox = QHBoxLayout()
            # X Coord
        self.x_coord = QLineEdit()
        self.x_coord.setPlaceholderText('X-Coord')
        self.x_coord.returnPressed.connect(self.on_x_coord_change)
        coords_hbox.addWidget(self.x_coord)            
            # Y Coord
        self.y_coord = QLineEdit()
        self.y_coord.setPlaceholderText('Y-Coord')
        self.y_coord.returnPressed.connect(self.on_y_coord_change)
        coords_hbox.addWidget(self.y_coord)

        add_node_vbox.addLayout(coords_hbox)
            
            # Support Input
        supports_hbox = QHBoxLayout()
        self.x_support = QCheckBox('Horizontal Support')
        self.x_support.clicked.connect(self.on_x_support_change)
        supports_hbox.addWidget(self.x_support)
        self.y_support = QCheckBox('Vertical Support')
        self.y_support.clicked.connect(self.on_y_support_change)
        supports_hbox.addWidget(self.y_support)
        add_node_vbox.addLayout(supports_hbox)

        right_subgrid.addLayout(add_node_vbox, 1, 0)
            
            # Remove Node
        remove_node_vbox = QVBoxLayout()
        remove_node_button = QPushButton('Remove Node', self)
        remove_node_button.clicked.connect(self.remove_node)
        remove_node_vbox.addWidget(remove_node_button)
        self.remove_node_id = QLineEdit()
        self.remove_node_id.setPlaceholderText('Node ID')
        remove_node_vbox.addWidget(self.remove_node_id)
            # Clear Selection
        clear_selection_button = QPushButton('Clear Selection', self)
        clear_selection_button.clicked.connect(self.clear_selection)
        remove_node_vbox.addWidget(clear_selection_button)
        right_subgrid.addLayout(remove_node_vbox, 2, 0)

        grid.addLayout(right_subgrid, 0, 1)
            
        # Save Bridge
        bridge_buttons = QVBoxLayout()

        save_load = QHBoxLayout()

        save_bridge_button = QPushButton('Save Bridge', self)
        save_load.addWidget(save_bridge_button)
        save_bridge_button.clicked.connect(self.save_bridge)

        # Load Bridge
        load_bridge_button = QPushButton('Load Bridge', self)
        save_load.addWidget(load_bridge_button)
        load_bridge_button.clicked.connect(self.load_bridge)
        bridge_buttons.addLayout(save_load)

        # Return to Main Menu Button
        return_to_main_button = QPushButton('Exit', self)
        bridge_buttons.addWidget(return_to_main_button)        
        return_to_main_button.clicked.connect(self.return_to_main)

        grid.addLayout(bridge_buttons, 1, 0)

        # Solution Menu
        
        solution_vbox = QVBoxLayout()
        solution_vbox.setSpacing(0)

        solve_bridge_button = QPushButton('Solve Bridge')
        solve_bridge_button.clicked.connect(self.solve_bridge)
        solution_vbox.addWidget(solve_bridge_button)

        self.efficiency_text = QLabel()
        self.efficiency_text.setText('Efficiency: None')
        self.efficiency_text.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.efficiency_text.setFont(QFont('Arial', 20))
        solution_vbox.addWidget(self.efficiency_text)
        
        grid.addLayout(solution_vbox, 1, 1)  

        centralWidget.setLayout(grid)
        self.show()


    def add_node(self):
        '''
        Adds a node to the bridge by reading the xcoord, ycoord, xsupport, ysupport boxes.
        If the xcoord or ycoord box is empty, it won't do anything.
        '''
        if self.bridge.is_solved:
            self.efficiency_text.setText('Efficiency: None')
            self.bridge.is_solved = False


        x_coord = self.x_coord.text()
        y_coord = self.y_coord.text()
        x_support = self.x_support.isChecked()
        y_support = self.y_support.isChecked()

        if x_coord == '' or y_coord == '':
            return

        node = Node(self.bridge.num_nodes+1, x_coord, y_coord, x_support, y_support)
        self.bridge.add_node(node)
       

        self.ax.clear()
        self.plot_bridge()
        self.canvas.draw()


    def remove_node(self):
        '''
        Removes the selected node, all members it is a part of, and its X and Y supports.
        If there is no selected node, it will check the 'Node ID' text box too.
        '''

        # Check that the remove_node exists
        if self.selected_node == None:
            node = self.bridge.get_node(self.remove_node_id.text())
            if node is not None:
                self.selected_node = node
            else:
                return 
                 
        # Check if the bridge is already solved, if it is, 'unsolve' it, since the bridge is being modified
        if self.bridge.is_solved:
            self.efficiency_text.setText('Efficiency: None')
            self.bridge.is_solved = False

        # Remove selected node's members
            # Filter to find the members that DON'T contain the node we're removing
            # Then set the bridge's members to that filtered list
        self.bridge.set_members([member for member in self.bridge.get_members() if member.get_nodeA().get_id() != self.selected_node.get_id() and member.get_nodeB().get_id() != self.selected_node.get_id()])
        self.bridge.num_members = len(self.bridge.get_members())
        
        # Remove displacements
        if self.selected_node.get_support_x():
            self.bridge.num_displacements -= 1
        if self.selected_node.get_support_y():
            self.bridge.num_displacements -= 1

        # Remove selected node
        self.bridge.remove_node(self.selected_node)

        self.selected_node = None
        self.ax.clear()
        self.plot_bridge()
        self.canvas.draw()


    def clear_selection(self):
        '''
        Clears the selected node
        '''
        self.selected_node = None
        self.ax.clear()
        self.plot_bridge()
        self.canvas.draw()


    def add_member(self):
        '''
        Adds a member to the bridge by reading the nodeA and nodeB boxes.
        If either of the boxes are empty, it won't do anything.
        '''
        # check if the input boxes are empty 

        # Get node ID's
        node_a = self.bridge.get_node(self.node_a.text())
        node_b = self.bridge.get_node(self.node_b.text())

        if node_a == None or node_b == None:
            return

        if self.bridge.is_solved:
            self.efficiency_text.setText('Efficiency: None')
            self.bridge.is_solved = False

        # check if the member already exists
        for member in self.bridge.get_members():
            if (member.get_nodeA() == node_a and member.get_nodeB() == node_b) or (member.get_nodeA() == node_b and member.get_nodeB() == node_a):
                return

        # create the member, add it to the bridge
        member_id = str(len(self.bridge.get_members()) + 1)
        member = Member(member_id, node_a, node_b)
        self.bridge.add_member(member)

        # redraw the plot
        self.ax.clear()
        self.plot_bridge()
        self.canvas.draw()


    def remove_member(self):
        '''
        Removes the member between nodeA and nodeB. If either box is empty, or the node doesn't exist, it does nothing.

        '''

        if self.bridge.is_solved:
            self.efficiency_text.setText('Efficiency: None')
            self.bridge.is_solved = False

        node_a = self.bridge.get_node(self.node_a.text())
        node_b = self.bridge.get_node(self.node_b.text())

        if node_a == None or node_b == None:
            return
        try:
            member = self.bridge.get_member(node_a, node_b)
            self.bridge.remove_member(member)
            self.ax.clear()
            self.plot_bridge()
            self.canvas.draw()
        except:  # The member does not exist
            pass  
        

    def member_on_return_pressed(self):
        '''
        Captures the 'Enter' keypress when you're typing in either the nodeA or nodeB box.
        Tries to add the member based on what is in the boxes.
        '''
        try:
            self.add_member()
        except:
            pass


    def on_x_support_change(self):
        '''
        Captures the click in the X-support checkbox, tries to update the x-support of the selected node.
        '''
        if self.bridge.is_solved:
            self.efficiency_text.setText('Efficiency: None')
            self.bridge.is_solved = False
            self.redraw_plot()

        if self.selected_node is not None:
            current_state = bool(self.selected_node.get_support_x())
            self.selected_node.set_support_x(int(not current_state))
            if current_state:
                self.bridge.num_displacements -= 1
            else:
                self.bridge.num_displacements += 1


    def on_y_support_change(self):
        '''
        Captures the click in the Y-support checkbox, tries to update the y-support of the selected node.
        '''
        if self.bridge.is_solved:  # if bridge is solved, 'unsolve' it
            self.efficiency_text.setText('Efficiency: None')
            self.bridge.is_solved = False
            self.redraw_plot()

        if self.selected_node is not None:
            current_state = bool(self.selected_node.get_support_y())
            self.selected_node.set_support_y(int(not current_state))  # inverse of the current state
            
            if current_state:  # if we're removing a support, decrease the number of displacements
                self.bridge.num_displacements -= 1
            
            else:  # if we're adding a support, increase displacements
                self.bridge.num_displacements += 1


    def on_x_coord_change(self):     
        '''
        Captures the 'Enter' keypress in the x-coord box, tries to update the x-coord of the selected node. 
        If there is no selected node, then it tries to make a new node at that coordinate.
        ''' 
        if self.bridge.is_solved:
            self.efficiency_text.setText('Efficiency: None')
            self.bridge.is_solved = False
            self.redraw_plot()

        if self.x_coord.text() == '':
            return

        if self.selected_node is not None:
            try:
                self.selected_node.set_x(float(self.x_coord.text()))
            except:
                pass
            
            self.ax.clear()
            self.plot_bridge()
            self.ax.plot(self.selected_node.get_x(), self.selected_node.get_y(), 'go', picker=5)
            self.canvas.draw()

        elif self.selected_node is None:
            node = Node(self.bridge.num_nodes+1, float(self.x_coord.text()), float(self.y_coord.text()), self.x_support.isChecked(), self.y_support.isChecked())
            self.bridge.add_node(node)
            self.ax.clear()
            self.plot_bridge()
            self.canvas.draw()


    def on_y_coord_change(self):
        '''
        Captures the 'Enter' keypress in the y-coord box, tries to update the y-coord of the selected node. 
        If there is no selected node, then it tries to make a new node at that coordinate.
        ''' 
        if self.bridge.is_solved:
            self.efficiency_text.setText('Efficiency: None')
            self.bridge.is_solved = False
            self.redraw_plot()

        if self.y_coord.text() == '' or self.x_coord.text() == '':
            return

        if self.selected_node is not None:
            try:
                self.selected_node.set_y(float(self.y_coord.text()))
            except:
                pass
            
            self.ax.clear()
            self.plot_bridge()
            self.ax.plot(self.selected_node.get_x(), self.selected_node.get_y(), 'go', picker=5)  # Plot the selected node in green
            self.canvas.draw()
            
        elif self.selected_node is None:
            node = Node(self.bridge.num_nodes+1, float(self.x_coord.text()), float(self.y_coord.text()), self.x_support.isChecked(), self.y_support.isChecked())
            self.bridge.add_node(node)
            self.ax.clear()
            self.plot_bridge()
            self.canvas.draw()


    def onpick_node(self, event):
        '''
        Captures a 'click' event on a node, marks it as the selected node.
        '''
        
        if isinstance(event.artist, Line2D):
            self.selected_node = None
            self.redraw_plot()

            thisline = event.artist
            xdata = thisline.get_xdata()
            ydata = thisline.get_ydata()
            ind = event.ind

            x_coord = str(np.take(xdata, ind)[0])
            y_coord = str(np.take(ydata, ind)[0])

            for node in self.bridge.get_nodes():
                if str(node.get_x()) == x_coord and str(node.get_y()) == y_coord:
                    self.selected_node = node
            
            # Get node data
            selected_x_coord = self.selected_node.get_x()
            selected_y_coord = self.selected_node.get_y()
            selected_x_support = self.selected_node.get_support_x()
            selected_y_support = self.selected_node.get_support_y()

            self.ax.plot(selected_x_coord, selected_y_coord, 'go', picker=5)
            self.canvas.draw()

            self.x_coord.setText(str(selected_x_coord))
            self.y_coord.setText(str(selected_y_coord))
            self.remove_node_id.setText(str(self.selected_node.get_id()))

            if selected_x_support:
                self.x_support.setChecked(True)
            else:
                self.x_support.setChecked(False)

            if selected_y_support:
                self.y_support.setChecked(True)
            else:
                self.y_support.setChecked(False)

        else:
            xlim = self.ax.get_xlim()
            ylim = self.ax.get_ylim()
            self.ax.clear()
            self.plot_bridge()
            self.canvas.draw()
            self.ax.set_xlim(xlim)
            self.ax.set_ylim(ylim)


    def redraw_plot(self, preserve_zoom=True):
        '''
        Redraws the plot, preserving zoom level.
        '''
        # Preserve zoom
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        
        self.ax.clear()
        self.plot_bridge()
        self.canvas.draw()
        
        if preserve_zoom:
            self.ax.set_xlim(xlim)
            self.ax.set_ylim(ylim)


    def plot_bridge(self):
        '''
        Draws the bridge using matplotlib.
        '''

        if self.bridge.is_solved:
            seismic = plt.cm.get_cmap('bwr', 2056)
            # seismic = plt.cm.get_cmap('rainbow', 2056)

            # Plot Members (Blue = Compression, Red = Tension)
            max_force = self.bridge.internal_forces.abs().max()

            for member in self.bridge.get_members():   
                force = self.bridge.internal_forces.loc['F'+str(member.get_id())] 
                force_remapped = (force + max_force) / (max_force*2+0.000001)

                nodeA = member.get_nodeA()
                nodeB = member.get_nodeB()

                # Draw a line between the nodes
                self.ax.plot([nodeA.get_x(),nodeB.get_x()], [nodeA.get_y(),nodeB.get_y()], color=seismic(force_remapped))

            
            # Plot Loading Nodes (with an Arrow pointing downwards)
            for node in self.bridge.load_nodes:
                self.ax.arrow(node.get_x(), node.get_y(), dx=0, dy=-5, length_includes_head=True, head_width=2, head_length=1, width=0.5)

     
            # Plot Broken Member(s) in Black
            for member_id, _ in self.bridge.broken_members.items():
                member = self.bridge.get_member_by_id(member_id[1:])
                nodeA = member.get_nodeA()
                nodeB = member.get_nodeB()
                # Draw a line between the nodes
                self.ax.plot([nodeA.get_x(),nodeB.get_x()], [nodeA.get_y(),nodeB.get_y()], 'k')


            # Plot Zero-Load Member(s) in Green
            zero_load = self.bridge.internal_forces.where(np.isclose(self.bridge.internal_forces, 0, rtol=1e-03, atol=1e-03, equal_nan=False)).dropna()
            for member_id, _ in zero_load.items():
                    member = self.bridge.get_member_by_id(member_id[1:])
                    nodeA = member.get_nodeA()
                    nodeB = member.get_nodeB()
                    # Draw a line between the nodes
                    self.ax.plot([nodeA.get_x(),nodeB.get_x()], [nodeA.get_y(),nodeB.get_y()], 'g')


        else:  # Bridge is not solved, plot normally
            for member in self.bridge.get_members(): 
                # Get incident and terminal node
                nodeA = member.get_nodeA()
                nodeB = member.get_nodeB()
                # Draw a line between the nodes
                self.ax.plot([nodeA.get_x(),nodeB.get_x()], [nodeA.get_y(),nodeB.get_y()], 'ro-')
        

        # Plot Nodes
        for node in self.bridge.get_nodes():
            # Plot node's X and Y coordinate
            self.ax.plot(node.get_x(), node.get_y(), 'bo', picker=5)
            # Add a text label with the node's ID
            self.ax.annotate(node.get_id(), (node.get_x(), node.get_y()), xytext=(node.get_x()+0,node.get_y()+2))
        

    def load_bridge(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","All Files (*);;Text Files (*.txt)", options=options)
        if fileName:
            if self.bridge is not None:
                self.bridge = Bridge()  
          
            text = self.bridge.load_from_file(fileName)
            if text is not '':
                self.error_dialog(text)
                return

            self.redraw_plot(preserve_zoom=False)
            self.efficiency_text.setText('Efficiency: None')


    def save_bridge(self):
        '''
        Writes the current bridge to a user-defined text file.
        '''
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getSaveFileName(self,"QFileDialog.getOpenFileName()", "","All Files (*);;Text Files (*.txt)", options=options)
        if fileName:        
            self.bridge.save_to_file(fileName)


    def solve_bridge(self):
        # For a planar truss to be statically determinate, the number of members plus the number of support reactions must not exceed the number of joints times 2.
        # members + support_reactions <= joints*2 to be statically determinant

        # support_reaction_count = 0
        # for node in self.bridge.get_nodes():
        #     if node.get_support_x():
        #         support_reaction_count += 1
        #     if node.get_support_y():
        #         support_reaction_count += 1

        # lhs = len(self.bridge.get_members()) + support_reaction_count  # left hand side of the equation
        # rhs = len(self.bridge.get_nodes())*2  # right hand side of the equation

        # if lhs > rhs:
        #     self.efficiency_text.setText('Efficiency: Not Solvable')
        #     return

        text = self.bridge.solve()

        if text is not '':
            self.error_dialog(text)
            return

        self.efficiency_text.setText('Efficiency: ' + str(int(self.bridge.efficiency)))
        self.redraw_plot()        
        
        return


    def return_to_main(self):
        confirm = ConfirmExitDialog()
        if confirm.exec_():
            sys.exit(0)


    def error_dialog(self, error_text):
        error = ErrorDialog(error_text)
        if error.exec_():
            pass


    def zoom(self, event):
        # Function to allow scroll zooming within a matplotlib plot
        # Credit to tacaswell
        # https://stackoverflow.com/questions/11551049/matplotlib-plot-zooming-with-scroll-wheel/12793033

        if event.button == 'down':
            # Zoom in 
            factor = 1.05

        elif event.button == 'up':
            # Zoom Out
            factor = 0.25


        curr_xlim = self.ax.get_xlim()
        curr_ylim = self.ax.get_ylim()

        new_width = (curr_xlim[1]-curr_ylim[0])*factor
        new_height= (curr_xlim[1]-curr_ylim[0])*factor

        relx = (curr_xlim[1]-event.xdata)/(curr_xlim[1]-curr_xlim[0])
        rely = (curr_ylim[1]-event.ydata)/(curr_ylim[1]-curr_ylim[0])

        self.ax.set_xlim([event.xdata-new_width*(1-relx),
                    event.xdata+new_width*(relx)])
        self.ax.set_ylim([event.ydata-new_width*(1-rely),
                            event.ydata+new_width*(rely)])
        self.canvas.draw()


class ConfirmExitDialog(QDialog):
    def __init__(self, parent=None):
        super(ConfirmExitDialog, self).__init__(parent)
        self.InitUI()
        

    def InitUI(self):
        grid = QGridLayout()

        confirm = QPushButton('Confirm Exit', self)
        confirm.clicked.connect(self.accept)
        grid.addWidget(confirm)
        
        deny = QPushButton('Take Me Back!', self)
        deny.clicked.connect(self.reject)
        grid.addWidget(deny)

        self.setLayout(grid)
        self.show()


class ErrorDialog(QDialog):
    def __init__(self, error_text, parent=None):
        super(ErrorDialog, self).__init__(parent)
        self.setWindowTitle('Error!')
        grid = QGridLayout()

        displayText = QLabel()
        displayText.setText(error_text)
        displayText.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        displayText.setFont(QFont('Arial', 15))
        grid.addWidget(displayText)

        confirm = QPushButton('Ok', self)
        confirm.clicked.connect(self.accept)
        grid.addWidget(confirm)
        
        self.setLayout(grid)
        self.show()

class CustomNavigationToolbar(NavigationToolbar):
    # Custom Toolbar to only display the buttons we want
    toolitems = [t for t in NavigationToolbar.toolitems if t[0] in ('Home', 'Pan', 'Zoom', 'Save')]


if __name__ == '__main__':
    app = QApplication(sys.argv)    
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())