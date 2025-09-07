import time
from artnet_sender.artnet_sender import ArtNetSender
from mainboard.mainboard import MainBoard
from views.main_view import MainView
from kickdetector.kickdetector import KickDetector
from audio.output import AudioPassthrough

def app_logic(input_device_index, output_device_index):
    print("App running...")
    mainboard = MainBoard("black and white kick")
    artnet = ArtNetSender("192.168.18.28", 0, 6454)
    
    # Audio monitoring (input -> output)
    if input_device_index is not None and output_device_index is not None:
        monitor = AudioPassthrough(
            input_device_index=input_device_index,
            output_device_index=output_device_index,
            samplerate=44100,
            blocksize=512,
            channels=1,
            gain=1.0
        )
        monitor.start()
        print("Monitoring audio input -> output...")
    else:
        print("Pas de monitor (input ou output manquant).")
    
# Démarre kick detector (si device sélectionné)
    if input_device_index is not None:
        kd = KickDetector(
            mainboard=mainboard,
            input_device_index=input_device_index,
            trigger_factor=3.0,      # Ajuste si trop / pas assez sensible
            refractory_time=0.11
        )
        kd.start()
    else:
        print("Aucun périphérique input sélectionné. Pas de détection kick.")

    while True:
        mainboard.update_board()
        artnet.send_fixtures(mainboard.board)
        time.sleep(0.002)  # 2 ms (réduction légère charge CPU)

if __name__ == "__main__":
    app = MainView(app_logic)
    app.mainloop()