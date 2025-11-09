
import PySimpleGUI as sg

import PySimpleGUI as sg

def main():
    layout = [
        [sg.Text("Kaiser Communicator — Test GUI")],
        [sg.Button("OK")]
    ]
    window = sg.Window("Kaiser Communicator", layout)
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, "OK"):
            break
    window.close()

if __name__ == "__main__":
    main()

