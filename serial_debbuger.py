import sys
import glob
import serial
import tkinter as tk
from tkinter import scrolledtext
from tkinter import END, ttk
from tkinter import  DISABLED, messagebox
from tkinter.font import NORMAL
from tkinter import filedialog as fd
import threading

CPU_READY = b'\x03'


class serial_debug:
    def __init__(self):
        self.started = False
        self.filename = ""
        self.memory = {}


    def start(self):
        self.started = True
        if self.filename == "":
            messagebox.showerror(message="Primero debes seleccionar un archivo.", title="Selecciona un archivo")
            return
        f = open(self.filename, "rb")
        for j in range(20):
            array=[]
            for _ in range(4):
                array.append(f.read(1))
            self.memory[j*4] = array
        print_gui(str(self.memory))
        print_gui(str(self.memory[0]))
        threading.Thread(target=self.run).start()

    def stop(self):
        self.started = False

    def run(self):
        self.ser = serial.Serial(input_puerto.get(), input_baud.get(), rtscts=True)
        if not self.ser.is_open:
            self.ser.open()
        print_gui("Esperando cpu_ready")
        self.ser.write(b'\x00\x01')
        self.wait_cpu_ready()

    def start_debug(self):
        pass

    def step_debug(self):
        boton_step.configure(state=DISABLED)
        self.ser.write(b'\x00\x02')
        while self.started:
            addr = int.from_bytes(self.ser.read(4)[:4], byteorder='little', signed=False)
            print_gui("Instrucción recibida: " + str(addr))
            self.ser.reset_input_buffer()
            if addr:
                break
        enviar_instruccion(addr, self.memory, self.ser)
        self.wait_cpu_ready()

    def wait_cpu_ready(self):
        while self.started:
            if self.ser.read(1) == CPU_READY:
                boton_step.configure(state=NORMAL)
                break

    def stop_debug(self):
        pass


    def select_file(self):
        self.filename = fd.askopenfilename(
        title='Abrir archivo',
        initialdir='/',
        filetypes=(
            ('text files', '*.txt'),
            ('All files', '*.*')
        ))
        label_file.config(text= "Archivo: " + self.filename)
    

sd = serial_debug()

def serial_ports():
    """ 
        https://stackoverflow.com/questions/12090503/listing-available-com-ports-with-python
        Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result

def rescan():
    puertos = serial_ports()
    input_puerto.configure(values=puertos)
    if puertos:
        input_puerto.current(0)

def clear():
    out_text.configure(state=NORMAL)
    out_text.delete("1.0", tk.END)
    out_text.configure(state=DISABLED)

def print_gui(text, new_line = True):
    out_text.configure(state=NORMAL)
    out_text.insert(tk.END, text)
    if new_line:
        out_text.insert(tk.END, "\n")
    out_text.configure(state=DISABLED)
    out_text.see("end")

def enviar_instruccion(addr, memory, fpgaData):
    for i in range(8):
        if(i==0):
            fpgaData.write(b'\x01')
        elif(i==1):
            fpgaData.write(bytearray(memory[addr][3]))
        elif(i==2):
            fpgaData.write(b'\x02')
        elif(i==3):
            fpgaData.write(bytearray(memory[addr][2]))
        elif(i==4):
            fpgaData.write(b'\x03')
        elif(i==5):
            fpgaData.write(bytearray(memory[addr][1]))
        elif(i==6):
            fpgaData.write(b'\x04')
        elif(i==7):
            fpgaData.write(bytearray(memory[addr][0]))


puertos = serial_ports()
root = tk.Tk()
root.title("Serial debugger")
#root.iconbitmap("logo.ico")
root.geometry("740x550")

frame_conf = tk.LabelFrame(root, relief=tk.GROOVE, padx=10, pady=10, text="Configuración")
frame_conf.grid(row=0, column=0)

label_puerto = tk.Label(frame_conf, text="Puerto: ")
label_puerto.grid(row=0, column=0)

input_puerto = ttk.Combobox(frame_conf, state="readonly", values=puertos)
input_puerto.grid(row = 0, column = 1)
if puertos:
    input_puerto.current(0)

boton_rescan = tk.Button(frame_conf, text="Reescanear", command=rescan)
boton_rescan.grid(row=0, column=2)

boton_open = tk.Button(frame_conf, text='Abrir archivo', command=sd.select_file)
boton_open.grid(row=0, column=3, padx=20, pady=10)

label_baud = tk.Label(frame_conf, text="Baudrate: ")
label_baud.grid(row = 0, column = 4)

input_baud = ttk.Combobox(frame_conf, state="readonly", values=["9600",
                                                               "115200"])
input_baud.grid(row=0, column=5)
input_baud.current(0)

boton_conectar = tk.Button(frame_conf, text="Conectar", command=sd.start)
boton_conectar.grid(row=0, column=6)

label_file = tk.Label(frame_conf, text="Archivo: *Debes elegir un archivo*")
label_file.grid(row = 1, column = 0, columnspan=6)


frame_send = tk.LabelFrame(root, padx=10, pady=10, text="Steps")
frame_send.grid(row=2, column=0)


boton_start = tk.Button(frame_send, padx=10, text="Start", command=sd.start_debug)
boton_start.grid(row=0, padx=10, column=0)

boton_step = tk.Button(frame_send, padx=10, text="Step", state=DISABLED, command=sd.step_debug)
boton_step.grid(row=0, padx=50, column=1)

boton_stop = tk.Button(frame_send, padx=10, text="Stop", command=sd.stop_debug)
boton_stop.grid(row=0, padx=10, column=2)

frame_out = tk.LabelFrame(root, relief=tk.GROOVE, text="Salida")
frame_out.grid(row=3, column=0)

boton_stop = tk.Button(frame_out, text="Detener", command=sd.stop)
boton_stop.grid(row=0, column=0)

boton_clear = tk.Button(frame_out, text="Limpiar salida", command=clear)
boton_clear.grid(row=0, column=1)

out_text = scrolledtext.ScrolledText(frame_out,
                                     yscrollcommand=True,
                                     state=DISABLED, 
                                     font= ("Consolas", 10),
                                     width=100,
                                     height=20)
out_text.grid(row=1,column=0, columnspan=2)

def on_closing():
    if messagebox.askokcancel("Cerrar", "¿Realmente quieres salir?"):
        root.destroy()
        

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()