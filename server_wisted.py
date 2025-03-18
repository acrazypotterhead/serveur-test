# install_twisted_rector must be called before importing and using the reactor
from kivy.support import install_twisted_reactor

install_twisted_reactor()

from twisted.internet import reactor
from twisted.internet import protocol


class EchoServer(protocol.Protocol):
    def dataReceived(self, data):
        response = self.factory.app.handle_message(data)
        if response:
            self.transport.write(response)


class EchoServerFactory(protocol.Factory):
    protocol = EchoServer

    def __init__(self, app):
        self.app = app


from kivy.app import App
from kivy.uix.label import Label
x, y, z = [], [], []

class TwistedServerApp(App):
    label = None

    def build(self):
        self.label = Label(text="server started\n")
        reactor.listenTCP(8000, EchoServerFactory(self))
        return self.label

    def handle_message(self, msg):
        msg = msg.decode('utf-8')
        self.label.text = "received:  {}\n".format(msg)
        msg = format(msg)
        split_msg = msg.split(",")
        if len(split_msg) == 3:
            x.append(float(split_msg[0]))
            y.append(float(split_msg[1]))
            z.append(float(split_msg[2]))

        if msg == "ping":
            msg = "Pong"
        if msg == "plop":
            msg = "Kivy Rocks!!!"
        self.label.text += "responded: {}\n".format(msg)
        

        print(f"x: ", x)
        print("y: ", y)
        print("z: ", z)
        print("\n")
        return msg.encode('utf-8')
if __name__ == '__main__':
    TwistedServerApp().run()