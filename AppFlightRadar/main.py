import tkinter as tk
import customtkinter
from tkintermapview import TkinterMapView
from PIL import Image, ImageTk

import pymysql



customtkinter.set_default_color_theme("blue")

class App(customtkinter.CTk):
    __APP_NAME = "Flight Radar"
    __WIDTH = 800
    __HEIGHT = 400

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        ##Configuration de la fenêtre ----------------------------------------------------------------------

        #Configuration Taille + Nom
        self.title(self.__APP_NAME)
        self.geometry(str(self.__WIDTH) + "x" + str(self.__HEIGHT))
        self.minsize(self.__WIDTH,self.__HEIGHT)

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        ##Partie Bouton ------------------------------------------------------------------------------------

        self.frame_left = customtkinter.CTkFrame(master=self, width=150, corner_radius=0, fg_color=None)
        self.frame_left.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")


        #creation Bouton
        self.button_marker = customtkinter.CTkButton(master=self.frame_left,
                                                command=self.set_marker_event,
                                                text="Rafraichir")
        self.button_marker.grid(pady=20, padx=60,column=9, row=0)

        self.quitbutton = customtkinter.CTkButton(master=self.frame_left,
                                                text="Quitter",
                                                command=self.on_closing)
        self.quitbutton.grid(pady=280, padx=60, column=9, row=2)

        ##Partie Carte -------------------------------------------------------------------------------------
        #creation de la partie de la fenetre dans la quel on met la carte
        self.frame_right = customtkinter.CTkFrame(master=self, corner_radius=0)
        self.frame_right.grid(row=0, column=1, rowspan=1, pady=0, padx=0, sticky="nsew")

        self.frame_right.grid_rowconfigure(1, weight=1)
        self.frame_right.grid_rowconfigure(0, weight=0)
        self.frame_right.grid_columnconfigure(0, weight=1)
        self.frame_right.grid_columnconfigure(1, weight=0)
        self.frame_right.grid_columnconfigure(2, weight=1)

        self.map_widget = TkinterMapView(self.frame_right, corner_radius=0)
        self.map_widget.grid(row=1, rowspan=1, column=0, columnspan=3, sticky="nswe", padx=(0, 0), pady=(0, 0))
        self.map_widget.set_address("Chelles-Paris")
        self.map_widget.set_zoom(15)

        #Configuration de la partie de la fenêtre
        self.frame_right.grid_rowconfigure(1, weight=1)
        self.frame_right.grid_rowconfigure(0, weight=0)
        self.frame_right.grid_columnconfigure(0, weight=1)
        self.frame_right.grid_columnconfigure(1, weight=0)
        self.frame_right.grid_columnconfigure(2, weight=1)

        #Configuration Icon Marker
        self.img = Image.open("m_resize.png")
        self.img = self.img.resize((75,75), Image.ANTIALIAS)
        self.icon = ImageTk.PhotoImage(self.img)
        self.liste_avion = []
        self.marker_list = []

    def on_closing(self, event=0):
        self.destroy()
        return True

    def start(self):
        self.mainloop()


        ## Connexion SQL + Affichage avion -----------------------------------------------------------------

    def set_marker_event(self):
        #connexion à un base en localhost pour effectuer des test en attendant la base de données:
        self.connect = pymysql.connect(host="localhost", port=3306, user="root", database="tour_de_control")
        self.cursor  = self.connect.cursor()
        self.liste_avion = []
        for marker in self.marker_list:
            marker.delete()
        self.cursor.execute("SELECT COUNT(id_avion) FROM avion")
        nb_avion = self.cursor.fetchone()
        if nb_avion != 0:
            for i in range(nb_avion[0]):
                self.cursor.execute("SELECT Latitude, Longitude, id_avion FROM avion WHERE id_avion=" + str(1+i))
                self.liste_avion.append(self.cursor.fetchone())
        for coordonnées in self.liste_avion:
            if isinstance(coordonnées, tuple):
                self.marker = self.map_widget.set_marker(coordonnées[0], coordonnées[1], icon=self.icon)
                self.marker_list.append(self.marker)

if __name__ == "__main__":
    app = App()
    app.start()
    while True:
        if app.on_closing():
            break

