from tkinter import Tk, Frame, Canvas, Scrollbar, TclError, Label, Entry, StringVar, Toplevel, simpledialog, Button
from tkinter.ttk import Scrollbar
from os import listdir, access, W_OK, startfile
from os.path import join, isdir, isfile, dirname, basename, splitext, expanduser
from sys import argv
from json import dump, load, JSONDecodeError
from winsound import MessageBeep

from AliasTkFunctions import fix_resolution_issue, resize_window

from functions import *

fix_resolution_issue()

main = Tk()
resize_window(main, 2, 2, False)
main.title("Seeker")
main.configure(background="#ffffff")
main.protocol("WM_DELETE_WINDOW", lambda: update_user_settings())
main.bind("<Alt-F4>", lambda _: update_user_settings())

loop = 0

while True:
    try:
        user_settings = load(open("user_settings.json", "r"))
        break
    except (FileNotFoundError, JSONDecodeError):
        dump({
            "show_file_extensions": False,
            "last_dir": expanduser("~")
        }, open("user_settings.json", "w"))
    loop += 1


class ScrollableFrame(Frame):
    def __init__(self, parent=main, **kwargs):
        self.frame = Frame(parent)
        self.frame.grid(**kwargs)
        self.frame.grid_propagate(False)

        self.canvas = Canvas(self.frame)
        self.canvas.grid(row=0, column=0, sticky="nsew")

        def on_enter():
            self.canvas.bind_all("<MouseWheel>", mouse_scroll)

        def on_leave():
            self.canvas.unbind_all("<MouseWheel>")

        self.canvas.bind("<Enter>", lambda event: on_enter())
        self.canvas.bind("<Leave>", lambda event: on_leave())

        self.scrollbar = Scrollbar(self.frame, orient="vertical", command=self.canvas.yview)
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)
        
        super().__init__(self.canvas)
        self.canvas.create_window((0, 0), window=self, anchor="nw")

        def resize_inner_frame():
            canvas_width = self.winfo_reqwidth()
            canvas_height = self.winfo_reqheight()
            self.canvas.config(width=canvas_width, height=canvas_height)
            self.config(width=canvas_width, height=canvas_height)
            
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        self.canvas.bind("<Configure>", lambda event: resize_inner_frame())
        self.bind("<Configure>", lambda event: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.bind("<Configure>", lambda event: self.canvas.configure(background=self.cget("background")))

        def mouse_scroll(event):
            try:
                self.canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")
            except TclError:
                self.canvas.unbind_all("<MouseWheel>")

        self.scrollbar = Scrollbar(self.frame, orient="horizontal", command=self.canvas.xview)
        self.scrollbar.grid(row=1, column=0, sticky="ew")
        self.canvas.configure(xscrollcommand=self.scrollbar.set)


def open_dir(folder):
    global current_dir

    content = [i for i in listdir(folder) if isdir(join(folder, i))] + [i for i in listdir(folder) if
                                                                        isfile(join(folder, i))]

    current_dir.set(folder)
    user_settings["last_dir"] = folder

    children_copy = explorer.winfo_children()

    explorer.canvas.yview_moveto(0.0)

    class Link(Label):
        def __init__(self, path, display_name=None, empty_link=False, **kwargs):
            if display_name is None:
                display_name = f"{"📁 " if isdir(path) else ""}{basename(path)}"
                if not user_settings["show_file_extensions"] and not isdir(path):
                    display_name = splitext(display_name)[0]

            super().__init__(explorer, text=display_name, anchor="w",
                             background=explorer.cget("background"), **kwargs)
            self.pack(side="top", fill="x")

            if not empty_link:
                self.bind("<Enter>", lambda _: self.configure(background="#cce8ff"))
                self.bind("<Leave>", lambda _: self.configure(background=explorer.cget("background")))

                self.bind("<Button-1>", lambda _: handle(path, mode="preview"))
                self.bind("<Double-Button-1>", lambda _: handle(path, mode="open"))
                self.bind("<Button-3>", lambda _: open_menu(path))

    parent = dirname(current_dir.get())
    if basename(current_dir.get()):
        Link(parent, basename(parent) if basename(parent) else "Home", font="TkDefaultFont 9 bold")

    for f in range(0, max(len(children_copy), len(content)) + 1):
        try:
            children_copy[f].destroy()
        except IndexError:
            pass

        try:
            f = join(current_dir.get(), content[f])
            Link(f, foreground=get_access_colour(f), empty_link=not access(f, 4))
        except IndexError:
            pass


def open_file(file, mode="preview"):
    if mode == "open":
        startfile(file)


def handle(path, **kwargs):
    try:
        if isdir(path):
            open_dir(path)

        elif isfile(path):
            open_file(path, **kwargs)

        else:
            MessageBeep(16)

    except PermissionError:
        pass


def open_menu(path):
    modal = Toplevel()
    modal.overrideredirect(True)
    modal.bind("<FocusOut>", lambda event: modal.destroy())
    modal.focus_force()

    modal.configure(pady=2, padx=2, highlightthickness=1, background="#ffffff")

    x, y = modal.winfo_pointerxy()
    modal.geometry(f"+{x+10}+{y-5}")

    class Link(Label):
        def __init__(self, name=None, function=None):
            super().__init__(modal, text=name, anchor="w", background=modal.cget("background"))
            self.pack(side="top", fill="x")

            self.bind("<Enter>", lambda _: self.configure(background="#cce8ff"))
            self.bind("<Leave>", lambda _: self.configure(background=modal.cget("background")))

            self.bind("<Button-1>", function)

    if access(path, W_OK):
        Link("Rename", lambda _: print(simpledialog.askstring("", "")))

    modal.update_idletasks()


def update_user_settings():
    dump(user_settings, open("user_settings.json", "w"))
    main.destroy()


def open_settings():
    pass


main.grid_columnconfigure(0, weight=3)
main.grid_columnconfigure(1, weight=3)
main.grid_columnconfigure(2, weight=4)

main.grid_rowconfigure(0, weight=0)
main.grid_rowconfigure(1, weight=1)


current_dir = StringVar(value="")

explorer = ScrollableFrame(row=0, rowspan=3, column=2, sticky="nsew")
explorer.configure(background="#ffffff")

nav_frame = Frame()
nav_frame.grid(row=0, column=0, columnspan=2, sticky="new")

Button(nav_frame, text="⚙", width=3, command=open_settings).pack(side="left", fill="y")

nav_bar = Entry(nav_frame, textvariable=current_dir, justify="center")
nav_bar.pack(side="left", fill="both", expand=True)
nav_bar.bind("<Return>", lambda _: handle(current_dir.get()))

Button(nav_frame, text="Go!", width=3, command=lambda: handle(current_dir.get())).pack(side="left", fill="y")

preview = Frame()
preview.grid(row=1, column=0, sticky="nsew")

info = Frame()
info.grid(row=1, column=1, sticky="nsew")

open_dir(user_settings["last_dir"])


def start():
    if len(argv) > 1 and isdir(argv[1]):
        open_dir(argv[1])

    elif len(argv) > 1 and isfile(argv[1]):
        open_dir(dirname(argv[1]))
        open_file(argv[1])


main.after(100, start)

main.mainloop()
