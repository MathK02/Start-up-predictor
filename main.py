import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from mainwindow import MainWindow
from splash_screen import SplashScreen

def load_data(splash, window):
    steps = [
        (10, "Loading data files..."),
        (30, "Initializing map..."),
        (50, "Processing data..."),
        (70, "Setting up interface..."),
        (90, "Finalizing..."),
        (100, "Ready!")
    ]
    
    for i, (progress, message) in enumerate(steps):
        def update(p=progress, m=message):
            splash.update_progress(p, m)
            if p == 100:
                window.show()
                splash.finish(window)
        
        # Add delay between updates
        QTimer.singleShot(i * 500, update)

def main():
    app = QApplication(sys.argv)
    
    # Create and show splash screen
    splash = SplashScreen()
    splash.show()
    
    # Create main window (but don't show it yet)
    window = MainWindow()
    
    # Start loading sequence
    QTimer.singleShot(100, lambda: load_data(splash, window))
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()