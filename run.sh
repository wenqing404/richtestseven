#!/bin/bash

# Set the port
export PORT=12000

# Note: DeepSeek API key should be set in .env file
# Copy .env.example to .env and set your DEEPSEEK_API_KEY
export DEEPSEEK_API_KEY=your api_key
# Run the application
python main.py
