# coding: utf-8
import gzip
import os

import ffmpeg
from colorama import Fore

from settings import extraction_path
from utils import format_bytes

from project_logger import logger


class H4RFile(object):
    """
    Heroes4 Resource.
    Found inside an h4r file.
    Base class to handle all data.
    Others classes in this file subclass this one to add extraction and display mecanisms.
    """

    def __init__(
        self,
        file,
        h4resourcefile="",
        extra_data="",
        file_offset=0,
        uncompressed_size=0,
        compressed_size=0,
        date=0,
        name_size=0,
        name="",
        extra_data_size=0,
        updated_file_name_size=0,
        updated_file_name="",
        compression=0,
        binary_start=0,
        binary_end=0,
    ):
        self.data = b""
        self.file = file
        self.h4resourcefile = h4resourcefile
        self.type = self.h4resourcefile.split("\\")[-1].split(".")[0]
        self.file_offset = file_offset
        self.uncompressed_size = uncompressed_size
        self.compressed_size = compressed_size
        self.date = date
        self.name_size = name_size
        self.name = name
        self.extra_data_size = extra_data_size
        self.extra_data = extra_data
        self.data_type = ""
        self.updated_file_name_size = updated_file_name_size
        self.updated_file_name = updated_file_name
        self.compression = compression
        self.binary_start = binary_start
        self.binary_end = binary_end
        self.out_file = ""
        self.find_data_type()

    def __repr__(self):
        return f"""
        File {self.name}
        Data Type is {self.data_type}
        Compression is {f'{Fore.GREEN}active{Fore.RESET}' if self.compression else f'{Fore.RED}inactive{Fore.RESET}'}.
        {f'Compressed size is {format_bytes(self.compressed_size)} and file size is {format_bytes(self.uncompressed_size)}' if self.compression else f'File size is {format_bytes(self.uncompressed_size)}'}
        Table data starts at {self.binary_start} and ends at {self.binary_end}
        Data is at offset {self.file_offset}
        {f'File is replaced by {Fore.RED}{self.updated_file_name}{Fore.RESET} and its size is {self.updated_file_name_size}' if self.updated_file_name_size else ''}"""

    def find_data_type(self,):
        extension_mapping = {
            "unknown": ".unk",
            "actor_sequence": ".seq",
            "adv_actor": ".act",
            "adv_object": ".obj",
            "animation": ".ani",
            "battlefield_preset_map": ".map",
            "bitmap_raw": ".raw",
            "bink": ".bik",
            "castle": ".cst",
            "combat_actor": ".cmb",
            "combat_header_table_cache": ".cht",
            "combat_object": ".obj",
            "font": ".fnt",
            "game_maps": ".h4c",
            "layers": ".lay",
            "sound": ".mp3",
            "strings": ".txt",
            "table": ".txt",
            "terrain": ".ter",
            "transition": ".tra",
        }

        # Fnd the extension.
        self.data_type = extension_mapping[self.name.split(".")[0]]

    def extract(self):
        self.file.seek(self.file_offset)
        self.data = self.file.read(self.compressed_size)
        # 3 = compressed. 1 = uncompressed. Can check if compressed_size == uncompressed_size too.
        if self.compression == 3:
            bytes_to_write = gzip.decompress(self.data)
            if self.uncompressed_size != len(bytes_to_write):
                logger.warning(f"{Fore.RED}extracting was NOT OK !{Fore.RESET}")
            self.data = bytes_to_write

    def save_file(self, write_mp3):
        out_dir = os.path.join(extraction_path, self.type.capitalize())
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
            # out_file: Remove the .h4d and write the file with its name + add extension.
        self.out_file = os.path.join(out_dir, ".".join(self.name.split(".")[:-1]) + self.data_type)
        with open(self.out_file, "wb") as out:
            written = out.write(self.data)
            try:
                assert self.uncompressed_size == written
            except AssertionError:
                logger.warning(
                    f"{Fore.RED}Error: File should be {str(self.uncompressed_size).ljust(6)}, and is {written}{Fore.RESET} : {self.name}"
                )

        del self.data

    def write_to_disk(self, write_mp3):
        # Extract only if there is NOT an updated version.
        if not self.updated_file_name_size:
            self.extract()
            self.save_file(write_mp3)


class Sound(H4RFile):
    """
    Handles a Sound file
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sound_type = ""
        self.channels = 0
        self.samplerate = 0

    def extract(self):
        # TODO: This is only for RAW. Need mp3
        super(Sound, self).extract()
        self.sound_type = "RAW" if int.from_bytes(self.data[0:3], "little") == 0 else "MP3"
        bit_per_sample = self.data[3]
        self.channels = self.data[4]
        self.samplerate = int.from_bytes(self.data[5:9], "little")
        if self.sound_type == "RAW":
            # we need to save a .pcm.
            self.data_type = ".pcm"
            size = int.from_bytes(self.data[9:13], "little")
            unknown = int.from_bytes(self.data[13:14], "little")
            assert len(self.data) == size + 15
        else:
            sample_count = int.from_bytes(self.data[9:13], "little")
            unknown = int.from_bytes(self.data[13:15], "little")
            size = int.from_bytes(self.data[15:19], "little")
            try:
                assert len(self.data) == size + 19
            except AssertionError as e:
                logger.error(f"data length is {len(self.data)}, file says it should be {size}")
                raise e

    def save_file(self, write_mp3):
        super(Sound, self).save_file(write_mp3)
        if self.sound_type == "RAW" and write_mp3:
            out_dir = os.path.join(extraction_path, self.type.capitalize(), "mp3")
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)
            #  Signed 16-bit PCM Big-Endian Mono/Stereo 22050/40100 Hz theorically.
            ffmpeg_input_kwargs = {"f": "s16be", "acodec": "pcm_s16be", "ar": self.samplerate, "ac": self.channels}
            # Put our converted pcms in a standalone folder.
            name_without_pcm = ".".join(self.out_file.split(".")[:-1])
            name_with_mp3 = name_without_pcm.split("/")[-1] + ".mp3"
            full_name = os.path.join(out_dir, name_with_mp3)
            ffmpeg_output_kwargs = {"filename": full_name}
            (ffmpeg.input(self.out_file, **ffmpeg_input_kwargs).output(**ffmpeg_output_kwargs).overwrite_output().run())


class Table(H4RFile):
    """
    Handles a Table file
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class Strings(H4RFile):
    """
    Handles a Strings file
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class GameMaps(H4RFile):
    """
    Handles a GameMaps file
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class AdventureObject(H4RFile):
    """
    Handles a GameMaps file
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class_map = {
    "sound": Sound,
    "table": Table,
    "strings": Strings,
    "game_maps": GameMaps,
    "adv_object": AdventureObject,
    "bink": H4RFile,
    "font": H4RFile,
    "layers": H4RFile,
    "transition": H4RFile,
    "animation": H4RFile,
    "adv_actor": H4RFile,
    "combat_actor": H4RFile,
    "combat_object": H4RFile,
    "actor_sequence": H4RFile,
    "terrain": H4RFile,
    "castle": H4RFile,
    "bitmap_raw": H4RFile,
    "battlefield_preset_map": H4RFile,
    "combat_header_table_cache": H4RFile,
}
