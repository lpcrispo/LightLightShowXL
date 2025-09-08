import time
from artnet_sender.artnet_sender import ArtNetSender
from mainboard.mainboard import MainBoard
from views.main_view import MainView
from kickdetector.kickdetector import KickDetector
from audio.output import AudioPassthrough
from audio.bpmdetector import BPMDetector  # Nouveau import

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
            trigger_factor=0.9,      # Réduit de 1.2 à 1 (plus sensible)
            onset_threshold=0.15,    # Plus sensible
            smoothing_alpha=0.4,     # Plus réactif
            use_onset_detection=True, # Active la détection d'onset
            debug=False   
        )
        kd.start()
        
        # Nouveau : Démarre le détecteur de BPM
        bpm_detector = BPMDetector(
            mainboard=mainboard,
            input_device_index=input_device_index,
            bpm_range=(60, 180),
            update_interval=1.0,
            smoothing_factor=0.8,
            onset_threshold=0.1,
            history_length=15,
            debug=True  # ACTIVÉ pour voir ce qui se passe
        )
        bpm_detector.start()
        print("BPM detector started...")
    else:
        print("Aucun périphérique input sélectionné. Pas de détection kick.")

    while True:
        mainboard.update_board()
        artnet.send_fixtures(mainboard.board)
        time.sleep(0.002)  # 2 ms (réduction légère charge CPU)

if __name__ == "__main__":
    app = MainView(app_logic)
    app.mainloop()