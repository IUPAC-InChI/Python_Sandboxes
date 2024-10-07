from tucan.io import graph_from_molfile_text, graph_to_molfile
import os
import networkx as nx
from plotly import graph_objects as go

from yapyinchi import *
from metallic_elements import metallic_elements
from disconnection_table import disconnection_table
from numpy import exp
from js import document


def check_disconnection_table(mol, atom_to_disconnect, neighbor_atoms):
    number_of_disconnected_bonds = 0
    atom_list = list(mol.nodes(data="element_symbol"))
    if atom_list[atom_to_disconnect][1] in disconnection_table:
        for n in neighbor_atoms:
            if atom_list[n][1] in disconnection_table[atom_list[atom_to_disconnect][1]]:
                print("DISCONNECT")
                number_of_disconnected_bonds += 1
                attrs = {(atom_to_disconnect, n): {"disconnect": True}}
                nx.set_edge_attributes(mol, attrs)
    disconnection_text = None
    if number_of_disconnected_bonds <= 1:
        disconnection_text = f"{number_of_disconnected_bonds} bond to atom {atom_to_disconnect} was disconnected"
    else:
        disconnection_text = f"{number_of_disconnected_bonds} bonds to atom {atom_to_disconnect} were disconnected"
    if disconnection_text == None:
        disconnection_text = "Nothing"
    document.getElementById("statusText").innerHTML = disconnection_text
    return mol


def disconnect_bonds(mol):
    value = nx.get_edge_attributes(mol, "disconnect")
    for v in value:
        mol.remove_edge(v[0], v[1])
    return mol


def get_inchi_string(mol, inchi_api):
    molfile = graph_to_molfile(mol)
    inchi_options = "-RecMet"
    show_auxinfo = ""
    calc_key = ""
    calc_xkey = ""
    # inchi_api = load_inchi_library(os.path.dirname(os.path.abspath(__file__)))

    inchi_output = inchify_molfile(
        molfile, inchi_options, show_auxinfo, calc_key, calc_xkey, inchi_api
    )
    inchi = inchi_output[2]
    inchi_warning = inchi_output[3]
    inchi_key_output = calc_inchikey(sinchi=inchi, calc_xkey=0, inchi_api=inchi_api)
    inchi_key = inchi_key_output[1]
    inchi_return = f"{inchi}\n\r{inchi_key}\n\r{inchi_warning}"
    return inchi_return


def draw_mol(mol, title):
    coords = nx.kamada_kawai_layout(mol, dim=3)
    color_scale_indices = list(nx.get_node_attributes(mol, "atomic_number").values())
    labels = list(nx.get_node_attributes(mol, "element_symbol").values())
    # Decrease node size exponentially with increasing number of atoms.
    max_node_size = 50
    min_node_size = 10
    rate_constant = 8  # Determined experimentally.
    node_size = max_node_size * exp(-mol.order() / rate_constant) + min_node_size

    # Plotly requires separate node coordinates...
    x_nodes = [coords[key][0] for key in coords.keys()]
    y_nodes = [coords[key][1] for key in coords.keys()]
    z_nodes = [coords[key][2] for key in coords.keys()]
    # ...as well as tuples of node coordinated that define edges.
    x_edges = []
    y_edges = []
    z_edges = []
    for edge in mol.edges():
        x_edges.extend([coords[edge[0]][0], coords[edge[1]][0], None])
        y_edges.extend([coords[edge[0]][1], coords[edge[1]][1], None])
        z_edges.extend([coords[edge[0]][2], coords[edge[1]][2], None])

    trace_edges = go.Scatter3d(
        x=x_edges,
        y=y_edges,
        z=z_edges,
        mode="lines",
        line=dict(color="black", width=2),
        hoverinfo="none",
    )

    trace_nodes = go.Scatter3d(
        x=x_nodes,
        y=y_nodes,
        z=z_nodes,
        mode="markers+text",
        marker=dict(
            symbol="circle",
            size=node_size,
            color=color_scale_indices,
            colorscale="turbo",
            cmin=1,
            cmax=118,
            opacity=0.5,
        ),
        text=labels,
        hoverinfo="none",
        textfont=dict(size=node_size),
    )

    fig = go.Figure()
    fig.add_traces([trace_edges, trace_nodes])
    fig.update_scenes(
        patch=dict(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False),
        ),
    )
    fig.update_layout(
        showlegend=False,
        title=title,
        height=700,
        width=700,
        scene_camera=dict(eye=dict(x=2.0, y=2.0, z=0.75)),
    )

    return fig.to_html(include_plotlyjs=False, full_html=False)


def compare_inchis(inchi1, inchi2):
    if inchi1 == inchi2:
        document.getElementById("inchiCompare").innerHTML = "InChIs are identical"
    else:
        document.getElementById("inchiCompare").innerHTML = "InChIs are different"


#  from https://codepen.io/jmsmdy/pen/MWpdjVZ
def render_plot(container, plot_html):
    range = document.createRange()
    range.selectNode(container)
    document_fragment = range.createContextualFragment(plot_html)
    while container.hasChildNodes():
        container.removeChild(container.firstChild)
    container.appendChild(document_fragment)
    container.style = "width: 100%; height: 350px; overflow-y: scroll;"


def main():
    inchi_api = load_inchi_library(os.path.dirname(os.path.abspath(__file__)))


def process(molfile):
    molecule = graph_from_molfile_text(molfile)
    atoms = list(molecule.nodes(data="element_symbol"))
    for atom in molecule:
        neighbors = list(molecule.neighbors(atom))
        number_of_bonds = len(neighbors)
        element = atoms[atom][1]
        if (element in metallic_elements) & (number_of_bonds != 0):
            if number_of_bonds == 1:
                molecule = check_disconnection_table(molecule, atom, neighbors)
            else:
                if number_of_bonds < metallic_elements[element]:
                    molecule = check_disconnection_table(molecule, atom, neighbors)
    disconnected_molecule = disconnect_bonds(molecule.copy())
    img_origin = draw_mol(molecule, "Original molecule")
    render_plot(document.getElementById("original_image"), img_origin)
    img_disconnected = draw_mol(disconnected_molecule, "Disconnected molecule")
    render_plot(document.getElementById("disconnected_image"), img_disconnected)

    # inchi_api = load_inchi_library(os.getcwd())
    inchi_api = load_inchi_library(os.path.dirname(os.path.abspath(__file__)))
    inchi = get_inchi_string(molecule, inchi_api)
    document.getElementById("original_inchi").innerHTML = inchi
    inchi_disconnected = get_inchi_string(disconnected_molecule, inchi_api)
    document.getElementById("disconnected_inchi").innerHTML = inchi_disconnected
    compare_inchis(inchi, inchi_disconnected)
