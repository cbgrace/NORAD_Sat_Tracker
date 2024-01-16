import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import business
import filters
from exceptions import BusinessLogicException

"""
This module contains the gui elements of this application, and a variety of methods to service the gui.

Methods:
--------
    on_select(self, event):
        when the satellite dropdown menu is used, if the satellite search bar has text in it, clears the search bar. 
    clear_form(self):
        resets the form to its load state
    get_results_on_click(self):
        handles the click event for the 'Generate Results' button, starts the get_results thread.
    get_results(self, callback):
        handles the retrieval of specific satellite event data from elsewhere in the code
    display_response(self, response, latitude, longitude):
        displays the results from get_results() to the results text.
    generate_all_optimal_onclick(self):
        handles the click event for the generate all optimal events button, starts the generate_optimal thread.
    generate_optimal(self, callback):
        handles the retrieval & filtering of satellite event data for every satellite in the dropdown menu of the gui.
    display_optimal(self, response, latitude, longitude):
        displays the results of the generate_optimal() method to the gui results text.
    list_all_satellites(self):
        lists every satellite name in satellites.db to the results text
    open_help_file(self):
        opens the help file when the 'help' button is clicked.
    export_results(self):
        passes the contents of the results text to a method which will export them to results_export.txt
    on_load(self):
        handles displaying some message to the results text when the form is first loaded.
    search_entry_used(self, event):
        if the search entry is used, clears anything that might be selected in the satellite dropdown.
    sunlit_tooltip_show(self, event):
        shows the tooltip for the sunlit filter checkbox
    night_tooltip_show(self, event):
        shows the tooltip for the only night filter checkbox
    clear_tooltip_show(self, event):
        shows the tooltip for the only clear skies filter checkbox
    moon_tooltip_show(self, event):
        shows the tooltip for the moon warnings checkbox
    forecast_tooltip_show(self, event):
        shows the tooltip for the add forecast checkbox
    filter_moon_tooltip_show(self, event):
        shows the tooltip for the moon filter checkbox
    add_sunlit_tooltip_show(self, event):
        shows the tooltip for the add sunlit filter checkbox
    generate_all_optimal_tooltip(self, event):
        shows the tooltip for the generate optimal events button
    get_results_color_change_enter(self, event):
        changes the color of the get results button on mouseover
    get_results_color_change_leave(self, event):
        changes the color of the get results button back when the mouse moves away
    tooltip_hide(self, event):
        hides any tooltip that is currently displayed.
    disable_buttons(self):
        disables the buttons (for while the form is loading results)
    enable_buttons(self):
        enables buttons (for when result loading is done)
    
"""


class SatForm:
    def __init__(self, root):
        self.root = root
        self.root.title('Satellite Tracker')
        self.root.config(bg='black')
        self.tooltip_window = None

        left_frame = tk.Frame(root, width=75, height=55, bg='white')
        left_frame.grid(row=0, column=0, padx=5, pady=5)

        right_frame = tk.Frame(root, width=105, height=55, bg='white')
        right_frame.grid(row=0, column=1, padx=5, pady=5)

        # address field
        self.address_label = ttk.Label(left_frame, text="Enter Your Address: ", width=18, background='white')
        self.address_label.grid(row=0, column=0, padx=3, pady=5, sticky='e')
        self.address_entry = ttk.Entry(left_frame, width=50)
        self.address_entry.grid(row=0, column=1, padx=5, pady=5)

        # satellite dropdown
        self.satellite_label = ttk.Label(left_frame, text='Select a Satellite: ', width=15, background='white')
        self.satellite_label.grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.options = business.MOST_POPULAR_SATELLITES
        self.sat_combo_box = ttk.Combobox(left_frame, state='readonly', width=30, values=self.options)
        self.sat_combo_box.grid(row=1, column=1, padx=5, pady=5)
        self.sat_combo_box.bind("<<ComboboxSelected>>", self.on_select)

        # search for satellite
        self.satellite_search_label = ttk.Label(left_frame, text="Or Search For Satellite Name: ", width=26,
                                                background='white')
        self.satellite_search_label.grid(row=2, column=0, padx=5, pady=5, sticky='e')
        self.satellite_sarch_entry = ttk.Entry(left_frame, width=33)
        self.satellite_sarch_entry.grid(row=2, column=1, padx=5, pady=5)
        self.satellite_sarch_entry.bind("<KeyRelease>", self.search_entry_used)

        # filter label & frame
        self.filter_label = ttk.Label(left_frame, text="Filter Results", background='white', justify=tk.CENTER,
                                      font=('Times New Roman', 12, 'bold'))
        self.filter_label.grid(row=3, column=0, columnspan=2, padx=1, pady=1)
        self.filter_frame = ttk.Frame(left_frame, width=50, borderwidth=5, relief='sunken')
        self.filter_frame.grid(row=4, rowspan=2, column=0, columnspan=2, padx=5, pady=5, ipady=5)

        # declare filter variables
        self.only_sunlit_ischecked = tk.IntVar()
        self.only_night_ischecked = tk.IntVar()
        self.only_clear_sky_ischecked = tk.IntVar()
        self.moon_warning_ischecked = tk.IntVar()
        self.add_forecast_ischecked = tk.IntVar()
        self.moon_filter_ischecked = tk.IntVar()
        self.add_sunlit_ischecked = tk.IntVar()

        # filter checkboxes
        self.only_sunlit_checkbox = ttk.Checkbutton(self.filter_frame, text="Sunlit Filter",
                                                    variable=self.only_sunlit_ischecked)
        self.only_sunlit_checkbox.grid(row=4, column=0, padx=5, pady=1)
        self.only_night_checkbox = ttk.Checkbutton(self.filter_frame, text="At Night Filter",
                                                   variable=self.only_night_ischecked)
        self.only_night_checkbox.grid(row=4, column=3, padx=5, pady=1)
        self.only_clear_sky_checkbox = ttk.Checkbutton(self.filter_frame, text="Clear Sky Filter",
                                                       variable=self.only_clear_sky_ischecked)
        self.only_clear_sky_checkbox.grid(row=4, column=2, padx=5, pady=1)
        self.filter_for_moon_checkbox = ttk.Checkbutton(self.filter_frame, text="Moonlight Filter",
                                                        variable=self.moon_filter_ischecked)
        self.filter_for_moon_checkbox.grid(row=4, column=1, padx=5, pady=1)
        self.moon_warning_checkbox = ttk.Checkbutton(self.filter_frame, text="Add Moon Warnings",
                                                     variable=self.moon_warning_ischecked)
        self.moon_warning_checkbox.grid(row=5, column=1, padx=5, pady=1)
        self.add_forecast_conditions_checkbox = ttk.Checkbutton(self.filter_frame, text='Add Forecasts',
                                                                variable=self.add_forecast_ischecked)
        self.add_forecast_conditions_checkbox.grid(row=5, column=2, padx=5, pady=1)
        self.add_sunlit_checkbox = ttk.Checkbutton(self.filter_frame, text='Add Sunlit',
                                                   variable=self.add_sunlit_ischecked)
        self.add_sunlit_checkbox.grid(row=5, column=0, padx=5, pady=1)

        # filter checkbox tooltips
        self.only_sunlit_checkbox.bind('<Enter>', self.sunlit_tooltip_show)
        self.only_sunlit_checkbox.bind('<Leave>', self.tooltip_hide)
        self.only_night_checkbox.bind('<Enter>', self.night_tooltip_show)
        self.only_night_checkbox.bind('<Leave>', self.tooltip_hide)
        self.only_clear_sky_checkbox.bind('<Enter>', self.clear_tooltip_show)
        self.only_clear_sky_checkbox.bind('<Leave>', self.tooltip_hide)
        self.moon_warning_checkbox.bind('<Enter>', self.moon_tooltip_show)
        self.moon_warning_checkbox.bind('<Leave>', self.tooltip_hide)
        self.add_forecast_conditions_checkbox.bind('<Enter>', self.forecast_tooltip_show)
        self.add_forecast_conditions_checkbox.bind('<Leave>', self.tooltip_hide)
        self.filter_for_moon_checkbox.bind('<Enter>', self.filter_moon_tooltip_show)
        self.filter_for_moon_checkbox.bind('<Leave>', self.tooltip_hide)
        self.add_sunlit_checkbox.bind('<Enter>', self.add_sunlit_tooltip_show)
        self.add_sunlit_checkbox.bind('<Leave>', self.tooltip_hide)

        # list all satellites button
        self.list_all_satellites_button = ttk.Button(left_frame, text='List All Satellites', width=20,
                                                     command=self.list_all_satellites)
        self.list_all_satellites_button.grid(row=6, column=0, columnspan=2, padx=5, pady=2, ipadx=2, sticky='w,e')

        # help file & export button
        self.help_file_button = ttk.Button(left_frame, text='Help', width=15, command=self.open_help_file)
        self.help_file_button.grid(row=7, column=0, columnspan=2, padx=5, pady=2, ipadx=2, sticky='w,e')
        self.export_button = ttk.Button(left_frame, text='Export', width=15, command=self.export_results,
                                        state='disabled')
        self.export_button.grid(row=8, column=0, columnspan=2, padx=5, pady=2, ipadx=2, sticky='w,e')

        # get results/clear buttons
        self.clear_button = ttk.Button(left_frame, text='Clear Form', width=15, command=self.clear_form)
        self.clear_button.grid(row=9, column=0, columnspan=2, padx=5, pady=2, ipadx=2, sticky='w,e')
        self.get_results_button = tk.Button(left_frame, text='Generate Events', width=15, bg='green',
                                            command=self.get_results_on_click)
        self.get_results_button.bind('<Enter>', self.get_results_color_change_enter)
        self.get_results_button.bind('<Leave>', self.get_results_color_change_leave)
        self.get_results_button.grid(row=11, column=0, columnspan=2, padx=5, pady=2, ipadx=2, sticky='w,e')

        # generate all optimal events button
        self.generate_all_optimal_button = ttk.Button(left_frame, text='Generate All Optimal Events', width=15,
                                                      command=self.generate_all_optimal_onclick)
        self.generate_all_optimal_button.grid(row=10, column=0, columnspan=2, padx=5, pady=2, ipadx=2, sticky='w,e')
        self.generate_all_optimal_button.bind('<Enter>', self.generate_all_optimal_tooltip)
        self.generate_all_optimal_button.bind('<Leave>', self.tooltip_hide)

        # results text - right side.
        self.resuts_label = tk.Label(right_frame, text="RESULTS", background='white', justify=tk.CENTER,
                                     font=('Times New Roman', 12, 'bold'))
        self.resuts_label.grid(row=0, column=0, padx=5)
        self.loading_label = tk.Label(right_frame, text="Status: Ready", background='white',
                                      justify=tk.CENTER)
        self.loading_label.grid(row=1, column=0, padx=5)
        self.results_text = tk.Text(right_frame, width=95, height=45, state='disabled')
        self.results_text.grid(row=2, column=0, padx=5, pady=5)

    def on_select(self, event):
        """
        when the satellite dropdown menu is used, if the satellite search bar has text in it, clears the search bar.
        :param event: combobox selected event
        :return: n/a
        """
        if self.satellite_sarch_entry.get() != "":
            self.satellite_sarch_entry.delete(0, tk.END)

    def clear_form(self):
        """
        resets the form to its load state
        :return: n/a
        """
        self.address_entry.delete(0, tk.END)
        self.sat_combo_box.set("")
        self.satellite_sarch_entry.delete(0, tk.END)
        self.only_sunlit_ischecked.set(0)
        self.only_night_ischecked.set(0)
        self.only_clear_sky_ischecked.set(0)
        self.moon_warning_ischecked.set(0)
        self.moon_filter_ischecked.set(0)
        self.add_forecast_ischecked.set(0)
        self.add_sunlit_ischecked.set(0)
        self.loading_label.config(text="Status: Ready")
        self.results_text.config(state='normal')
        self.results_text.delete(0.0, tk.END)
        self.results_text.config(state='disabled')
        self.get_results_button.config(state='normal')
        self.export_button.config(state='disabled')

    def get_results_on_click(self):
        """
        handles the click event for the 'Generate Results' button, starts the get_results thread.
        :return: n/a
        """
        self.results_text.config(state='normal')  # set state to normal so I can insert things
        self.results_text.delete(0.0, tk.END)
        self.loading_label.config(text="Status: Loading Results, may take 30+ seconds to compute satellite locations for all events.")
        self.results_text.config(state='disabled')
        thread = threading.Thread(target=self.get_results, args=(self.display_response,))
        thread.start()

    def get_results(self, callback):
        """
        handles the retrieval of specific satellite event data from elsewhere in the code
        :param callback: what to pass the results of this thread to
        :return: satellite event results
        """
        # disable the button so user cannot spam click
        self.disable_buttons()
        # grab the user's address
        address = self.address_entry.get()
        # check if it is blank
        if address == "":
            messagebox.showinfo('Error', "Address can not be blank!")
            self.loading_label.config(text="Status: Ready")
            self.enable_buttons()
            return
        # grab the forecast data so I can pass it to the filters.
        try:
            lat_lon = business.get_lat_long(address.strip())
            latitude = lat_lon[0]
            longitude = lat_lon[1]
        except BusinessLogicException:
            messagebox.showinfo('Error', 'Bad Address, please try again.')
            self.loading_label.config(text="Status: Ready")
            self.enable_buttons()
            return
        try:
            forecast = business.get_forecast_data(latitude, longitude)
        except BusinessLogicException:
            messagebox.showinfo('Error', 'Unable to retrieve forecast info.')
            self.loading_label.config(text="Status: Ready")
            self.enable_buttons()
            return
        selected_satellite = self.sat_combo_box.get()  # get the selected satellite
        if selected_satellite == '':
            selected_satellite = self.satellite_sarch_entry.get().upper().strip()
            # check if the satellite the user is searching for can be found
            sat_name_list = business.get_sat_names_list()
            if selected_satellite not in sat_name_list:
                messagebox.showinfo('Error', "Satellite not found.")
                self.loading_label.config(text="Status: Ready")
                self.enable_buttons()
                return
        try:
            sat_info = business.get_data_for_one_sat(selected_satellite, forecast, latitude, longitude)
        except BusinessLogicException:
            messagebox.showinfo('Error', "Could not retrieve satellite data. If problem persists, there is a database error.")
            self.loading_label.config(text="Status: Ready")
            self.enable_buttons()
            return
        if self.only_sunlit_ischecked.get() == 1:
            sat_info = filters.filter_only_sunlit_events(sat_info)
        if self.only_night_ischecked.get() == 1:
            sat_info = filters.filter_only_at_night(sat_info, forecast)
        if self.only_clear_sky_ischecked.get() == 1:
            sat_info = filters.filter_for_clouds(sat_info, forecast)
        if self.moon_warning_ischecked.get() == 1:
            sat_info = filters.set_moon_warnings(sat_info, forecast)
        if self.add_forecast_ischecked.get() == 1:
            sat_info = filters.add_conditions(sat_info, forecast)
        if self.moon_filter_ischecked.get() == 1:
            sat_info = filters.filter_for_moon(sat_info, forecast)
        if self.add_sunlit_ischecked.get() == 1:
            sat_info = filters.add_sunlit_to_events(sat_info)
        callback(sat_info, latitude, longitude)

    def display_response(self, response, latitude, longitude):
        """
        displays the results from get_results() thread to the results text.
        :param response: results from the get_results method
        :param latitude: user's latitude
        :param longitude: user's longitude
        :return: n/a, displays results to the results text
        """
        self.results_text.config(state='normal')  # set state to normal so I can insert things
        self.results_text.delete(0.0, tk.END)  # clear the text box so it's empty
        sat_info = response
        if len(sat_info) == 0:
            self.results_text.insert(tk.END, "No events in the next 7 days with the given filters")
            self.results_text.insert(tk.END, "\nIt is possible there are no events with no filters, dependent on your location")
        else:
            for item in sat_info:
                self.results_text.insert(tk.END, f"{item}\n")
                self.results_text.insert(tk.END, f"\t{item.return_satellite_location(latitude, longitude)}\n\n")
        self.loading_label.config(text="Status: Loading Complete (don't forget to scroll)")
        self.enable_buttons()
        self.results_text.config(state='disabled')

    def generate_all_optimal_onclick(self):
        """
        handles the click event for the generate all optimal events button, starts the generate_optimal thread.
        :return: n/a
        """
        self.results_text.config(state='normal')  # set state to normal so I can insert things
        self.results_text.delete(0.0, tk.END)
        self.loading_label.config(text="Status: Loading Results, may take 30+ seconds to compute satellite locations for all events.")
        self.results_text.config(state='disabled')
        # clear all this stuff because it does not matter for this button...
        self.sat_combo_box.set("")
        self.satellite_sarch_entry.delete(0, tk.END)
        self.only_sunlit_ischecked.set(0)
        self.only_night_ischecked.set(0)
        self.only_clear_sky_ischecked.set(0)
        self.moon_warning_ischecked.set(0)
        self.moon_filter_ischecked.set(0)
        self.add_forecast_ischecked.set(0)
        self.add_sunlit_ischecked.set(0)
        thread = threading.Thread(target=self.generate_optimal, args=(self.display_optimal,))
        thread.start()

    def generate_optimal(self, callback):
        """
        handles the retrieval & filtering of satellite event data for every satellite in the dropdown menu of the gui.
        :param callback: what to pass the results of this thread to
        :return: satellite event results
        """
        # disable the button so user cannot spam click
        self.disable_buttons()
        # grab the user's address
        address = self.address_entry.get()
        # check if it is blank
        if address == "":
            messagebox.showinfo('Error', "Address can not be blank!")
            self.loading_label.config(text="Status: Ready")
            self.enable_buttons()
            return
        try:
            # getting lat & long here saved a lot of api calls...
            lat_lon = business.get_lat_long(address.strip())
            latitude = lat_lon[0]
            longitude = lat_lon[1]
        except BusinessLogicException:
            messagebox.showinfo('Error', 'Bad Address, please try again.')
            self.loading_label.config(text="Status: Ready")
            self.enable_buttons()
            return
        # get forecast data
        try:
            forecast = business.get_forecast_data(latitude, longitude)
        except BusinessLogicException:
            messagebox.showinfo('Error', 'Unable to retrieve forecast info.')
            self.loading_label.config(text="Status: Ready")
            self.enable_buttons()
            return
        all_sats_from_dropdown_list = business.MOST_POPULAR_SATELLITES
        all_sat_info_list = []
        for a_satellite in all_sats_from_dropdown_list:
            try:
                sat_info = business.get_data_for_one_sat(a_satellite, forecast, latitude, longitude)
            except BusinessLogicException:
                messagebox.showinfo('Error',
                                    "Could not retrieve satellite data. If problem persists, there is a database error.")
                self.loading_label.config(text="Status: Ready")
                self.enable_buttons()
                return
            sat_info = filters.filter_only_sunlit_events(sat_info)
            sat_info = filters.filter_only_at_night(sat_info, forecast)
            sat_info = filters.filter_for_clouds(sat_info, forecast)
            sat_info = filters.set_moon_warnings(sat_info, forecast)
            all_sat_info_list.append(sat_info)
        callback(all_sat_info_list, latitude, longitude)

    def display_optimal(self, response, latitude, longitude):
        """
        displays the results from get_optimal() thread to the results text.
        :param response: results from the get_optimal method
        :param latitude: user's latitude
        :param longitude: user's longitude
        :return: n/a, displays results to the results text
        """
        self.results_text.config(state='normal')  # set state to normal so I can insert things
        self.results_text.delete(0.0, tk.END)  # clear the text box so it's empty
        sat_info_list = response
        sat_info_len = 0
        for item in sat_info_list:
            # it is possible for there to be results in some result lists, but not others, so I have to check them all.
            if len(item) > 0:
                sat_info_len += 1
        if sat_info_len == 0:
            self.results_text.insert(tk.END, "No events in the next 7 days with the given filters")
            self.results_text.insert(tk.END, "\nIt is possible there are no events with no filters, dependent on your location")
        else:
            for sat_info in sat_info_list:
                for item in sat_info:
                    self.results_text.insert(tk.END, f"{item}\n")
                    self.results_text.insert(tk.END, f"\t{item.return_satellite_location(latitude, longitude)}\n\n")
        self.loading_label.config(text="Status: Loading Complete (don't forget to scroll)")
        self.enable_buttons()
        self.results_text.config(state='disabled')

    def list_all_satellites(self):
        """
        lists every satellite name in satellites.db to the results text
        :return: n/a
        """
        sat_name_list = business.get_sat_names_list()
        self.results_text.config(state='normal')
        self.results_text.delete(0.0, tk.END)
        i = 0
        for item in sat_name_list:
            self.results_text.insert(tk.END, f"{item}, ")
            i += 1
            if i % 4 == 0:
                self.results_text.insert(tk.END, '\n')
        self.results_text.config(state='disabled')

    def open_help_file(self):
        """
        opens the help file when the 'help' button is clicked.
        :return: n/a
        """
        # probably should have just printed this information to the results text, eh?
        os.startfile('help_file.txt')

    def export_results(self):
        """
         passes the contents of the results text to a method which will export them to results_export.txt
        :return: n/a
        """
        results = self.results_text.get(0.0, tk.END)
        if len(results) < 20:  # I chose 20 arbitrarily, for some reason if results == "" did not work here, even
            # if the results text was cleared immediately before.
            # I suspect a newline character or something, but I don't know...
            messagebox.showinfo('Error', 'Will not export with no results')
            return
        try:
            business.write_results_to_txt(results)
            messagebox.showinfo('Success', 'Data Exported to results_export.txt')
        except BusinessLogicException:
            messagebox.showinfo('Error', 'Unable export data.')

    def on_load(self):
        """
        handles displaying some message to the results text when the form is first loaded.
        :return: n/a
        """
        self.results_text.config(state='normal')
        self.results_text.insert(tk.END, "Welcome!\nIf this is your first time using the program, please see the help file (click help)")
        self.results_text.config(state='disabled')

    def search_entry_used(self, event):
        """
        if the search entry is used, clears anything that might be selected in the satellite dropdown.
        :param event: the 'keyup' event from the satellite search entry
        :return: n/a
        """
        self.sat_combo_box.set("")

    def sunlit_tooltip_show(self, event):
        """
        shows the tooltip for the sunlit filter checkbox
        :param event: the mouseover event for this checkbox
        :return: n/a
        """
        self.tooltip_window = tk.Toplevel()
        # I cannot seem to pass this a text variable and reuse the same function for all tooltip events... If I add a
        # text variable & pass it, it says missing event variable.
        tooltip_label = tk.Label(self.tooltip_window,
                                 text="only display events where the SATELLITE (NOT YOU) is illuminated by the sun")
        tooltip_label.pack()
        self.tooltip_window.overrideredirect(True)
        x = self.root.winfo_pointerx() + 7
        y = self.root.winfo_pointery() + 7
        self.tooltip_window.geometry(f"+{x}+{y}")

    def night_tooltip_show(self, event):
        """
        shows the tooltip for the only night filter checkbox
        :param event: the mouseover event for this checkbox
        :return: n/a
        """
        self.tooltip_window = tk.Toplevel()
        tooltip_label = tk.Label(self.tooltip_window,
                                 text="only display events that happen at night")
        tooltip_label.pack()
        self.tooltip_window.overrideredirect(True)
        x = self.root.winfo_pointerx() + 7
        y = self.root.winfo_pointery() + 7
        self.tooltip_window.geometry(f"+{x}+{y}")

    def clear_tooltip_show(self, event):
        """
        shows the tooltip for the only clear skies filter checkbox
        :param event: the mouseover event for this checkbox
        :return: n/a
        """
        self.tooltip_window = tk.Toplevel()
        tooltip_label = tk.Label(self.tooltip_window,
                                 text="only display events that happen during clear skies")
        tooltip_label.pack()
        self.tooltip_window.overrideredirect(True)
        x = self.root.winfo_pointerx() + 7
        y = self.root.winfo_pointery() + 7
        self.tooltip_window.geometry(f"+{x}+{y}")

    def moon_tooltip_show(self, event):
        """
        shows the tooltip for the add moon warnings checkbox
        :param event: the mouseover event for this checkbox
        :return: n/a
        """
        self.tooltip_window = tk.Toplevel()
        tooltip_label = tk.Label(self.tooltip_window,
                                 text="attaches a warning if the moon is visible and more than 50% full")
        tooltip_label.pack()
        self.tooltip_window.overrideredirect(True)
        x = self.root.winfo_pointerx() + 7
        y = self.root.winfo_pointery() + 7
        self.tooltip_window.geometry(f"+{x}+{y}")

    def forecast_tooltip_show(self, event):
        """
        shows the tooltip for the add forecast checkbox
        :param event: the mouseover event for this checkbox
        :return: n/a
        """
        self.tooltip_window = tk.Toplevel()
        tooltip_label = tk.Label(self.tooltip_window,
                                 text="adds hourly forecast for each event (clear, cloudy, etc.)")
        tooltip_label.pack()
        self.tooltip_window.overrideredirect(True)
        x = self.root.winfo_pointerx() + 7
        y = self.root.winfo_pointery() + 7
        self.tooltip_window.geometry(f"+{x}+{y}")

    def filter_moon_tooltip_show(self, event):
        """
        shows the tooltip for the moon filter checkbox
        :param event: the mouseover event for this checkbox
        :return: n/a
        """
        self.tooltip_window = tk.Toplevel()
        tooltip_label = tk.Label(self.tooltip_window,
                                 text="filters out events where the moon is brighter than 50% & in the sky")
        tooltip_label.pack()
        self.tooltip_window.overrideredirect(True)
        x = self.root.winfo_pointerx() + 7
        y = self.root.winfo_pointery() + 7
        self.tooltip_window.geometry(f"+{x}+{y}")

    def add_sunlit_tooltip_show(self, event):
        """
        shows the tooltip for the add sunlit checkbox
        :param event: the mouseover event for this checkbox
        :return: n/a
        """
        self.tooltip_window = tk.Toplevel()
        tooltip_label = tk.Label(self.tooltip_window,
                                 text="adds to output whether the SATELLITE (NOT YOU) is in sunlight.")
        tooltip_label.pack()
        self.tooltip_window.overrideredirect(True)
        x = self.root.winfo_pointerx() + 7
        y = self.root.winfo_pointery() + 7
        self.tooltip_window.geometry(f"+{x}+{y}")

    def generate_all_optimal_tooltip(self, event):
        """
        shows the tooltip for the generate optimal events button
        :param event: the mouseover event for this button
        :return: n/a
        """
        self.tooltip_window = tk.Toplevel()
        tooltip_label = tk.Label(self.tooltip_window,
                                 text="Lists all optimal events for every satellite from the dropdown menu")
        tooltip_label.pack()
        self.tooltip_window.overrideredirect(True)
        x = self.root.winfo_pointerx() + 7
        y = self.root.winfo_pointery() + 7
        self.tooltip_window.geometry(f"+{x}+{y}")

    def get_results_color_change_enter(self, event):
        """
        changes the color of the get results button on mouseover
        :param event: the mouseover event for this button
        :return: n/a
        """
        self.get_results_button.config(bg='blue')

    def get_results_color_change_leave(self, event):
        """
        changes the color of the get results button back after mouseover
        :param event: the mouseover event for this button
        :return: n/a
        """
        self.get_results_button.config(bg='green')

    def tooltip_hide(self, event):
        """
        hides any tooltip that is currently displayed.
        :param event: mouseover event
        :return: n/a
        """
        self.tooltip_window.destroy()
        self.tooltip_window = None

    def disable_buttons(self):
        """
        disables the buttons (for while the form is loading results)
        :return: n/a
        """
        self.list_all_satellites_button.config(state='disabled')
        self.help_file_button.config(state='disabled')
        self.export_button.config(state='disabled')
        self.generate_all_optimal_button.config(state='disabled')
        self.get_results_button.config(state='disabled')

    def enable_buttons(self):
        """
        enables buttons (for when result loading is done)
        :return: n/a
        """
        self.list_all_satellites_button.config(state='normal')
        self.help_file_button.config(state='normal')
        self.export_button.config(state='normal')
        self.generate_all_optimal_button.config(state='normal')
        self.get_results_button.config(state='normal')

