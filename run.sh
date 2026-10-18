#!/bin/bash
set -e
echo "Compiling C++ backend..."
g++ src/main.cpp -o src/main -std=c++17 \
  -I"$(brew --prefix cpp-httplib)/include" \
  -I"$(brew --prefix nlohmann-json)/include" \
  -I"$(brew --prefix libpq)/include" \
  -L"$(brew --prefix libpq)/lib" -lpq
echo "Starting server on port 8000..."
./src/main
