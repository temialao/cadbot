# CadBot

A tool that allows users to generate precise 3D models from natural language descriptions using AI.

## Overview

CadBot leverages advanced AI techniques to interpret natural language descriptions and convert them into accurate 3D CAD models. This tool bridges the gap between conceptual design ideas and technical CAD implementation.

## Tech Stack

- **Programming Language:** Python
- **CAD Kernel:** CadQuery
- **AI Frameworks:**
  - Hugging Face Transformers
  - PEFT (for LoRA fine-tuning)
- **Training Platform:** Google Colab
- **Local Deployment:** Ollama

## Project Structure

```
cadbot/
├── data/                 # Training datasets
├── notebooks/           # Jupyter notebooks for development
├── src/                # Source code
├── requirements.txt    # Python dependencies
├── Modelfile          # Ollama model configuration
└── README.md          # Project documentation
```

## Getting Started

### Prerequisites

- Python 3.8+
- Ollama (for local deployment)

### Installation

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd cadbot
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python src/main.py
   ```

## Usage

Describe your 3D model in natural language, and CadBot will generate the corresponding CAD model using CadQuery.

## Development

The project includes Jupyter notebooks for model training and fine-tuning. Use Google Colab for training with GPU acceleration.

## License

MIT License
