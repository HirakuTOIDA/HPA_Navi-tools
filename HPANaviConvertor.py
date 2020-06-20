# -*- coding: utf-8 -*-
"""
Data conversion script for HPA_Navi.


"""
import os
import threading
import tkinter as tk
import tkinter.filedialog
import SylphideProcessor


class Application(tk.Frame):
    """
    GUI for data proceccing.

    Attributes
    ----------
    @todo

    """

    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack()
        self.master.title('HPA_Navi Convertor')

        _pad = [5, 5]

        self.bt = tk.Button(self, text=u'Open & Convert',
                            command=self.fileopen)
        self.bt.pack(fill=tk.BOTH, padx=_pad[0], pady=_pad[1])

        self.filename_str = tk.StringVar()
        self.filename_str.set(u"File name: ")
        self.lbfn = tk.Label(self, textvariable=self.filename_str)
        self.lbfn.pack(anchor=tk.W, padx=_pad[0], pady=_pad[1])

        self.filesize_str = tk.StringVar()
        self.filesize_str.set(u"File size: ")
        self.lbfs = tk.Label(self, textvariable=self.filesize_str)
        self.lbfs.pack(anchor=tk.W, padx=_pad[0], pady=_pad[1])

        self.status_str = tk.StringVar()
        self.status_str.set(u"Select file.")
        self.lbst = tk.Label(self, textvariable=self.status_str)
        self.lbst.pack(anchor=tk.W, padx=_pad[0], pady=_pad[1])

    def fileopen(self):
        """
        File open dialog.

        Returns
        -------
        None.

        """
        fTyp = [("log file", "*.dat")]
        filename = tk.filedialog.askopenfilename(filetypes=fTyp)
        if len(filename) > 0:
            self.bt.configure(state=tk.DISABLED)
            self.status_str.set(u"File selected.")
            th = threading.Thread(target=self.convert, args=(filename,))
            th.start()

    def func_handler_append(self, func, *args):
        """
        Page selector for appending converted data.

        Parameters
        ----------
        func : TYPE
            DESCRIPTION.
        *args : TYPE
            DESCRIPTION.

        Returns
        -------
        TYPE
            DESCRIPTION.

        """
        return func.append(*args)

    def func_handler_raw2phys(self, func):
        """
        Page selector for converting data with pysical units.

        Parameters
        ----------
        func : TYPE
            DESCRIPTION.

        Returns
        -------
        TYPE
            DESCRIPTION.

        """
        return func.raw2phys()

    def func_handler_save_raw_csv(self, func, *args):
        """
        Page selector for saving csv file.

        Parameters
        ----------
        func : TYPE
            DESCRIPTION.
        *args : TYPE
            DESCRIPTION.

        Returns
        -------
        TYPE
            DESCRIPTION.

        """
        return func.save_raw_csv(*args)

    def convert(self, filename):
        """
        Open and convert binary log file.

        Parameters
        ----------
        filename : str
            Log file to be converted.

        Returns
        -------
        None.

        """
        with open(filename, 'rb') as fobj:
            self.filename_str.set(u"File name: " + filename)
            filesize = os.path.getsize(filename)
            self.filesize_str.set("File size: {0:,} byte".format(filesize))
            self.status_str.set(u"File opened.")
            name, _ = os.path.splitext(filename)
            readsize = 0
            pb_previous = 0

            page = SylphideProcessor.page()
            page_list = ["a", "f", "h", "l", "m", "n", "o", "p", "s", "t", "v"]
            for page_elem in page_list:
                exec('page' + page_elem +
                     ' = SylphideProcessor.page' + page_elem + '()')
            pageg = SylphideProcessor.pageg()

            self.status_str.set(u"Reading file.")
            while True:
                h_data = fobj.read(page.size)
                if len(h_data) < page.size:
                    break
                readsize += page.size
                pb_current = int(readsize / filesize * 100)
                if pb_previous < pb_current:
                    self.status_str.set(u"Reading file. {}% done."
                                        .format(pb_current))
                    pb_previous = pb_current
                self.func_handler_append(eval("page" + chr(h_data[0]).lower()),
                                         h_data)

            self.status_str.set(u"Converting unit.")
            for page_elem in page_list:
                self.func_handler_raw2phys(eval("page" + page_elem))

            self.status_str.set(u"Writing csv files.")
            for page_elem in page_list:
                self.func_handler_save_raw_csv(eval("page" + page_elem),
                                               name + "_" +
                                               page_elem.upper() + ".csv")
            self.status_str.set(u"Writing ubx file.")
            pageg.save_raw_ubx(name + "_G.ubx")

            self.status_str.set(u"Done.")
            self.bt.configure(state=tk.NORMAL)


if __name__ == '__main__':
    root = tk.Tk()
    app = Application(master=root)
    app.mainloop()
