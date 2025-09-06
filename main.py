from mainboard.mainboard import MainBoard

def main():
    print("Hello, LightLightShowXL!")
    mainboard = MainBoard()
    print("MainBoard créé :", mainboard)
    print("Fixtures chargées :", mainboard.fixtures)

if __name__ == "__main__":
    main()