"""
Example script showing how to use the foundation potentials comparison functions
without running the full Dash app.
"""

import os
from pymatgen.core import Structure

# Set your API key
os.environ['MP_API_KEY'] = 'your_api_key_here'  # Replace with your actual key

# Import functions from app
from app import (
    get_structure_from_mp,
    load_models,
    predict_with_chgnet,
    predict_with_m3gnet
)

def compare_potentials(mp_id):
    """
    Compare foundation potentials for a given Materials Project ID
    
    Args:
        mp_id (str): Materials Project ID (e.g., 'mp-149')
    
    Returns:
        dict: Dictionary containing predictions from different models
    """
    print(f"\n{'='*60}")
    print(f"Comparing Foundation Potentials for {mp_id}")
    print(f"{'='*60}\n")
    
    # Load models (only done once)
    print("Loading models...")
    load_models()
    print("✓ Models loaded\n")
    
    # Fetch structure from Materials Project
    print(f"Fetching structure for {mp_id}...")
    structure = get_structure_from_mp(mp_id)
    print(f"✓ Structure loaded: {structure.composition.reduced_formula}")
    print(f"  Space group: {structure.get_space_group_info()}")
    print(f"  Number of atoms: {len(structure)}\n")
    
    # Make predictions with different models
    predictions = {}
    
    # CHGNet
    print("Running CHGNet predictions...")
    chgnet_pred = predict_with_chgnet(structure)
    if chgnet_pred:
        predictions['CHGNet'] = chgnet_pred
        print(f"✓ CHGNet energy: {chgnet_pred['energy']:.6f} eV/atom")
    
    # M3GNet
    print("Running M3GNet predictions...")
    m3gnet_pred = predict_with_m3gnet(structure)
    if m3gnet_pred:
        predictions['M3GNet'] = m3gnet_pred
        print(f"✓ M3GNet energy: {m3gnet_pred['energy']:.6f} eV/atom")
    
    print(f"\n{'='*60}")
    print("Comparison Summary")
    print(f"{'='*60}\n")
    
    # Print comparison table
    print(f"{'Property':<30} {'CHGNet':<20} {'M3GNet':<20}")
    print("-" * 70)
    
    # Energy
    chg_energy = predictions.get('CHGNet', {}).get('energy', 'N/A')
    m3g_energy = predictions.get('M3GNet', {}).get('energy', 'N/A')
    if isinstance(chg_energy, float):
        chg_energy = f"{chg_energy:.6f}"
    if isinstance(m3g_energy, float):
        m3g_energy = f"{m3g_energy:.6f}"
    print(f"{'Energy (eV/atom)':<30} {chg_energy:<20} {m3g_energy:<20}")
    
    # Forces
    import numpy as np
    chg_forces = predictions.get('CHGNet', {}).get('forces')
    m3g_forces = predictions.get('M3GNet', {}).get('forces')
    
    if chg_forces is not None:
        chg_avg_force = f"{np.mean(np.linalg.norm(chg_forces, axis=1)):.6f}"
        chg_max_force = f"{np.max(np.linalg.norm(chg_forces, axis=1)):.6f}"
    else:
        chg_avg_force = "N/A"
        chg_max_force = "N/A"
    
    if m3g_forces is not None:
        m3g_avg_force = f"{np.mean(np.linalg.norm(m3g_forces, axis=1)):.6f}"
        m3g_max_force = f"{np.max(np.linalg.norm(m3g_forces, axis=1)):.6f}"
    else:
        m3g_avg_force = "N/A"
        m3g_max_force = "N/A"
    
    print(f"{'Avg Force Magnitude (eV/Å)':<30} {chg_avg_force:<20} {m3g_avg_force:<20}")
    print(f"{'Max Force Magnitude (eV/Å)':<30} {chg_max_force:<20} {m3g_max_force:<20}")
    
    # Stress/Pressure
    chg_stress = predictions.get('CHGNet', {}).get('stress')
    m3g_stress = predictions.get('M3GNet', {}).get('stress')
    
    if chg_stress is not None:
        if len(chg_stress.shape) == 2:
            chg_pressure = f"{-np.trace(chg_stress) / 3:.6f}"
        else:
            chg_pressure = f"{-np.mean(chg_stress[:3]):.6f}"
    else:
        chg_pressure = "N/A"
    
    if m3g_stress is not None:
        if len(m3g_stress.shape) == 2:
            m3g_pressure = f"{-np.trace(m3g_stress) / 3:.6f}"
        else:
            m3g_pressure = f"{-np.mean(m3g_stress[:3]):.6f}"
    else:
        m3g_pressure = "N/A"
    
    print(f"{'Pressure (GPa)':<30} {chg_pressure:<20} {m3g_pressure:<20}")
    
    print("\n")
    
    return predictions

if __name__ == '__main__':
    # Example materials to compare
    materials = [
        'mp-149',   # Silicon
        'mp-66',    # Silicon (different structure)
        'mp-1234',  # LiCoO2
    ]
    
    # You can run one or multiple
    for mp_id in materials[:1]:  # Change to materials[:3] to run all
        try:
            predictions = compare_potentials(mp_id)
        except Exception as e:
            print(f"Error processing {mp_id}: {e}")
