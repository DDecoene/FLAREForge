# Prism Programming Language

Prism is a multi-paradigm programming language designed to bridge systems and application programming through innovative memory management, flexible typing, and first-class support for heterogeneous computing.

## Project Status

This repository contains the bootstrap compiler for Prism, written in Python. The bootstrap compiler will be used to develop the self-hosted compiler in Prism itself.

### Current Features
- [ ] Lexical analysis
- [ ] Parsing
- [ ] Type checking
- [ ] Basic code generation

## Getting Started

### Prerequisites
- Python 3.10 or higher
- pip (Python package installer)

### Installation

```bash
# Clone the repository
git clone https://github.com/prism-lang/prism.git
cd prism

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e .[dev]
```

### Running Tests

```bash
pytest
```

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
