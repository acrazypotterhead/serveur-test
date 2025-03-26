from kivy.uix.gridlayout import product
import threading
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from kivy.lang import Builder
from kivy_garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
import matplotlib.pyplot as plt
import kivy_matplotlib_widget
from matplotlib import pyplot as plt
from matplotlib.ticker import MaxNLocator
import matplotlib as mpl
import numpy as np
import time as time
from twisted.internet import reactor, protocol
import random
import csv
import os
from widgets import Jauge

import logging
logging.getLogger('matplotlib.font_manager').disabled = True
#optimized draw on Agg backend
mpl.rcParams['path.simplify'] = True
mpl.rcParams['path.simplify_threshold'] = 1.0

#depending of the data. This can increase the graph rendering
#see matplotlib doc for more info
#https://matplotlib.org/stable/users/explain/artists/performance.html#splitting-lines-into-smaller-chunks
mpl.rcParams['agg.path.chunksize'] = 1000



server = None
lock = threading.Lock()

add_count = 0
x = [] 
y = [] 
z = [] 
time_x = [] 
max_data_window =10000
ratio_data = 3
timestamps = {}

# Décorateur pour exécuter une fonction dans un thread séparé
def thread(function):
    def wrap(*args, **kwargs):
        t = threading.Thread(target=function, args=args, kwargs=kwargs, daemon=True)
        t.start()
        return t
    return wrap

#Activer le mode moniteur de Kivy (obtenir des informations sur le taux de FPS dans la barre supérieure)
def activate_monitor_mode():
    
    from kivy.core.window import Window
    from kivy.modules import Modules
    from kivy.config import Config

    Config.set('modules', 'monitor', '')        
    Modules.activate_module('monitor',Window)



# DataReceiver est une classe qui hérite de protocol.Protocol et est responsable de la réception et du traitement des données.
# Attributs:
#     start_time (int): L'heure de début en millisecondes.
#     parent (objet): L'objet parent qui contient l'attribut paused.
#     count (int): Un compteur pour suivre le nombre de paquets de données reçus.
# Méthodes:
#     dataReceived(data):
#         Reçoit des données, les décode et met à jour le tableau dans la classe FirstWindow si le parent n'est pas en pause.
#         Si les données sont invalides, elle affiche un message d'erreur.

class DataReceiver(protocol.Protocol):
    
    def __init__(self, start_time, parent):
        super().__init__()
        self.count = 0
        self.start_time = start_time
        self.parent = parent

    def dataReceived(self, data):
        if self.parent.paused:

            return
        
        try:
            with lock:
                values = data.decode("utf-8").strip().split(',')
                if len(values) != 3:
                    raise ValueError("Invalid data length")
                xdata, ydata, zdata = map(int, values)
                current_time = int(time.time()*1000) #self.count
                elapsed_time = current_time - self.start_time
                reactor.callFromThread(FirstWindow.update_array,  xdata, ydata, zdata, elapsed_time)
                self.count += 1
        except ValueError as e:
            print(f"Invalid data received: {data} - Error: {e}")


# DataReceiverFactory est une classe qui hérite de protocol.Factory et est responsable de la création d'instances de DataReceiver.
# Attributs:
#     start_time (int): L'heure de début en millisecondes.
#     parent (objet): L'objet parent qui contient l'attribut paused.
# Méthodes:
#     buildProtocol(addr):
#         Crée et retourne une instance de DataReceiver avec l'heure de début et le parent spécifiés.

class DataReceiverFactory(protocol.Factory):
    def __init__(self, start_time, parent):
        self.start_time = start_time
        self.parent = parent

    def buildProtocol(self, addr):
        return DataReceiver(self.start_time, self.parent)



class FirstWindow(Screen):

    

    def __init__(self, **kwargs):
        super(FirstWindow, self).__init__(**kwargs)
        self.data_count = 0
        self.count_time = 0
        self.index = -1
        self.mod_base = 0
        self.call_time = 0
        self.first_plot_time = None
        self.last_plot_time = None
        self.server_thread = None
        self.running = False
        self.call_time = 0
        self.add_index = 0
        self.status_serv =False

        self.paused = False
        self.pause_deferred = None

        # Définir le chemin du dossier où sauvegarder les données et les graphiques
        self.save_directory = "saved_data"
        # Créer le dossier s'il n'existe pas
        os.makedirs(self.save_directory, exist_ok=True)


    line1 = None
    line2 = None
    line3 = None
    min_index=0
    max_index=0
    current_xmax_refresh=None


    def update_status(self, status):
        Clock.schedule_once(lambda dt: self.ids.status_label.setter('text')(self.ids.status_label, status))



    def update_array( xdata, ydata, zdata, timestamp):
        global add_count
        with lock:
            x.append(xdata)
            y.append(ydata)
            z.append(zdata)
            time_x.append(timestamp)
            
            add_count += 1
            #if len(x) == 200:
            #    print(f"len time {len(time_x)}")
            #    print(f"time {time_x}")

            #print(f"add_count {add_count}")

            
           
     

    def save_graph_and_data(self):
        if self.figure_wgt.figure:
            """Sauvegarde le graphe sous forme d'image et les données en CSV."""
            # Chemins complets des fichiers
            graph_path = os.path.join(self.save_directory, self.ids.file_name_input.text + ".png")
            csv_path = os.path.join(self.save_directory, self.ids.file_name_input.text + ".csv")
            # Sauvegarde du graphe en image
            self.figure_wgt.figure.savefig(graph_path)
            
            
            # Sauvegarde des données en CSV
            with open(csv_path, mode="w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["Timestamp", "X", "Y", "Z"])  # En-têtes du CSV
                for i in range(len(time_x)):
                    writer.writerow([time_x[i], x[i], y[i], z[i]])
            
            
        else:
            print("Aucun graphique à sauvegarder.")

            
        
    @thread
    def start_server(self):
        
        if self.status_serv == False:
      
            self.status_serv = True
            self.update_status("Server started.")
            self.ids.status_server_button.text = "Stop Server"
            self.start_time = int(time.time() * 1000)   
            
            self.server = reactor.listenTCP(8000, DataReceiverFactory(self.start_time, self))

            if not reactor.running:
                reactor.run(installSignalHandlers=False)
            
        else:
            
            self.stop_server()

        
        

    def stop_server(self):
        """ Arrête proprement le serveur. """
        try:
            if self.server:
                self.server.stopListening()
                self.server = None  
        
            
            self.update_status("[ARRÊT] Server stopped.")
            reactor.stop()
        except:
            self.update_status("[ARRÊT] Server already stopped. Relaunch the application.")
            


    def toggle_pause_resume(self):
        """ Met en pause ou reprend la réception des données. """
        if self.paused:
            self.paused = False
            Clock.unschedule(self.update_graph)
            #self.reset_graph()
            self.update_status("[EN COURS] Server resumed.")
            self.ids.pause_resume_button.text = "Pause Reception"
            self.start_time = int(time.time() * 1000)
        else:
            self.paused = True
            
            self.update_status("[PAUSE] Server paused.")
            self.ids.pause_resume_button.text = "Resume Reception"

       

    def on_enter(self):
        activate_monitor_mode()
    
    def reset_graph(self):
        """Réinitialise les données et l'affichage du graphique"""
        global x, y, z, time_x
        with lock:
            x.clear()
            y.clear()
            z.clear()
            time_x.clear()
        
        self.start_graph()

        

    # initialisation du graphique
    def start_graph(self):

       
        fig, ax = plt.subplots(1, 1) # Créer une figure avec un axe et un seul graphique
        # 3 lignes pour les données X, Y et Z
        self.line1, = plt.plot([], [],color="green", label = "X")
        self.line2, = plt.plot([], [],color="red", label = "Y")
        self.line3, = plt.plot([], [],color="blue", label = "Z")


        # Configure l'axe des x pour utiliser un "locator" qui place un nombre maximum de graduations principales (ticks).
        # MaxNLocator est utilisé pour s'assurer qu'il y a au maximum 5 graduations principales sur l'axe des x.
        # prune='lower' supprime la première graduation (la plus basse) pour éviter les chevauchements ou pour des raisons esthétiques.
        ax.xaxis.set_major_locator(MaxNLocator(prune='lower',nbins=5))

        self.current_xmax_refresh = max_data_window
    
        xmin = 0
        xmax = self.current_xmax_refresh

        #Bornes de l'axe des x et y
        ax.set_xlim(xmin, self.current_xmax_refresh)
        ax.set_ylim(-40, 40)

        self.figure_wgt.figure = fig 
        self.figure_wgt.xmin = xmin 
        self.figure_wgt.xmax = xmax 
        self.home()

        Clock.schedule_once(self.update_graph_delay,1)

    def update_time(self, dt):
        time.append(self.count_time)
        self.count_time += 1
        
    def modulo (self, a):
        mod = divmod(a, max_data_window)
        return mod
    


    def update_graph_delay(self, *args):   
        #update graph data every 1/60 seconds
        Clock.schedule_interval(self.update_graph,1/6)

    def update_graph(self, *args):
        global add_count
        #print(f" appel : {self.call_time}")
        self.call_time += 1

        #if len(time_x) > 0:
        #    xmin = time_x[-1] - max_data_window * 100  # 🕒 Garde une plage de X millisecondes
        #    xmax = time_x[-1]  # 🕒 Met à jour xmax avec le dernier timestamp reçu
        #    self.figure_wgt.axes.set_xlim(xmin, xmax)

        with lock:
            current_x = time_x[self.min_index:self.max_index]
            current_y1 = x[self.min_index:self.max_index] 
            current_y2 = y[self.min_index:self.max_index] 
            current_y3 = z[self.min_index:self.max_index]
        #print(current_x)
        
        # Assurez-vous que les longueurs des tableaux sont égales
        min_length = min(len(current_x), len(current_y1), len(current_y2), len(current_y3))

        
        current_x = current_x[:min_length]
        current_y1 = current_y1[:min_length]
        current_y2 = current_y2[:min_length]
        current_y3 = current_y3[:min_length]

        self.max_index+= add_count
        add_count = 0
        if not self.max_index > len(time_x):

            self.line1.set_data(current_x,current_y1)
            self.line2.set_data(current_x,current_y2)
            self.line3.set_data(current_x,current_y3)

            

            if self.figure_wgt.axes.get_xlim()[0]==self.figure_wgt.xmin:
                if len(current_x) != 0:

                    if self.first_plot_time is None:
                        self.first_plot_time = time.time()  # Enregistrer l'heure du premier tracé
                    self.last_plot_time = time.time()  # 

                    self.index += 1
                    #print(f"index {self.index}")
                    #print(f"mod {self.modulo(self.index)}")
                    
                    if current_x[-1]< self.current_xmax_refresh:            #self.current_xmax_refresh:   

                        myfig=self.figure_wgt
                        ax2=myfig.axes
                        #use blit method            
                        if myfig.background is None:
                            myfig.background_patch_copy.set_visible(True)
                            ax2.figure.canvas.draw_idle()
                            ax2.figure.canvas.flush_events()                   
                            myfig.background = ax2.figure.canvas.copy_from_bbox(ax2.figure.bbox)
                            myfig.background_patch_copy.set_visible(False)  
                        ax2.figure.canvas.restore_region(myfig.background)

                        for line in ax2.lines:
                            ax2.draw_artist(line)
                        ax2.figure.canvas.blit(ax2.bbox)
                        ax2.figure.canvas.flush_events()                     
                    else:
                        #update axis limit
                        
                        try:
                            xmin = self.current_xmax_refresh - max_data_window//ratio_data
                            self.current_xmax_refresh = xmin + max_data_window 
                            
                            
                        except:
                            self.current_xmax_refresh =  time_x[-1]
                            #print(f"except{self.current_xmax_refresh}")
                        
                        self.figure_wgt.xmin = xmin
                        self.figure_wgt.xmax = self.current_xmax_refresh 
                        myfig=self.figure_wgt
                        ax2=myfig.axes                     
                        myfig.background_patch_copy.set_visible(True)
                        ax2.figure.canvas.draw_idle()
                        ax2.figure.canvas.flush_events()                   
                        myfig.background = ax2.figure.canvas.copy_from_bbox(ax2.figure.bbox)
                        myfig.background_patch_copy.set_visible(False)           
                        
                        self.home()
            else:
                #minimum xlim as changed. pan or zoom if maybe detected
                #update axis limit stop
                myfig=self.figure_wgt
                ax2=myfig.axes
                #use blit method            
                if myfig.background is None:
                    myfig.background_patch_copy.set_visible(True)
                    ax2.figure.canvas.draw_idle()
                    ax2.figure.canvas.flush_events()                   
                    myfig.background = ax2.figure.canvas.copy_from_bbox(ax2.figure.bbox)
                    myfig.background_patch_copy.set_visible(False)  
                ax2.figure.canvas.restore_region(myfig.background)
               
                for line in ax2.lines:
                    ax2.draw_artist(line)
                ax2.figure.canvas.blit(ax2.bbox)
                ax2.figure.canvas.flush_events()   


             #increase step value (each frame, add 20 data)
        
            #print(f"max_index {self.max_index}")
        else:
            Clock.unschedule(self.update_graph)
            myfig=self.figure_wgt          
            myfig.xmin = 0#if double-click, show all data   

        #if self.index == 500:
        #    self.print_plot_times()

    def print_plot_times(self):
        if self.first_plot_time is not None and self.last_plot_time is not None:
            elapsed_time_plot = self.last_plot_time - self.first_plot_time
            print(f"Time between first and last plot: {elapsed_time_plot} seconds")
    def home(self):
       self.figure_wgt.home()

    def set_touch_mode(self,mode):
        self.figure_wgt.touch_mode=mode

    def reset_data_count(self):
        while True:
            print(f"Data per second: {self.add_index}")
            #self.add_index = 0  # Réinitialiser le compteur
            time.sleep(1)


class SecondWindow(Screen):
    pass


class WindowManager(ScreenManager):
    pass


class ServerApp(App):
    def build(self):
        return Builder.load_file("interface_serveur.kv")


if __name__ == "__main__":

    ServerApp().run()
