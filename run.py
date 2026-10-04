import os
import webbrowser
from threading import Timer
from server import main, PORT

if __name__ == "__main__":
    if os.environ.get("OPEN_BROWSER", "1") == "1":
        Timer(1.0, lambda: webbrowser.open(f"http://127.0.0.1:{PORT}/")).start()
    main()
