# coding:utf-8
import os
from pprint import pprint

from colorama import Fore

from utils import format_bytes
from h4r_files_classes import class_map
from project_logger import logger

# Game static data.
H4R_HEADER = bytes(b"\x48\x34\x52\x05")


class H4ResourceFile(object):
    def __init__(self, filename, type):
        self.type = type
        self.unused_files = []
        self.name = filename.split("/")[-1]
        self.begin_files_table = 0
        self.nb_of_files = 0
        self.files_info = []
        # Counts uncompressed space for files where compressed_size == 0.
        self.total_uncompressed_for_nothing = 0
        try:
            self.filename = filename
            self.file = open(filename, "rb")
        except IOError:
            raise Exception(f"Couldn't open file {filename}")
        else:
            self.check_header()
        finally:
            self.scan_file()
            self.find_unused_files()

    def check_header(self):
        """
        Reads the 12 first bytes of the file. Checks for H4R file header correctness.
        Reads file address table and number of files in the h4r file.
        """
        self.file.seek(0)
        if self.file.read(4) != H4R_HEADER:
            raise Exception(f"Bad header: {self.name} is not a h4r file.")
        # This is the address of the table listing the files in the H4R file.
        self.begin_files_table = int.from_bytes(self.file.read(4), "little")
        self.nb_of_files = int.from_bytes(self.file.read(4), "little")
        logger.info(
            f"{Fore.CYAN}Checking header of {self.name} : OK.\n"
            f"{self.nb_of_files} files headers are located at {self.begin_files_table}{Fore.RESET}\n"
        )

    def find_unused_files(self):
        """
        Finds the files that have been replaced, but still lies in the h4r.
         compressed_size == 0 <-> File is not used anymore
         """
        self.unused_files = [file for file in self.files_info if file.compressed_size == 0 and file.file_offset != 0]
        if self.unused_files:
            logger.warning(f"{Fore.RED}Found {len(self.unused_files)} unused files !{Fore.RESET}")

    def bytes_uncovered(self):
        """This method is used to know if, while reversing, we missed some bytes."""
        # header + table offset + number of files = 12 bytes.
        bytes_discovered = 12
        total_bytes = os.path.getsize(self.filename)

        # Iterate over the files : calculate their record in the begin_files_table + their reported size.
        for file in self.files_info:
            bytes_discovered += file.binary_end - file.binary_start + file.compressed_size

        percent = float(bytes_discovered) / total_bytes * 100
        logger.info(
            f"{format_bytes(bytes_discovered)} out of {format_bytes(total_bytes)} : {percent:.2f} %\n"
            f"{total_bytes - bytes_discovered} bytes remaining."
        )

    def map_unknow_regions(self):
        """
        """
        data_parts = sorted(self.files_info, key=lambda x: x.file_offset)

        # This part is for DATA ONLY.
        missing = []
        start = 0
        for i, file in enumerate(data_parts[:-1]):
            if file.file_offset + file.compressed_size != data_parts[i + 1].file_offset:
                # Files are not contiguous ! We keep track of the missing interval.
                missing.append((file.file_offset + file.compressed_size, data_parts[i + 1].file_offset))
        # Check for last item in list:
        if not data_parts[-1].file_offset + data_parts[-1].compressed_size == os.path.getsize(self.filename):
            missing.append(
                (data_parts[-1].file_offset + data_parts[-1].compressed_size, os.path.getsize(self.filename))
            )

        # Write the part for table of pointer of files here.

        pprint(missing)

    def list_undiscovered_bytes(self):
        """
        Warning : developement feature only. This can be resource consuming.
        Keeps track of every single byte discovered
        """

        # Already checked the header.
        bytes_discovered = list(range(12))
        all_bytes = set(range(os.path.getsize(self.filename)))
        for byte in bytes_discovered:
            all_bytes.remove(byte)
        for file in self.files_info:
            all_bytes -= set(range(file.binary_start, file.binary_end))
            all_bytes -= set(range(file.file_offset, file.file_offset + file.compressed_size))

        boundaries = []
        lol = list(all_bytes)
        lol.sort()
        print(f"{len(all_bytes)} to sort.")
        print("building boundaries")
        for j, i in enumerate(lol[:-1]):
            if i + 1 == lol[j + 1]:
                continue
            else:
                boundaries.append(i)
        pprint(boundaries)

    def check_updates(self):
        for file in self.files_info:
            if file.compressed_size == 0 and file.uncompressed_size != 0:
                logger.info(
                    f"Found a file that shouldn't be here: size is {str(format_bytes(file.uncompressed_size)).ljust(6)}"
                )
                self.total_uncompressed_for_nothing += file.uncompressed_size

    def scan_file(self):
        """"""
        # +4 because we already read the number of files, which is the first 4 bytes of the table.
        self.file.seek(self.begin_files_table + 4)
        for i in range(self.nb_of_files):
            binary_start = self.file.tell()
            file_offset = int.from_bytes(self.file.read(4), "little")
            compressed_size = int.from_bytes(self.file.read(4), "little")
            if file_offset == 0 and compressed_size == 0:
                special_case = True

            uncompressed_size = int.from_bytes(self.file.read(4), "little")
            date = int.from_bytes(self.file.read(4), "little")
            name_size = int.from_bytes(self.file.read(2), "little")
            name = self.file.read(name_size).decode("iso-8859-1")
            extra_data_size = int.from_bytes(self.file.read(2), "little")
            extra_data = self.file.read(extra_data_size).decode("iso-8859-1")
            updated_file_name_size = int.from_bytes(self.file.read(2), "little")
            updated_file_name = self.file.read(updated_file_name_size).decode("iso-8859-1")
            compression = int.from_bytes(self.file.read(4), "little")
            binary_end = self.file.tell()

            h4r_file = class_map[name.split(".")[0]](
                self.file,
                self.name,
                extra_data,
                file_offset,
                uncompressed_size,
                compressed_size,
                date,
                name_size,
                name,
                extra_data_size,
                updated_file_name_size,
                updated_file_name,
                compression,
                binary_start,
                binary_end,
            )

            self.files_info.append(h4r_file)

    def extract_all_files(self, write_mp3=False):
        n = 0
        for i, file in enumerate(self.files_info):
            try:
                file.write_to_disk(write_mp3)
                n += 1
            except OSError as e:
                logger.error(f"Error is in file at index {i}", exc_info=e)
        logger.info(f"{n} files written out of {self.nb_of_files}")
