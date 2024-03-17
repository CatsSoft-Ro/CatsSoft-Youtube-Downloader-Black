#-------------------------------------------------------------------------------
# Name:        CatsSoft Youtube Downloader
# Purpose:
#
# Author:      Andruska
#
# Created:     29.12.2023
# Copyright:   (c) Andruska 2023
# Licence:     GNU
#-------------------------------------------------------------------------------

import tkinter as tk
import customtkinter as ctk
import customtkinter
from tkVideoPlayer import TkinterVideo
from tkinter import Tk, Frame, Entry, Toplevel, Button, Canvas, Label, Listbox, Scrollbar, RIGHT, Y, END, Menu, PhotoImage, filedialog, ttk, messagebox, N, S, E, W
from tkinter.messagebox import showinfo
from unidecode import unidecode
import unidecode as ud
from youtube_search import YoutubeSearch
from youtubesearchpython import VideosSearch
import youtube_websearch as yt
from PIL import Image, ImageTk
from pytube import Playlist, YouTube, Search
from pytube.exceptions import VideoUnavailable, RegexMatchError
import moviepy.editor as mp
from moviepy.editor import VideoFileClip
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_audio
from customtkinter import CTkEntry, CTkButton, CTkLabel, CTkImage, CTkComboBox, CTk
from customtkinter import *
import tkinter.ttk as ttk  # Import the ttk module
from urllib.parse import urlparse, parse_qs
import pyperclip
import io
import requests
import shutil
import getpass
import sys
import os
import re
import threading
import time
import math
import webbrowser

# Inițializare variabilă start_time
start_time = 0

# La începutul programului, setează output_path
username = getpass.getuser()
output_path = os.path.join("C:\\Users", username, "Videos")
# Acum, output_path ar trebui să conțină calea dorită cu numele de utilizator inclus
print(output_path)

# Initialize app

class GUI:
    def __init__(app, root=None):

        GUI.center(app.root)

# Definiți variabilele înainte de a utiliza app.after
chunk = 0   # Definiți chunk aici
bytes_remaining = 0  # Definiți bytes_remaining aici
filesize = 0
# Define download_speed as a global variable
download_speed = None

# Get video id
def get_video_id():
    ytLink = link.get()
    print(f"ytLink: {ytLink}")

    if not isinstance(ytLink, (str, bytes)):
        raise TypeError("Expected string or bytes-like object.")

    # Use re.search instead of regex_search
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", ytLink)

    if match:
        return match.group(1)

    raise ValueError(f"regex_search: could not find match for {ytLink}.")

# Inițializare
ytObject = None  # Asigură-te că ai definit variabila globală ytObject înainte
username = getpass.getuser()
output_path = os.path.join("C:\\Users", username, "Videos")

def start_download():
    global start_time, ytObject  # Referință la variabilele globale
    ytLink = link.get()
    qualidade = options.get()
    atualizar_thumb()

    try:
        output_path = output_entry.get()

        if not ytLink or not output_path:
            messagebox.showerror("Error", "Please enter both URL and output path.")
            return

        # Mută atribuirea start_time în afara blocului if
        start_time = time.time()  # Actualizează timpul de start
        ytObject = YouTube(ytLink, on_progress_callback=on_progress)
        video_title = ytObject.title  # Salvează titlul într-o variabilă

        if qualidade == "Only Audio (mp3)":
            audio = ytObject.streams.filter(only_audio=True).first()

            # Înlocuiește caracterele non-ASCII din titlu
            video_title = video_title.encode('ascii', 'ignore').decode()

            if not video_title:
                print("Error: Video title is not available.")
                return

            # Înlocuiește caracterele invalide și reduce spațiile la unul
            filename = re.sub(r'[\\/:"*?<>|]', '', video_title.replace(' ', ' '))

            audio_file_path = os.path.join(output_path, f"{filename}.mp3")
            audio.download(output_path)
            messagebox.showinfo("Download Complete", "The audio has been downloaded successfully!")
            open_output_directory(output_path)

        elif qualidade in ["2160p", "1440p", "1080p", "720p", "480p", "360p", "240p"]:
            found_stream = None

            # Filtrare directă a stream-urilor pe baza rezoluției dorite
            filtered_streams = ytObject.streams.filter(video_codec="vp9", res=qualidade, file_extension="mp4", adaptive=True, progressive=True)

            if filtered_streams:
                found_stream = filtered_streams.first()
            else:
                # Dacă nu a găsit un stream cu rezoluția dorită, alege stream-ul cu cea mai mare rezoluție disponibilă
                found_stream = ytObject.streams.filter(file_extension="mp4", progressive=True).get_highest_resolution()

            if found_stream is not None:
                video_title = ytObject.title
                video_title = video_title.encode('ascii', 'ignore').decode()

                if not video_title:
                    print("Error: Video title is not available.")
                    return

                # Înlocuiește caracterele invalide și reduce spațiile la unul
                filename = re.sub(r'[\\/:"*?<>|]', '', video_title.replace(' ', ' '))

                video_file_path = os.path.join(output_path, f"{filename}.mp4")
                found_stream.download(output_path)
                messagebox.showinfo("Download Complete", f"The {qualidade} video has been downloaded successfully!")
                open_output_directory(output_path)
            else:
                print(f"No video stream found with the specified resolution: {qualidade}")

                # Dacă nu a găsit un stream cu rezoluția dorită, afișează toate stream-urile disponibile
                print("Available streams:")
                for stream in ytObject.streams.filter(file_extension="mp4", progressive=True):
                    print(stream)

                messagebox.showerror("Download Error", f"No video stream found with the specified resolution: {qualidade}")

    except Exception as e:
        messagebox.showerror("Error", f"Download Error!: {str(e)}")

# Definiți variabilele înainte de a utiliza app.after

def on_progress(stream, chunk, bytes_remaining):
    global download_speed
    total_size = stream.filesize
    bytes_download = total_size - bytes_remaining
    percentage_of_completion = bytes_download / total_size * 100
    per = str(int(percentage_of_completion))
    pPercentage.configure(text=per + "%")
    pPercentage.update()

    # Actualizează ambele bare de progres
    progressBar.set(float(percentage_of_completion / 100))

    # Actualizează viteza de descărcare
    download_speed = calculate_download_speed(stream, chunk)
    download_speed_label.configure(text=f"Viteza de descărcare: {download_speed}")

    # Începe verificarea progresului într-un fir de execuție separat
    progress_check_thread(ytObject, stream, chunk, bytes_remaining, download_speed)

def progress_check_thread(ytObject, stream, chunk, bytes_remaining, download_speed):
    # Create a thread to check the progress of the download
    multi_thread_progress_check = threading.Thread(target=progress_check, args=(ytObject, stream, chunk, bytes_remaining, download_speed))
    multi_thread_progress_check.start()

def progress_check(ytObject, stream, chunk, bytes_remaining, download_speed):
    if ytObject:
        # Calculate the progress of the download
        download_progress_int = stream.filesize - bytes_remaining
        download_progress_percentage = int(download_progress_int / stream.filesize * 100)
        download_progress_mb = round(download_progress_int / 1048576, 2)
        download_file_size_mb = round(stream.filesize / 1048576, 2)
        download_speed_label.configure(text=f"Download Speed: {download_speed} Status: {download_progress_percentage}% {download_progress_mb}MB/{download_file_size_mb}MB | {ytObject.title}")

def calculate_download_speed(stream, chunk):
    # Convertește chunk la număr întreg
    chunk_size = len(chunk)

    # Utilizează momentul actual și momentul la care a început descărcarea
    bytes_per_second = chunk_size / (time.time() - start_time)
    return f"{convert_size(bytes_per_second)}/s"

def convert_size(size_bytes):
    if size_bytes == 0:
        return "0 B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"

# Paste link

def paste_link():
    try:
        app.clipboard_content = app.clipboard_get()
        if app.clipboard_content and app.clipboard_content.startswith("https"):
            link.delete(0, tk.END)
            link.insert(0, app.clipboard_content)
    except tk.TclError as e:
        # Gestionați excepția dacă nu puteți obține conținutul din clipboard
        print(f"Error getting clipboard content: {e}")
        # Afișați un mesaj de avertizare sau luați alte măsuri necesare

# Change buton event

def on_hover(event):
    download_label.configure(bg="#000000", fg="white")

def on_leave(event):
    download_label.configure(bg="#000000", fg="#414042")

# System Settings
customtkinter.set_appearance_mode("dark")  # Modes: system (default), light, dark
customtkinter.set_default_color_theme("black")  # Themes: blue (default), dark-blue, green

def setup_interface(app):
    frame = Frame(app)
    frame.pack()

    # Configurare dimensiuni și poziționare fereastră
    window_height = 690
    window_width = 1220
    x_position = (app.winfo_screenwidth() // 2) - (window_width // 2)
    y_position = (app.winfo_screenheight() // 4) - (window_height // 4)
    app.geometry('{}x{}+{}+{}'.format(window_width, window_height, x_position, y_position))
    app.resizable(width=False, height=False)
    app.config(background="#000000")

def load_images():
    # Încărcare imagini și iconi
    img_vid = Image.open(get_image_path("images/thumb.png"))
    app_icon_path = get_image_path("images/app.ico")
    app.iconbitmap(app_icon_path)

    # Încărcare imagine de fundal
    background_image = Image.open(get_image_path("images/background_image_dark.jpg"))
    background_image = background_image.resize((app.winfo_screenwidth(), app.winfo_screenheight()), Image.LANCZOS)
    background_photo = ImageTk.PhotoImage(background_image)
    app.background_photo = background_photo  # Menține referința globală la imagine

def get_image_path(filename):
    import os
    import sys
    from os import chdir
    from os.path import join
    from os.path import dirname
    from os import environ

    if hasattr(sys, '_MEIPASS'):
        # PyInstaller >= 1.6
        chdir(sys._MEIPASS)
        filename = join(sys._MEIPASS, filename)
    elif '_MEIPASS2' in environ:
        # PyInstaller < 1.6 (tested on 1.5 only)
        chdir(environ['_MEIPASS2'])
        filename = join(environ['_MEIPASS2'], filename)
    else:
        chdir(dirname(sys.argv[0]))
        filename = join(dirname(sys.argv[0]), filename)

    return filename

# Aplicație principală
app = customtkinter.CTk()  # create a Tk window
app.title("YouTube Downloader")

# Configurare interfață și încărcare imagini
setup_interface(app)
load_images()

# Creare etichetă pentru imaginea de fundal
background_label = tk.Label(app, image=app.background_photo)
background_label.place(x=0, y=0, relwidth=1, relheight=1)

# Interface
titulo_vid = ("Your video title will appear here.")

# BackGround

# Adaugă o imagine de fundal
background_image = Image.open(get_image_path("images/background_image_dark.jpg"))
background_image = background_image.resize((app.winfo_screenwidth(), app.winfo_screenheight()), Image.LANCZOS)
background_photo = ImageTk.PhotoImage(background_image)
app.background_photo = background_photo  # Menține referința globală la imagine

# Creează un label cu imaginea de fundal
background_label = tk.Label(app, image=app.background_photo)
background_label.place(x=0, y=0, relwidth=1, relheight=1)

# Font
my_font = customtkinter.CTkFont(family="sans-serif", size=12)

# Adding UI Elements
title = customtkinter.CTkLabel(app, width=200, height=12, text="Insert a YouTube link", font=my_font, text_color="#F2F2F2", fg_color="#000000")
title.place(relx=0.20, rely=0.13, anchor="center")

# Link input
url_var = tk.StringVar()
link = customtkinter.CTkEntry(app, width=300, height=45, fg_color="#414042", border_color="#414042", text_color="#F2F2F2", corner_radius=8, font=customtkinter.CTkFont(family="sans-serif", size=16), textvariable=url_var)
link.place(relx=0.20, rely=0.20, anchor="center")

# Paste Link button
paste_button = customtkinter.CTkButton(app, width=300, height=46, text="Paste Link", text_color="#F2F2F2", command=paste_link)
paste_button.place(relx=0.20, rely=0.30, anchor="center")  # Adjust the relx and rely values

# Change resolution

options = CTkComboBox(app, values=["240p","360p","480p","720p","1080p","1440p", "2160p","Only Audio (mp3)"],
                      width=300,height=51,
                      bg_color="#000000",
                      fg_color="#414042",
                      text_color="#F2F2F2", corner_radius=15, button_color="#414042",
                      border_color="#414042",
                      )
options.place(relx=0.20, rely=0.4, anchor="center")

# Finished Downloading
# finishLable = customtkinter.CTkLabel(app, text="")
# finishLable.place(relx=0.68, rely=0.4, anchor="center")

# Progress percentage
pPercentage = customtkinter.CTkLabel(app, text="0%", width=50, height=12, text_color="#F2F2F2", fg_color="#000000")
pPercentage.place(relx=0.920, rely=0.57, anchor="center")

# Progressbar
progressBar = customtkinter.CTkProgressBar(app, width=950, height=8, fg_color="#1A1A1A")
progressBar.set(0)
progressBar.place(relx=0.48, rely=0.57, anchor="center")

# Încărcați imaginea butonului rotund
img = Image.open(get_image_path("images/button_download.png"))  # Înlocuiți cu calea către imaginea dvs.
img = img.resize((208, 208), Image.LANCZOS)  # Redimensionați imaginea la dimensiunea dorită
img = ImageTk.PhotoImage(img)

# Creați un buton rotund cu imagine
round_button = tk.Button(app, image=img, command=start_download, bd=0, bg="#000000", activebackground="#000000", cursor="hand2")
round_button.image = img  # Mențineți referința globală la imagine

# Plasați butonul rotund în partea de jos a ferestrei
round_button.place(relx=0.5, rely=0.86, anchor="center")

# Adăugați textul "Download" peste imaginea butonului
download_label = tk.Label(app, text="Download", font=("sans-serif", 14), bg="#000000", fg="#F2F2F2")
download_label.place(relx=0.5, rely=0.86, anchor="center")

# Atașați funcțiile de eveniment la eticheta de descărcare
download_label.bind("<Enter>", on_hover)
download_label.bind("<Leave>", on_leave)

# Încărcare imagini
img_vid = Image.open(get_image_path("images/thumb.png"))

# Thumbnail
thumb_interface = CTkImage(dark_image=img_vid, size=(416, 230))
thumb_label = CTkLabel(app, text=None, image=thumb_interface, anchor="s")
thumb_label.place(relx=0.72, rely=0.30, anchor="center")

thumb_texto = CTkLabel(app, text=titulo_vid, font=("Arial", 11), text_color="#F2F2F2", width=600, height=12, fg_color="#000000")
thumb_texto.place(relx=0.50, rely=0.53, anchor="center")

# Actualiser Thumbnall
def atualizar_thumb():
    ytLink = link.get()

    try:
        yt = YouTube(ytLink)
        thumb = yt.thumbnail_url

        img_vid2 = Image.open(requests.get(thumb, stream=True).raw)
        thumb_interface.configure(dark_image=img_vid2)
        titulo_vid = yt.title
        thumb_texto.configure(text=titulo_vid)

    except Exception as e:
        print("Erro", f"An error occurred while updating the thumbnail: {str(e)}")

# Placeholder for missing variables
# link = None
play_button = None
pause_button = None
stop_button = None

# Video Player
video_frame = Canvas(app, bg="#1A1A1A", highlightthickness=0, bd=0, relief="ridge")
video_frame.pack(expand=True, fill="both", padx=20, pady=20)
video_frame.pack_forget()

# Definition of global videoplayer and progress_slider
videoplayer = None
progress_slider = None

def is_youtube(url):
    parse_url = urlparse(url)
    if parse_url.hostname == 'youtu.be' or parse_url.hostname in ('www.youtube.com', 'youtube.com'):
        return True
    return False

def center_window(window, width=800, height=600):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width/2) - (width/2)
    y = (screen_height/2) - (height/2)
    window.geometry('%dx%d+%d+%d' % (width, height, x, y))

def play_youtube_video():
    global videoplayer, progress_slider, link, play_button, pause_button, stop_button

    # Creați fereastra pop-up
    popup = CTkToplevel()
    popup.protocol('WM_DELETE_WINDOW', popup.destroy)
    popup.configure(bg="#1A1A1A")
    popup.title("Play Youtube...")
    popup.attributes("-topmost", True)
    popup.geometry("800x600")

    # Complex widgets that have many components require time to instantiate correctly
    popup.update_idletasks()

    # Widgets can be bound to keyboard or mouse inputs
    popup.bind("<Escape>", closer)

    # Setați iconița pentru fereastra pop-up
    popup_icon_path = get_image_path("images/app.ico")
    try:
        popup.iconbitmap(popup_icon_path)
    except tk.TclError:
        # Gestionați eroarea dacă nu puteți încărca iconița
        print("Iconița nu a putut fi încărcată.")

    # Centrează fereastra pop-up
    center_window(popup)

    # Creați frame-ul pentru video
    video_frame = tk.Frame(popup, bg="#1A1A1A")
    video_frame.pack(expand=True, fill="both", padx=20, pady=20)

    ytLink = link.get()

    if not is_youtube(ytLink):
        print("Error: The provided link is not a valid YouTube link.")
        return

    try:
        yt = YouTube(ytLink)
        video = yt.streams.get_highest_resolution()
    except Exception as e:
        print(f"Error getting video from YouTube: {str(e)}")
        return

    if video is None:
        print("Error: No video stream available for the specified resolution.")
        return

    video_url = video.url

    videoplayer = TkinterVideo(master=video_frame, scaled=True, keep_aspect=True, consistant_frame_rate=True)
    videoplayer.set_resampling_method(1)
    videoplayer.set_size(size=(1080, 740))
    videoplayer.pack(expand=True, fill="both")

    videoplayer.bind("<<Duration>>", update_duration)
    videoplayer.bind("<<SecondChanged>>", update_scale)
    videoplayer.bind("<<Ended>>", video_ended)

    # Create progress_slider here and make it global
    progress_slider = customtkinter.CTkSlider(video_frame, from_=-1, to=1, number_of_steps=1, command=seek)
    progress_slider.set(-1)
    progress_slider.pack(fill="both", padx=10, pady=10)

    try:
        videoplayer.load(video_url)
        videoplayer.play()
        progress_slider.set(-1)
        play_button.configure(text="Play ►")
        pause_button.configure(text="Pause ||")

    except Exception as e:
        print(f"Error playing video: {str(e)}")

def closer(event):
    popup.destroy()

def update_duration(event):
    try:
        duration = int(videoplayer.video_info()["duration"])
        progress_slider.configure(from_=-1, to=duration, number_of_steps=duration)
    except:
        pass

def seek(value):
    if videoplayer:
        try:
            videoplayer.seek(int(value))
            videoplayer.play()
            videoplayer.after(50, videoplayer.pause)
            play_button.configure(text="Play ►")
        except:
            pass

def update_scale(event):
    try:
        progress_slider.set(int(videoplayer.current_duration()))
    except:
        pass

def video_ended(event):
    # Resetează textul butoanelor la starea inițială
    play_button.configure(text="Play")
    pause_button.configure(text="Pause")

    # Actualizează bara de progres după ce videoclipul s-a încheiat
    progress_slider.set(-1)

def play_pause():
    global videoplayer, play_button, pause_button

    if videoplayer:
        if videoplayer.is_paused():
            videoplayer.play()
            pause_button.configure(text="Pause ||")
            play_button.configure(text="Play ►")

        else:
            videoplayer.pause()
            play_button.configure(text="Play")
            pause_button.configure(text="Pause")

def stop_video():
    global videoplayer, play_button, pause_button

    try:
        if videoplayer is not None:
            videoplayer.stop()
            videoplayer.destroy()

            # Check if _container is not None before trying to close it
            if app._container is not None:
                app._container.close()

            play_button.configure(text="Play")
            pause_button.configure(text="Pause")

            # Check if there is a popup associated and destroy it
            if hasattr(videoplayer, '_popup') and videoplayer._popup is not None:
                videoplayer._popup.destroy()
    except Exception as e:
        print(f"An error occurred: {e}")

def on_play_button_click():
    play_youtube_video()

def update_volume(event):
    global videoplayer, volume_slider

    try:
        videoplayer.set_volume(float(volume_slider.get()))
    except:
        pass
volume_slider = customtkinter.CTkSlider(video_frame, from_=0, to=100, number_of_steps=100, command=update_volume)
volume_slider.set(50)
volume_slider.pack(fill="both", padx=10, pady=10)

play_button = customtkinter.CTkButton(app, width=10, height=10, text="Play", text_color="#F2F2F2", font=("Helvetica", 10, "normal"), command=on_play_button_click)
play_button.place(relx=0.820, rely=0.70, anchor="center")

pause_button = customtkinter.CTkButton(app, width=10, height=10, text="Pause", text_color="#F2F2F2", font=("Helvetica", 10, "normal"), command=play_pause)
pause_button.place(relx=0.870, rely=0.70, anchor="center")

stop_button = customtkinter.CTkButton(app, width=10, height=10, text="Stop", text_color="#F2F2F2", font=("Helvetica", 10, "normal"), command=stop_video)
stop_button.place(relx=0.920, rely=0.70, anchor="center")

# Download speed
download_speed_label = customtkinter.CTkLabel(app, text="", font=("Arial",11), text_color="#F2F2F2", width=600, height=12, fg_color="#000000")
download_speed_label.place(relx=0.50, rely=0.62, anchor="center")

# search_frame = customtkinter.CTkFrame(app, bg_color="#1A1A1A")
# search_frame.pack(side="top", anchor="ne", padx=10, pady=10)
# search_frame.pack_forget()

# Declare global variables
results_frame = None
canvas = None

results_frame = Canvas(app, bg="#000000", bd=0, highlightthickness=0)
results_frame.pack(expand=True, fill="both", padx=20, pady=20)
results_frame.pack_forget()

# Declare global variables
results_frame = None
canvas = None

results_thumbnails = []
results_links = []

def handle_left_click(event):
  index = (event.widget.find_closest(event.x, event.y)[0] - 1) // 2

  if index < len(results_links):
    link = results_links[index]
    # Copy the link to the clipboard
    copy_to_clipboard(link)
    print(f"Link copied to clipboard: {link}")

def show_context_menu(event):
    x, y = event.x, event.y
    item = results_frame.find_closest(x, y)

    if item:
        selected_thumbnail_index = (item[0] - 1) // 2
        menu = Menu(app, tearoff=0)
        menu.add_command(label="Copy Link", command=lambda index=selected_thumbnail_index: copy_selected_link_context(index))
        menu.post(event.x_root, event.y_root)

def copy_selected_link_context(index):
    link = results_links[index]
    app.clipboard_clear()
    app.clipboard_append(link)
    app.update()
    print(f"Link copied to clipboard: {link}")

def copy_to_clipboard(index):
    if 0 <= index < len(results_links):
        link = results_links[index]
        app.clipboard_clear()
        app.clipboard_append(link)
        app.update()
        print(f"Link copied to clipboard: {link}")
    else:
        print(f"Invalid index: {index}")

def popup_center(window, width=1200, height=620):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width/2) - (width/2)
    y = (screen_height/2) - (height/2)
    window.geometry('%dx%d+%d+%d' % (width, height, x, y))

# Declare a global variable for the cache
youtube_cache = {}
results = []

def search_videos():
    global results_links, results_frame, results_thumbnails, canvas, results_frame_inside, popup

    query = unidecode(search_input.get())

    # Check the cache for the results
    results = youtube_cache.get(query)

    # If the results are not in the cache, fetch them from YouTube
    if not results:
        results = YoutubeSearch(query, max_results=None).to_dict()
        youtube_cache[query] = results

    print(results)

    # Clear the results
    results_links = []
    results_thumbnails = []

    # Create the pop-up window
    popup = customtkinter.CTkToplevel(app)
    popup.protocol('WM_DELETE_WINDOW', popup.destroy)
    popup.configure(bg="#000000")
    popup.title("Search Youtube...")
    popup.attributes("-topmost", True)
    popup.geometry("1200x620")

    # Widgets can be bound to keyboard or mouse inputs
    popup.bind("<Escape>", close)

    # Set the icon for the pop-up window
    popup_icon_path = get_image_path("images/app.ico")
    try:
        popup.iconbitmap(popup_icon_path)
    except tk.TclError:
        print("Icon could not be loaded.")

    # Center the pop-up window
    popup_center(popup)

    # Load the background image
    img = Image.open(get_image_path("images/background_search_black.jpg"))
    img = img.resize((1200, 620), Image.LANCZOS)
    background_image = ImageTk.PhotoImage(img)

    # Display the background image in a Label
    background_label = customtkinter.CTkLabel(popup, image=background_image)
    background_label.place(relwidth=1, relheight=1)

    # Create a Frame inside the Canvas
    results_frame = Frame(popup, bg="#000000", bd=0, highlightthickness=0)
    results_frame.pack(side="top", fill="both", expand=True)

    # Create the Canvas for search results
    canvas = tk.Canvas(results_frame, bg="#000000", bd=0, highlightthickness=0)
    canvas.pack(side="left", fill="both", expand=True)

    # Add a vertical scrollbar to the Canvas
    vscrollbar = customtkinter.CTkScrollbar(popup, orientation="vertical", command=canvas.yview)
    vscrollbar.pack(side="right", fill="y")
    canvas.configure(yscrollcommand=vscrollbar.set)

    # Color the vertical scrollbar in blue
    vscrollbar._canvas.configure(bg="#0000FF")

    # Add context menu for each thumbnail
    results_frame.bind("<Button-3>", show_context_menu)
    results_frame.bind("<Button-1>", handle_left_click)

    # Create a Frame inside the Canvas
    results_frame_inside = Frame(canvas, bg="#1A1A1A", bd=0, highlightthickness=0)
    canvas.create_window((0, 0), window=results_frame_inside, anchor='nw')

    # Bind the mouse wheel event to the scrollbar function
    if canvas:
        canvas.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(int(-1 * (event.delta / 120)), "units") if canvas.winfo_exists() else None)

    row = 0
    col = 0
    thumbnail_width = 120
    thumbnail_height = 90
    num_columns = 3  # Set the number of columns

    # Declare thumbnail_frame before the loop
    thumbnail_frame = None

    # Check if results is not empty
    if results:
        # Iterate over the results
        for index, result in enumerate(results, 1):
            # Inside the loop
            print(f"Processing result {index}")
            thumbnail_url = result.get('thumbnails', [])[0]
            print(f"Thumbnail URL: {thumbnail_url}")
            thumbnail_image = get_thumbnail_image(thumbnail_url)

            if thumbnail_image:
                thumbnail_frame, thumbnail_label = create_thumbnail(result, thumbnail_image, index, row, col)

                title_label = customtkinter.CTkLabel(results_frame_inside, text=result['title'], font=("Helvetica", 10),
                                                     text_color="white", fg_color="#000000")
                title_label.grid(row=row + 1, column=col, padx=5, pady=5, sticky="nsew")

                # Append the link to the results_links list
                results_links.append(f"https://www.youtube.com/watch?v={result['id']}")

                # After the loop
                print("Results Links:", results_links)

                # Bind a click event to the thumbnail
                # thumbnail_label.bind("<Button-1>", lambda event, clicked_index=index-1: open_link(clicked_index))
                thumbnail_label.bind("<Button-1>", lambda event, clicked_index=index-1: open_link(int(clicked_index)))

                # Add the context menu
                bind_context_menu(thumbnail_label, index, popup)

                col += 1
                if col == num_columns:
                    col = 0
                    row += 2

        # Resize the canvas to fit the content
        canvas.config(width=num_columns * thumbnail_width + 2 * thumbnail_frame.winfo_width(),
                      height=row * thumbnail_height + 2 * thumbnail_frame.winfo_height())

        # Update the results frame
        results_frame_inside.update_idletasks()
        canvas.config(scrollregion=canvas.bbox('all'))

def create_thumbnail(result, thumbnail_image, i, row, col):
    global results_frame_inside  # Ensure it's declared as a global variable
    thumbnail_width, thumbnail_height = 120, 90

    # Resize thumbnail image
    thumbnail_image = thumbnail_image.resize((thumbnail_width, thumbnail_height), Image.LANCZOS)
    thumbnail_photo = ImageTk.PhotoImage(thumbnail_image)

    # Create thumbnail frame and label
    thumbnail_frame = customtkinter.CTkFrame(master=results_frame_inside, bg_color="#000000", fg_color="#000000",
                                              width=thumbnail_width, height=thumbnail_height)
    thumbnail_label = customtkinter.CTkButton(master=thumbnail_frame, text="", font=("Arial", 11), text_color="white",
                                               width=thumbnail_width, height=thumbnail_height, image=thumbnail_photo,
                                               command=lambda i=i: open_link(i))
    thumbnail_label.image = thumbnail_photo
    thumbnail_label.pack(side="top", fill="both", expand=True)
    thumbnail_frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

    results_thumbnails.append(thumbnail_frame)
    return thumbnail_frame, thumbnail_label

def bind_context_menu(widget, i, popup):
    context_menu_popup = Menu(popup, tearoff=0)
    context_menu_popup.add_command(label="Copy Link", command=lambda index=i-1: copy_to_clipboard(index))
    widget.bind("<Button-3>", lambda event: context_menu_popup.tk_popup(event.x_root, event.y_root))

def close(event):
    global popup
    popup.destroy()

def open_link(index):
    if 0 <= index < len(results_links):
        link = results_links[index]
        webbrowser.open(link)
    else:
        print(f"Invalid index: {index}")

def get_thumbnail_image(url, target_size=(160, 120)):
    try:
        if url:
            response = requests.get(url)
            thumbnail_data = response.content
            thumbnail_image = Image.open(io.BytesIO(thumbnail_data))
            thumbnail_image.thumbnail(target_size)
            return thumbnail_image
        else:
            return None
    except Exception as e:
        print(f"Error loading thumbnail: {e}")
        return None

search_input = customtkinter.CTkEntry(app, font=("Helvetica", 12), fg_color="#414042", text_color="#F2F2F2", border_color="#F2F2F2", corner_radius=8, width=200, height=15)
search_input.insert(0, "Search from YouTube...")
search_input.configure(state=NORMAL)
search_input.place(relx=0.920, rely=0.040, anchor="ne")

search_button = customtkinter.CTkButton(app, text="Search", text_color="#F2F2F2", command=search_videos, font=("Helvetica", 10, "normal"), width=30, height=10)
search_button.place(relx=0.970, rely=0.040, anchor="ne")

# Setări

# Frame pentru secțiunea despre autor (ințial invizibilă)

settings_frame = customtkinter.CTkFrame(master=app, bg_color="#000000")
settings_frame.pack(pady=35, padx=60, fill="both", expand=True)
settings_frame.pack_forget()

# Frame pentru butoanele din secțiunea de setări
settings_button_frame = customtkinter.CTkFrame(master=settings_frame)
settings_button_frame.grid(row=1, column=0, pady=10)  # Adjust the row and column as needed

# Frame pentru butoanele din secțiunea de setări
settings_framebuttons = customtkinter.CTkFrame(master=settings_frame)
settings_framebuttons.grid(row=2, column=0, pady=30)  # Adjust the row and column as needed

settings_visible = False
settings_frame = None  # Initialize the `settings_frame` variable

# Initialize output_entry as a global variable
output_entry = None

# Initialize output_var as a global variable
output_var = None

def toggle_output_widgets():
    global settings_frame, settings_visible, select_folder_button, output_var, output_entry

    try:
        if settings_visible and settings_frame:
            # Dacă fereastra de setări este deja vizibilă, ascunde-o
            settings_frame.pack_forget()
            settings_visible = False
            settings_button.configure(text="Settings")
            return

        if not settings_frame:
            # Dacă fereastra de setări nu a fost încă creată, creează-o
            settings_frame = customtkinter.CTkFrame(master=app)

            settings_frame.pack(pady=35, padx=60, fill="both", expand=True)
            settings_button.configure(text="Hide")

            # Label pentru setări cu aspect de titlu
            settings_label = customtkinter.CTkLabel(settings_frame, text="Settings", text_color="#F2F2F2", font=("Helvetica", 16, "bold"),
                                                    width=140, height=2, fg_color="#000000")
            settings_label.pack(padx=10, pady=0.1, side="top", anchor="center")  # Adjust the padding and placement as needed

            output_label = customtkinter.CTkLabel(settings_frame, text="Output Path: 📂", text_color="#F2F2F2",
                                                  width=40, height=14, fg_color="#000000")
            output_label.pack(padx=65, pady=0.2, side="left", anchor="e")

            if output_var is None:
                output_var = tk.StringVar()

            if hasattr(output_label, "_font"):
                output_entry_font = output_label._font
            else:
                output_entry_font = None

            # La începutul programului, setează output_path
            username = getpass.getuser()
            output_path = os.path.join("C:\\Users", username, "Videos")

            # Crează entry cu destinația prestabilită
            output_entry = customtkinter.CTkEntry(settings_frame, width=700, height=10, fg_color="#414042",
                                      text_color="#F2F2F2", border_color="#414042", corner_radius=8, font=output_entry_font, textvariable=output_var)

            # Completează automat entry cu calea prestabilită
            output_entry.insert(0, output_path)

            # Restul codului pentru pack și altele
            output_entry.pack(padx=5, pady=0.2, side="left", anchor="w")

            if select_folder_button is None:
                select_folder_button = customtkinter.CTkButton(master=settings_frame, width=30, height=10, text="Select Folder", text_color="#F2F2F2", command=select_output_folder)
            select_folder_button.pack(padx=5, pady=0.2, side="left", anchor="w")

            settings_visible = True
    except Exception as e:
        # Prinde și afișează erorile
        messagebox.showerror("Error", f"An error occurred: {str(e)}")

# Funcție apelată când butonul de setări este apăsat
def on_settings_button_click():
    toggle_output_widgets()

def select_output_folder():
    global output_var

    folder_selected = filedialog.askdirectory()
    if folder_selected:
        if output_var is None:
            output_var = tk.StringVar()  # Initialize output_var if it's None
        output_entry.delete(0, tk.END)
        output_entry.insert(0, folder_selected)
        output_var.set(folder_selected)

# Inițializează variabilele pentru etichetă și intrare pentru calea de ieșire
output_label = customtkinter.CTkLabel(master=settings_framebuttons, text="Output Path: 📂")
output_label.pack_forget()  # Ascunde implicit

# Initialize output_entry as a global variable
output_entry = customtkinter.CTkEntry(master=settings_framebuttons, width=40)
output_entry.pack_forget()  # Ascunde implicit

# Initialize output_entry as a global variable
select_folder_button = None

# Button for opening/closing the settings section
settings_button = customtkinter.CTkButton(app, text="Settings", text_color="#F2F2F2", command=toggle_output_widgets)
settings_button.pack(padx=10, pady=10, side="bottom", anchor="sw")

# Open directory
def open_output_directory(directory):
    try:
        if directory and os.path.exists(directory):  # Verifică dacă directory nu este None și există pe disc
            if sys.platform.startswith('win'):
                os.startfile(directory)
            elif sys.platform.startswith('darwin'):
                webbrowser.open('file://' + directory)
            elif sys.platform.startswith('linux'):
                webbrowser.open(directory)
        else:
            print("Error: Directory is not set or does not exist.")
    except Exception as e:
        print(f"Error opening directory: {str(e)}")

# Adăugare buton pentru a deschide directorul de salvare
open_directory_button = customtkinter.CTkButton(app, text="Open Directory", text_color="#F2F2F2", font=("Helvetica", 12, "normal"), command=lambda: open_output_directory(output_path))
open_directory_button.place(relx=0.15, rely=0.70, anchor="center")
open_directory_button.pack_forget()

def center(win):
    """
    centers a tkinter window
    :param win: the main window or Toplevel window to center
    """
    win.update_idletasks()
    width = win.winfo_width()
    frm_width = win.winfo_rootx() - win.winfo_x()
    win_width = width + 2 * frm_width
    height = win.winfo_height()
    titlebar_height = win.winfo_rooty() - win.winfo_y()
    win_height = height + titlebar_height + frm_width
    x = win.winfo_screenwidth() // 2 - win_width // 2
    y = win.winfo_screenheight() // 2 - win_height // 2
    win.geometry('{}x{}+{}+{}'.format(width, height, x, y))
    win.deiconify()

# Run app
app.mainloop()



