# Foundation Potentials Comparison Dashboard

A Dash Plotly web application to compare predictions from different foundation ML potentials (CHGNet, M3GNet) for crystal structures from the Materials Project.

## Features

- 🔍 Fetch structures from Materials Project by ID
- 🤖 Compare predictions from multiple foundation models:
  - **CHGNet**: Universal neural network potential for charge-informed atomistic modeling
  - **M3GNet**: Materials graph network with three-body interactions
- 📊 Interactive visualizations:
  - Energy per atom comparison
  - Force magnitudes distribution
  - Stress tensor components (radar plot)
  - Comprehensive summary table
- 🏗️ Structure information display:
  - Chemical formula
  - Space group
  - Lattice parameters
  - Volume and density

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd <repository-directory>
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

**Note**: Installing the ML models (CHGNet, M3GNet) may take some time and requires sufficient disk space (~2-3 GB for model weights).

### 4. Set up Materials Project API Key

Get your free API key from [materialsproject.org/api](https://materialsproject.org/api)

Set it as an environment variable:

```bash
export MP_API_KEY="your_api_key_here"
```

Or on Windows:

```cmd
set MP_API_KEY=your_api_key_here
```

Alternatively, you can enter the API key directly in the app interface.

## Usage

### Running the App

```bash
python app.py
```

The app will start and be accessible at: **http://127.0.0.1:8050**

### Using the Dashboard

1. **Enter Materials Project ID**: Type a Materials Project ID (e.g., `mp-149` for silicon, `mp-1234` for other materials)
   - You can enter with or without the `mp-` prefix
   
2. **Provide API Key** (optional): If you haven't set the `MP_API_KEY` environment variable, enter it in the API Key field

3. **Click "Load & Predict"**: The app will:
   - Fetch the structure from Materials Project
   - Load the ML models (first time may take a minute)
   - Generate predictions from available models
   - Display results in interactive plots

4. **Explore Results**: Switch between tabs to view:
   - **Energy**: Bar chart comparing energy per atom
   - **Forces**: Box plots showing force magnitude distributions
   - **Stress**: Radar plot of stress tensor components
   - **Summary Table**: Comprehensive comparison of all properties

## Example Materials to Try

- `mp-149` - Silicon (diamond structure)
- `mp-66` - Silicon (simple cubic)
- `mp-1234` - Lithium cobalt oxide
- `mp-1265` - Lithium iron phosphate
- `mp-2815` - Graphite
- `mp-804` - Magnesium oxide

## Model Details

### CHGNet
- Universal neural network potential
- Trained on Materials Project structures
- Predicts: energy, forces, stress, magnetic moments
- Reference: [CHGNet Paper](https://www.nature.com/articles/s42256-023-00716-3)

### M3GNet
- Graph neural network with three-body interactions
- Universal interatomic potential
- Trained on Materials Project PES dataset
- Predicts: energy, forces, stress
- Reference: [M3GNet Paper](https://www.nature.com/articles/s43588-022-00349-3)

## Requirements

- Python 3.8+
- CUDA-capable GPU (optional, but recommended for faster predictions)
- ~2-3 GB disk space for model weights
- Internet connection for Materials Project API access

## Troubleshooting

### Models not loading
- Ensure you have sufficient disk space
- Check internet connection for downloading model weights
- First-time model loading may take 1-2 minutes

### API Key errors
- Verify your API key is valid at materialsproject.org
- Ensure the key is properly set in environment variables or entered in the app

### Memory issues
- Close other applications to free up RAM
- Start with smaller structures (fewer atoms)
- Models require ~2-4 GB RAM when loaded

## Tech Stack

- **Dash**: Web application framework
- **Plotly**: Interactive visualizations
- **PyMatGen**: Materials analysis toolkit
- **CHGNet**: ML potential for materials
- **M3GNet/MatGL**: Graph neural network potential
- **MP-API**: Materials Project API client

## Contributing

Contributions are welcome! Areas for improvement:
- Add more foundation models (MACE, NequIP, Allegro)
- Structure relaxation comparisons
- Phonon property predictions
- Export results to files
- Batch processing multiple structures

## License

This project is open source. Please cite the respective papers if you use CHGNet or M3GNet in your research.

## Acknowledgments

- Materials Project for providing the structure database
- CHGNet and M3GNet teams for their excellent ML potentials
- Plotly and Dash teams for the visualization framework
