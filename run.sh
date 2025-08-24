#!/bin/bash

# Set the port
export PORT=12000

# Note: DeepSeek API key should be set in .env file
# Copy .env.example to .env and set your DEEPSEEK_API_KEY
export DEEPSEEK_API_KEY=sk-87e816f6cf16411cb2b7b90589a79ee6

# Run the application
python main.py
