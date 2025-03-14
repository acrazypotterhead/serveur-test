#!/usr/bin/env python3
# -+-coding: utf-8 -+-

import sys,os
import multiprocessing as mp

from time import time,sleep
import numpy as np
import matplotlib.pyplot as plt

import kivy

from kivy.app           import App
from kivy.lang          import Builder
#from kivy.core.window   import Window
from kivy.clock         import Clock
from kivy.uix.label     import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button    import Button

KV_MAIN_PANEL="""
<MainPanel>:
    BoxLayout:
        orientation: 'vertical'
        size: root.size

        Slider:
            id: ID_SLIDER_FREQ
            min: 1.0
            max: 10
            step: 1
            orientation: 'vertical'
            on_value: root.on_slide(self)
        BoxLayout:
            orientation: 'horizontal'
            padding: 10
            spacing: 10
            Label:
                id: ID_TXT_FREQ
                text: str(ID_SLIDER_FREQ.value)
                size_hint_x: .40
                font_size: 20
            Label:
                id: ID_TXT_PROC_TIME
                size_hint_x: .40
                font_size: 20
        BoxLayout:
            orientation: 'horizontal'
            padding: 10
            spacing: 10
            
            BoxLayout:
                orientation: 'vertical'
                Switch:
                    id: ID_CK_VERBOSE
                    on_active: root.on_verbose(self, self.active)
                    size_hint_x: .20 
                Label:
                    text: 'VERBOSE' if ID_CK_VERBOSE.active else 'QUIET'
                    size_hint_x: .20
                    font_size: 20
           
            Button:
                id: ID_BT_START
                text: "START"
                font_size: 48
                size_hint_x: .5
                on_press: root.on_press(self)
                
"""

def my_process(qin,qout):
    """
    :param qin:  input queue recive msg
    :param qout: output queue send msg to MainApp (kivy)
    """
    t0 = time()
    print(" --> PROC start multiprocess")

   # -- plot fig
    x = np.linspace(0,1,1000)
    y = np.sin(  2 * np.pi * x )
    plt.ion()

    fig = plt.figure()
    ax = fig.add_subplot(111)
    line1, = ax.plot(x, y, 'r-')
    fig.suptitle(f"Multi Processing Example Freq",fontsize=16)

    status = True
    verbose = False

    while status:
        sleep(0.2) # delay for polling qin
        freq   = None

        while not qin.empty():
           data = qin.get(block=False)
           if data.get("exit",False):
              status = False
              break

           freq    = data.get('freq',freq)
           verbose = data.get('verbose',verbose)

        if freq is not None:
           line1.set_ydata(np.sin( 2 * np.pi * x *  freq))
           fig.canvas.draw()
           fig.canvas.flush_events()
           fig.suptitle(f"Multi Processing Example Freq: {freq}",fontsize=16)

        t = time() - t0
        if verbose:
           qout.put( f"multiprocess time: {t:.3f}" )

    # -- clean up pro for closing
    print(" --> PROC start closing")
    plt.close(fig)
    plt.pause(1)
    print(" --> PROC done multiprocess")


class MSG():
    def __init__(self):
        self.qget = mp.Queue()
        self.qsend = mp.Queue()
        self._proc = None
        self.proc_logger = None

    def start_process(self,*args,**kwargs):
        if self._proc is None:
            self._proc = mp.Process(target=my_process, args=(self.qsend, self.qget))
            self._proc.start()
        if self._proc.is_alive:
           print('==> MAIN proc is running')
        else:
           print('==> MAIN proc starting')
           self._proc.start()
           print('==> MAIN proc started')

    def stop_process(self):
        if self._proc is not None:
           if self._proc.is_alive:
              self.qsend.put({'exit': True})
              self._proc.join()
              print('==> MAIN proc send stop')
        self._proc = None

    def send(self,data):
        self.qsend.put(data)

    def get(self):
        try:
           return self.qget.get(block=False)
        except: # empty
           return None

    def close(self):
        self.stop_process()
        if self.qget:
            self.qget.close()
        if self.qsend:
            self.qsend.close()

class MainPanel(BoxLayout):
    Builder.load_string(KV_MAIN_PANEL)

    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.msg_logger = None
        self.msg = MSG()

    def on_press(self,obj):
        if obj.text == 'START':
           self.start_process(obj)
        else:
            self.stop_process(obj)
            obj.text = 'START'

    def start_process(self,obj):
        self.msg.start_process()
        obj.text = 'STOP'
        self.msg.send( {'freq': self.ids.ID_SLIDER_FREQ.value,
                        'verbose': self.ids.ID_CK_VERBOSE.active })
        self.msg_logger = Clock.schedule_once(self.get_proc_msg,0.5)

    def stop_process(self,obj):
        self.msg.stop_process()
        if self.msg_logger:
           Clock.unschedule(self.msg_logger)
        if obj is not None:
           obj.text = 'START'

    def on_verbose(self,obj,verbose):
        self.msg.send({'verbose': verbose})

    def get_proc_msg(self,obj):
        msg = self.msg.get()
        if msg:
          # print(f'==> MAIN proc get queue {msg}')
           self.ids.ID_TXT_PROC_TIME.text = msg
        try:
           self.msg_logger = Clock.schedule_once(self.get_proc_msg,0.5)
        except:
            pass

    def on_slide(self,obj):
        self.msg.send({'freq': obj.value})

    def on_close(self,*args,**kwargs):
        self.stop_process(None)
        sleep(1)
        self.msg.close()
        App.get_running_app().stop()

class MyApp(App):
    def __init__(self, **kwargs):
        self.title = 'MyApp Multiprocess'
        super().__init__( **kwargs)
        Window.bind(on_request_close=self.close_request)

    def build(self):
        self.MainPanel = MainPanel()
        return self.MainPanel

    def close_request(self,*args,**kwargs):
        self.MainPanel.on_close()

if __name__ == '__main__':
   mp.freeze_support()
   mp.set_start_method('spawn')
   from kivy.core.window import Window # !!! avoid second kivy-window
   MyApp().run()