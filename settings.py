# coding=utf-8
import os

# As a user or developper, you should set this:
path_to_game_directory = "../Heroes_of_Might_and_Magic_IV/"

data_dir = {
    "text": os.path.join(path_to_game_directory, "Data/text.h4r"),
    "movies": os.path.join(path_to_game_directory, "Data/movies.h4r"),
    "updates": os.path.join(path_to_game_directory, "Data/updates.h4r"),
    "heroes4": os.path.join(path_to_game_directory, "Data/heroes4.h4r"),
    "music": os.path.join(path_to_game_directory, "Data/music.h4r"),
}

extraction_path = "./h4r_files/"
