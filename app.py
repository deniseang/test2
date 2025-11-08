"""
Dash Plotly App to Compare Foundation Potentials for Materials
This app fetches structures from Materials Project and compares predictions
from different ML potentials (CHGNet, M3GNet, MACE).
"""

import os
import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

from mp_api.client import MPRester
from pymatgen.core import Structure
from pymatgen.io.ase import AseAtomsAdaptor

try:
    from chgnet.model import CHGNet
    CHGNET_AVAILABLE = True
except ImportError:
    CHGNET_AVAILABLE = False

try:
    import matgl
    from matgl.ext.ase import M3GNetCalculator, Relaxer
    M3GNET_AVAILABLE = True
except ImportError:
    M3GNET_AVAILABLE = False

import warnings
warnings.filterwarnings('ignore')

# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Foundation Potentials Comparison"

# Global variables for models
models_cache = {}

def load_models():
    """Load foundation models"""
    global models_cache
    
    if CHGNET_AVAILABLE and 'chgnet' not in models_cache:
        try:
            models_cache['chgnet'] = CHGNet.load()
            print("CHGNet loaded successfully")
        except Exception as e:
            print(f"Error loading CHGNet: {e}")
    
    if M3GNET_AVAILABLE and 'm3gnet' not in models_cache:
        try:
            # Load M3GNet universal potential
            potential = matgl.load_model("M3GNet-MP-2021.2.8-PES")
            models_cache['m3gnet'] = potential
            print("M3GNet loaded successfully")
        except Exception as e:
            print(f"Error loading M3GNet: {e}")

def get_structure_from_mp(mp_id, api_key=None):
    """Fetch structure from Materials Project"""
    if api_key is None:
        api_key = os.environ.get('MP_API_KEY', None)
    
    if not api_key:
        raise ValueError("MP_API_KEY not found. Please set it as an environment variable or provide it in the app.")
    
    with MPRester(api_key) as mpr:
        structure = mpr.get_structure_by_material_id(mp_id)
    
    return structure

def predict_with_chgnet(structure):
    """Get predictions from CHGNet"""
    if 'chgnet' not in models_cache:
        return None
    
    try:
        model = models_cache['chgnet']
        prediction = model.predict_structure(structure)
        
        return {
            'energy': prediction['e'],  # eV/atom
            'forces': prediction['f'],  # eV/Å
            'stress': prediction['s'],  # GPa
            'magmom': prediction.get('m', None)  # μB
        }
    except Exception as e:
        print(f"CHGNet prediction error: {e}")
        return None

def predict_with_m3gnet(structure):
    """Get predictions from M3GNet"""
    if 'm3gnet' not in models_cache:
        return None
    
    try:
        potential = models_cache['m3gnet']
        adaptor = AseAtomsAdaptor()
        atoms = adaptor.get_atoms(structure)
        
        # Set up calculator
        calc = M3GNetCalculator(potential=potential)
        atoms.calc = calc
        
        # Get predictions
        energy = atoms.get_potential_energy()  # eV
        forces = atoms.get_forces()  # eV/Å
        stress = atoms.get_stress()  # eV/Å³
        
        # Convert stress to GPa (1 eV/Å³ = 160.21766208 GPa)
        stress_gpa = stress * 160.21766208
        
        return {
            'energy': energy / len(atoms),  # eV/atom
            'forces': forces,
            'stress': stress_gpa
        }
    except Exception as e:
        print(f"M3GNet prediction error: {e}")
        return None

def create_structure_info_card(structure):
    """Create a card displaying structure information"""
    if structure is None:
        return html.Div("No structure loaded")
    
    info = [
        html.H5("Structure Information", className="card-title"),
        html.Hr(),
        html.P([html.Strong("Formula: "), structure.composition.reduced_formula]),
        html.P([html.Strong("Space Group: "), f"{structure.get_space_group_info()[0]} ({structure.get_space_group_info()[1]})"]),
        html.P([html.Strong("Lattice: "), 
                f"a={structure.lattice.a:.3f} Å, b={structure.lattice.b:.3f} Å, c={structure.lattice.c:.3f} Å"]),
        html.P([html.Strong("Angles: "), 
                f"α={structure.lattice.alpha:.2f}°, β={structure.lattice.beta:.2f}°, γ={structure.lattice.gamma:.2f}°"]),
        html.P([html.Strong("Volume: "), f"{structure.lattice.volume:.3f} Ų"]),
        html.P([html.Strong("Density: "), f"{structure.density:.3f} g/cm³"]),
        html.P([html.Strong("Number of Sites: "), str(len(structure))]),
    ]
    
    return dbc.Card(dbc.CardBody(info), className="mb-3")

def create_energy_comparison_plot(predictions):
    """Create bar plot comparing energies"""
    models = []
    energies = []
    
    for model_name, pred in predictions.items():
        if pred and pred.get('energy') is not None:
            models.append(model_name.upper())
            energies.append(pred['energy'])
    
    if not models:
        return go.Figure().add_annotation(
            text="No energy predictions available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
    
    fig = go.Figure(data=[
        go.Bar(x=models, y=energies, marker_color='steelblue')
    ])
    
    fig.update_layout(
        title="Energy per Atom Comparison",
        xaxis_title="Model",
        yaxis_title="Energy (eV/atom)",
        template="plotly_white",
        height=400
    )
    
    return fig

def create_forces_comparison_plot(predictions, structure):
    """Create plot comparing force magnitudes"""
    if structure is None:
        return go.Figure()
    
    fig = go.Figure()
    
    for model_name, pred in predictions.items():
        if pred and pred.get('forces') is not None:
            forces = pred['forces']
            force_magnitudes = np.linalg.norm(forces, axis=1)
            
            fig.add_trace(go.Box(
                y=force_magnitudes,
                name=model_name.upper(),
                boxmean='sd'
            ))
    
    fig.update_layout(
        title="Force Magnitudes Distribution",
        yaxis_title="Force Magnitude (eV/Å)",
        template="plotly_white",
        height=400
    )
    
    return fig

def create_stress_comparison_plot(predictions):
    """Create radar plot comparing stress components"""
    stress_labels = ['XX', 'YY', 'ZZ', 'XY', 'YZ', 'XZ']
    
    fig = go.Figure()
    
    for model_name, pred in predictions.items():
        if pred and pred.get('stress') is not None:
            stress = pred['stress']
            # For 3x3 stress tensor, extract components
            if len(stress.shape) == 2:
                stress_values = [stress[0,0], stress[1,1], stress[2,2], 
                               stress[0,1], stress[1,2], stress[0,2]]
            else:  # Voigt notation
                stress_values = stress[:6] if len(stress) >= 6 else list(stress) + [0]*(6-len(stress))
            
            fig.add_trace(go.Scatterpolar(
                r=stress_values,
                theta=stress_labels,
                fill='toself',
                name=model_name.upper()
            ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True)
        ),
        title="Stress Tensor Components (GPa)",
        template="plotly_white",
        height=500
    )
    
    return fig

def create_comparison_table(predictions):
    """Create a table comparing all predictions"""
    if not predictions:
        return html.Div("No predictions available")
    
    rows = []
    
    # Energy row
    energy_row = [html.Td(html.Strong("Energy (eV/atom)"))]
    for model in ['chgnet', 'm3gnet']:
        if model in predictions and predictions[model]:
            energy = predictions[model].get('energy')
            energy_row.append(html.Td(f"{energy:.6f}" if energy is not None else "N/A"))
        else:
            energy_row.append(html.Td("N/A"))
    rows.append(html.Tr(energy_row))
    
    # Average force magnitude row
    force_row = [html.Td(html.Strong("Avg Force Mag (eV/Å)"))]
    for model in ['chgnet', 'm3gnet']:
        if model in predictions and predictions[model]:
            forces = predictions[model].get('forces')
            if forces is not None:
                avg_force = np.mean(np.linalg.norm(forces, axis=1))
                force_row.append(html.Td(f"{avg_force:.6f}"))
            else:
                force_row.append(html.Td("N/A"))
        else:
            force_row.append(html.Td("N/A"))
    rows.append(html.Tr(force_row))
    
    # Max force magnitude row
    max_force_row = [html.Td(html.Strong("Max Force Mag (eV/Å)"))]
    for model in ['chgnet', 'm3gnet']:
        if model in predictions and predictions[model]:
            forces = predictions[model].get('forces')
            if forces is not None:
                max_force = np.max(np.linalg.norm(forces, axis=1))
                max_force_row.append(html.Td(f"{max_force:.6f}"))
            else:
                max_force_row.append(html.Td("N/A"))
        else:
            max_force_row.append(html.Td("N/A"))
    rows.append(html.Tr(max_force_row))
    
    # Hydrostatic pressure row
    pressure_row = [html.Td(html.Strong("Pressure (GPa)"))]
    for model in ['chgnet', 'm3gnet']:
        if model in predictions and predictions[model]:
            stress = predictions[model].get('stress')
            if stress is not None:
                if len(stress.shape) == 2:
                    pressure = -np.trace(stress) / 3
                else:
                    pressure = -np.mean(stress[:3])
                pressure_row.append(html.Td(f"{pressure:.6f}"))
            else:
                pressure_row.append(html.Td("N/A"))
        else:
            pressure_row.append(html.Td("N/A"))
    rows.append(html.Tr(pressure_row))
    
    table = dbc.Table([
        html.Thead(html.Tr([
            html.Th("Property"),
            html.Th("CHGNet"),
            html.Th("M3GNet")
        ])),
        html.Tbody(rows)
    ], bordered=True, hover=True, responsive=True, striped=True)
    
    return table

# App Layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("🔬 Foundation Potentials Comparison", className="text-center mt-4 mb-4"),
            html.P("Compare predictions from different ML potentials (CHGNet, M3GNet) for materials from Materials Project",
                   className="text-center text-muted mb-4")
        ])
    ]),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Input", className="card-title"),
                    dbc.Label("Materials Project ID:"),
                    dbc.Input(
                        id="mp-id-input",
                        placeholder="e.g., mp-149, mp-1234",
                        type="text",
                        value="mp-149"
                    ),
                    html.Small("Enter a Materials Project ID (with or without 'mp-' prefix)", 
                              className="text-muted d-block mb-3"),
                    
                    dbc.Label("API Key (optional):"),
                    dbc.Input(
                        id="api-key-input",
                        placeholder="Leave empty to use MP_API_KEY env var",
                        type="password"
                    ),
                    html.Small("Get your API key from materialsproject.org", 
                              className="text-muted d-block mb-3"),
                    
                    dbc.Button("Load & Predict", id="predict-button", color="primary", className="w-100 mt-2"),
                    
                    html.Div(id="status-message", className="mt-3")
                ])
            ], className="mb-3"),
            
            html.Div(id="structure-info")
        ], md=4),
        
        dbc.Col([
            dbc.Tabs([
                dbc.Tab(label="Energy", tab_id="energy"),
                dbc.Tab(label="Forces", tab_id="forces"),
                dbc.Tab(label="Stress", tab_id="stress"),
                dbc.Tab(label="Summary Table", tab_id="table"),
            ], id="tabs", active_tab="energy"),
            
            html.Div(id="tab-content", className="mt-3")
        ], md=8)
    ]),
    
    # Store components for data
    dcc.Store(id='structure-store'),
    dcc.Store(id='predictions-store')
    
], fluid=True, className="p-4")

# Callbacks
@app.callback(
    [Output('structure-store', 'data'),
     Output('predictions-store', 'data'),
     Output('status-message', 'children'),
     Output('structure-info', 'children')],
    Input('predict-button', 'n_clicks'),
    [State('mp-id-input', 'value'),
     State('api-key-input', 'value')],
    prevent_initial_call=True
)
def load_and_predict(n_clicks, mp_id, api_key):
    """Load structure and make predictions"""
    if not mp_id:
        return None, None, dbc.Alert("Please enter a Materials Project ID", color="warning"), None
    
    # Clean MP ID
    mp_id = mp_id.strip()
    if not mp_id.startswith('mp-'):
        mp_id = f'mp-{mp_id}'
    
    try:
        # Show loading status
        status = dbc.Alert("Loading models...", color="info")
        
        # Load models
        load_models()
        
        # Fetch structure
        structure = get_structure_from_mp(mp_id, api_key if api_key else None)
        structure_dict = structure.as_dict()
        
        # Make predictions
        predictions = {}
        
        if CHGNET_AVAILABLE:
            status = dbc.Alert("Running CHGNet predictions...", color="info")
            predictions['chgnet'] = predict_with_chgnet(structure)
        
        if M3GNET_AVAILABLE:
            status = dbc.Alert("Running M3GNet predictions...", color="info")
            predictions['m3gnet'] = predict_with_m3gnet(structure)
        
        if not predictions:
            return structure_dict, None, dbc.Alert("No models available. Please install CHGNet or M3GNet.", color="danger"), create_structure_info_card(structure)
        
        # Create structure info
        structure_info = create_structure_info_card(structure)
        
        status = dbc.Alert(f"✓ Successfully loaded {mp_id} and completed predictions!", color="success")
        
        return structure_dict, predictions, status, structure_info
        
    except Exception as e:
        error_msg = dbc.Alert(f"Error: {str(e)}", color="danger")
        return None, None, error_msg, None

@app.callback(
    Output('tab-content', 'children'),
    [Input('tabs', 'active_tab'),
     Input('predictions-store', 'data'),
     Input('structure-store', 'data')]
)
def render_tab_content(active_tab, predictions, structure_dict):
    """Render content based on selected tab"""
    if not predictions:
        return html.Div("No predictions available. Please load a structure first.", 
                       className="text-center text-muted p-5")
    
    structure = Structure.from_dict(structure_dict) if structure_dict else None
    
    if active_tab == "energy":
        return dcc.Graph(figure=create_energy_comparison_plot(predictions))
    
    elif active_tab == "forces":
        return dcc.Graph(figure=create_forces_comparison_plot(predictions, structure))
    
    elif active_tab == "stress":
        return dcc.Graph(figure=create_stress_comparison_plot(predictions))
    
    elif active_tab == "table":
        return create_comparison_table(predictions)
    
    return html.Div("Select a tab to view results")

if __name__ == '__main__':
    print("Starting Foundation Potentials Comparison App...")
    print(f"CHGNet available: {CHGNET_AVAILABLE}")
    print(f"M3GNet available: {M3GNET_AVAILABLE}")
    print("\nNote: Make sure to set your MP_API_KEY environment variable or enter it in the app.")
    print("Get your API key from: https://materialsproject.org/api")
    print("\nAccess the app at: http://127.0.0.1:8050")
    app.run_server(debug=True, host='0.0.0.0', port=8050)
