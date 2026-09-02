# 🪙 Bitcoin Transaction Analysis

A full-stack application for analyzing and modeling Bitcoin transactions, featuring a React frontend, a Spring Boot backend API, and a Python Machine Learning engine.

---

## 🏗️ Project Architecture

```text
Bitcoin_transaction_analysis/
├── frontend/           # UI built with React / Node.js
├── backend/            # Core REST API built with Java & Spring Boot
├── ml_engine/          # Python ML pipeline & data processing
│   ├── environment.yml # Conda environment dependencies
│   ├── main.py         # Main ML entry point
│   ├── ingestion.py    # Data ingestion logic
│   └── generator.py    # Synthetic transaction generator script
├── data/               # Raw and processed datasets (git-ignored)
└── scripts/            # Utility and automation scripts
🚀 Getting Started
Follow these steps to set up your local development environment.

1. ML Engine Setup (Python / Conda)
We use Conda to manage isolated dependencies across team environments.

Prerequisites
Anaconda or Miniconda
# 🪙 Team Setup & Git Collaboration Workflow

---

## 🐍 1. Conda Environment & Data Setup for ML contributor's

Run these commands in your terminal to set up the Python environment and build your local dataset:

```bash
# Step 1: Navigate to ml_engine and create the Conda environment
cd ml_engine
conda env create -f environment.yml

# Step 2: Activate the environment (named 'coin' from environment.yml)
conda activate coin

# Step 3: Return to the project root and generate your local dataset
cd ..
python -m ml_engine.generator

# Step 4: Run the ML pipeline
python -m ml_engine.main

🌿 2. Git Branching & Push Workflow
Never push directly to main. Always work inside a feature branch.

Step-by-Step Instructions:
Pull the latest code from main:

Bash
git checkout main
git pull origin main
Create your feature branch:

Bash
# Naming format: feature/description or fix/description
git checkout -b feature/your-feature-name
Make changes, stage, and commit:

Bash
git add .
git commit -m "Brief description of your changes"
(Note: Never commit .csv files inside data/. Everyone generates data locally using Step 3 above).

Push your branch to GitHub:

Bash
git push origin feature/your-feature-name
Open a Pull Request (PR):
Go to GitHub, click "Compare & pull request", ask a teammate for code review, and merge into main.