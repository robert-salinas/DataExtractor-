import sys
import os

# Add src to python path to allow imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.desktop.ui import App

if __name__ == "__main__":
    app = App()
    app.mainloop()
