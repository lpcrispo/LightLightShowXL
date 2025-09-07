import threading
import time
from artnet_sender.artnet_sender import ArtNetSender
from mainboard.mainboard import MainBoard
from views.main_view import MainView

def wait_for_enter(stop_event):
    input()
    stop_event.set()

def app_logic():
    print("App running. Appuyez sur Entrée pour quitter.")
    mainboard = MainBoard()
    artnet = ArtNetSender()
    
    while True:
        mainboard.update_board()
        artnet.send_fixtures(mainboard.board)
        time.sleep(0.001)  # 1ms

if __name__ == "__main__":
    app = MainView(app_logic)
    app.mainloop()