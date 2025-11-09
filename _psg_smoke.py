import PySimpleGUI as sg
sg.theme('Dark Blue 3')
sg.Window('PSG OK', [[sg.Text('PySimpleGUI works!')],[sg.Button('OK')]]).read(close=True)
