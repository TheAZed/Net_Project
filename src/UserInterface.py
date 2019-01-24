import threading
from tkinter import Frame, Button, Tk, Entry, Label


class Application(Frame):
    def advertise(self):
        self.__buffer.append('Advertise')
        self.output['text'] = 'advertise sent!'

    def register(self):
        self.__buffer.append('Register')
        self.output['text'] = 'register sent!'

    def send_message(self):
        self.__buffer.append('SendMessage ' + self.input.get())
        self.output['text'] = 'message sent!'

    def createWidgets(self):
        self.output = Label(self)
        self.output['text'] = 'ready!'
        self.output.grid(row=0, column=0, columnspan=10)

        self.advertise_button = Button(self)
        self.advertise_button["text"] = "Advertise"
        self.advertise_button["command"] = self.advertise
        self.advertise_button.grid(row=1, column=2)

        self.register_button = Button(self)
        self.register_button["text"] = "Register"
        self.register_button["command"] = self.register
        self.register_button.grid(row=1, column=0)

        self.input = Entry(self)
        self.input.grid(row=1, column=5, columnspan=4)

        self.send_button = Button(self)
        self.send_button["text"] = "Send Message"
        self.send_button["command"] = self.send_message
        self.send_button.grid(row=1, column=10)

    def __init__(self, master, buffer):
        Frame.__init__(self, master, width=300, height=200)
        self.__buffer = buffer
        self.pack(fill=None, expand=False)
        self.createWidgets()


class UserInterface(threading.Thread):
    buffer = []

    def run(self):
        """
        Which the user or client sees and works with.
        This method runs every time to see whether there are new messages or not.
        """


        root = Tk()
        app = Application(root, self.buffer)
        app.mainloop()
        root.destroy()

        # while True:
        #     self.buffer.append(input("?"))


