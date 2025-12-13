import sys
import os

# ensure it runs from the right folder
sys.path.append(os.path.join(os.path.dirname(__file__), "app"))

from app.server import app

# run your real main
# from app.main import main

#if __name__ == "__main__":
    # main()