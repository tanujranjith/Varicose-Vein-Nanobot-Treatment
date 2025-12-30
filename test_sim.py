#!/usr/bin/env python
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

if __name__ == "__main__":
    print("Starting test...", flush=True)
    try:
        print("Importing run_simulation...", flush=True)
        import run_simulation
        print("Calling main()...", flush=True)
        run_simulation.main(gui=False, record_video=True)
        print("Simulation completed!", flush=True)
    except Exception as e:
        import traceback
        print("Error during simulation:", flush=True)
        traceback.print_exc()
