import threading
import time
from mainboard.mainboard import MainBoard

def wait_for_enter(stop_event):
    input()
    stop_event.set()

def main():
    print("App running. Appuyez sur Entrée pour quitter.")
    mainboard = MainBoard()
    stop_event = threading.Event()
    thread = threading.Thread(target=wait_for_enter, args=(stop_event,))
    thread.start()
    try:
        while not stop_event.is_set():
            mainboard.update_board()
            time.sleep(0.001)  # 1ms
    except KeyboardInterrupt:
        pass
    print("App arrêtée.")
    

if __name__ == "__main__":
    main()