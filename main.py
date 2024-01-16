from gui import SatForm
import tkinter as tk

# Charles Grace
# Programming Logic 3 - Homework 4
# NOTE: must install the 'skyfield' library for this application to work.


if __name__ == '__main__':
    root = tk.Tk()
    app = SatForm(root)
    app.on_load()
    root.mainloop()

