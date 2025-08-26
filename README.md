# CadBot

A tool that allows users to generate precise 3D models from natural language descriptions using AI.

## Overview

CadBot leverages AI techniques to interpret natural language descriptions and convert them into accurate 3D CAD models. This tool bridges the gap between conceptual design ideas and technical CAD implementation.

## Tech Stack

- **Programming Language:** Python
- **CAD Kernel:** CadQuery
- **AI Frameworks:**
  - Hugging Face Transformers
  - PEFT (for LoRA fine-tuning)
- **Training Platform:** Google Colab
- **Local Augmentation & Deployment:** Ollama

## Project Structure

```
cadbot/
├── data/                    # Training datasets
│   └── dataset.jsonl       # CadQuery training data
├── notebooks/              # Jupyter notebooks for development
│   └── fine_tuning.ipynb   # Model fine-tuning notebook
├── src/                    # Source code
│   ├── main.py            # Main application entry point
│   ├── validate_dataset.py # Comprehensive dataset validator
│   ├── fix_dataset.py     # Dataset repair utilities
│   └── test_validation.py # Validation system tests
├── requirements.txt        # Python dependencies
├── Modelfile              # Ollama model configuration
├── AUGMENTATION_GUIDE.md    # Dataset augmentation documentation
├── VALIDATION_GUIDE.md    # Dataset validation documentation
└── README.md             # Project documentation
```

## Dataset

The project includes a comprehensive training dataset (`data/dataset.jsonl`) with 59 high-quality examples covering:

- **Basic Shapes**: Boxes, cylinders, spheres, and cones
- **Boolean Operations**: Union, difference, and intersection
- **Advanced Features**: Fillets, chamfers, and holes
- **Complex Operations**:
  - Revolutions (torus, rings)
  - Sweeps (bent pipes, complex paths)
  - Shelling (hollow structures)
  - 3D Text generation
- **Workplane Operations**: Multi-plane modeling and transformations
- **Pattern Operations**: Linear and polar arrays

Each entry follows a structured format with natural language instructions, detailed inputs, and validated CadQuery code outputs.

## Dataset Validation System

CadBot includes a comprehensive validation system to ensure dataset quality and code correctness:

### Features

- **Static Analysis**: JSON format validation, syntax checking, and code structure analysis
- **Dynamic Execution**: Actual CadQuery code execution with geometry validation
- **Quality Metrics**: Code complexity analysis, best practices verification
- **Error Detection**: Runtime errors, geometric failures, and STL export validation
- **Automated Repair**: Tools to fix common dataset issues

### Usage

```bash
# Validate the entire dataset
python src/validate_dataset.py

# Run validation tests
python src/test_validation.py

# Fix common dataset issues
python src/fix_dataset.py
```

For detailed validation documentation, see [VALIDATION_GUIDE.md](VALIDATION_GUIDE.md).

## Dataset Augmentation Approach

The final training dataset will be created by the augment_dataset script. This script configures a local LLM to create variations of each entry in `seed_dataset.jsonl`, aiming to train the final model to understand a wide range of user prompting styles. 

For guidance on dataset augmentation with a local LLM, see [AUGMENTATION_GUIDE.md](AUGMENTATION_GUIDE.md).

## Getting Started

### Prerequisites

- Python 3.8+
- CadQuery 2.4+ (for full validation)
- Ollama (for local deployment)

### Installation

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd cadbot
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. For full validation capabilities, install CadQuery:

   ```bash
   pip install cadquery>=2.4.0
   ```

5. Validate the dataset:

   ```bash
   python src/validate_dataset.py
   ```

6. Run the application:
   ```bash
   python src/main.py
   ```

## Usage

Describe your 3D model in natural language, and CadBot will generate the corresponding CAD model using CadQuery.

## Development

### Dataset Development Workflow

1. **Add New Examples**: Create new entries in `data/dataset.jsonl` following the established format
2. **Validate Changes**: Run `python src/validate_dataset.py` to ensure quality
3. **Fix Issues**: Use `python src/fix_dataset.py` for automated repairs
4. **Test Validation**: Run `python src/test_validation.py` to verify the validation system

### Model Training

The project includes Jupyter notebooks for model training and fine-tuning:

- `notebooks/fine_tuning.ipynb`: LoRA fine-tuning workflow
- Use Google Colab for training with GPU acceleration
- The dataset is automatically validated before training

### Contributing

When adding new CadQuery examples:

1. Follow the JSON structure: `{"instruction": "...", "input": "...", "output": "..."}`
2. Ensure CadQuery code is syntactically correct and executable
3. Include proper imports and result variable assignment
4. Test complex operations (revolutions, sweeps, boolean operations)
5. Run validation tools before submitting

## License

MIT License
