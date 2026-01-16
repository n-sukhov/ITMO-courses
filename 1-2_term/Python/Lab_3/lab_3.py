#Вариант 1
from tkinter import *
from tkinter import ttk
import time
from random import choice, shuffle
from string import ascii_uppercase, digits
from PIL import Image, ImageTk


def gen_block():
    block = []
    for i in range(2):
        time.sleep(0.1)
        pb.step(1)
        pb.update()
        block.append(choice(digits))
    for i in range(3):
        time.sleep(0.1)
        pb.step(1)
        pb.update()
        block.append(choice(ascii_uppercase))
    shuffle(block)
    block = "".join(block)
    return block


def keygen():
    key = gen_block() + '-' + gen_block() + '-' + gen_block()
    return key


def clicked():
    pb.value = 0
    text.config(text = keygen())
    text.config(fg="black")


def copy_text():
    window.clipboard_clear()
    window.clipboard_append(text.cget("text"))

window = Tk()
window.geometry('1000x600')
window.title("Keygen for game ГОООООООЛ!")

image = Image.open('Lab_3/goooal.png').resize((1000, 600))
img_tk = ImageTk.PhotoImage(image)

C = Canvas(window, height=600, width=1000)
background_label = Label(window, image=img_tk)
background_label.place(x=0, y=0, relwidth=1, relheight=1)

frame = Frame(window, borderwidth=0, background="white")
frame.place(relx=0.5, rely=0.5, anchor='center')
text = Label(frame, text='XXXXX-XXXXX-XXXXX', fg="gray", bg="white", font=('Arial', 20))
text.grid(column=1, row=0, padx=10, pady=10)

gen_btn = Button(window, text="Генерировать", command=clicked)
gen_btn.place(relx=0.35, rely=0.7, anchor='center')

copy_btn = Button(window, text="Скопировать", command=copy_text)
copy_btn.place(relx=0.65, rely=0.7, anchor='center')

exit_btn = Button(window, text="Выход", command=window.destroy)
exit_btn.place(relx=0.9, rely=0.9, anchor='center')

s = ttk.Style()
s.theme_use('alt')
s.configure("green.Horizontal.TProgressbar", background='green')

pb = ttk.Progressbar(window, orient='horizontal', length=300, mode='determinate', style="green.Horizontal.TProgressbar", maximum=15)
pb.place(relx=0.5, rely=0.6, anchor='center')
style = ttk.Style()


window.mainloop()