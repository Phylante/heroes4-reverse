# coding: utf-8


def format_bytes(size):
    # 2**10 = 1024
    power = 2 ** 10
    n = 0
    power_labels = {0: "", 1: "k", 2: "M", 3: "G", 4: "T"}
    while size > power:
        size /= power
        n += 1
    return f"{size:.2f} {power_labels[n]}" + "b"


def find_gz_signature(filename, dump_gz=False):
    file = open(filename, "rb")
    file.seek(0, 2)  # Seek the end.
    num_bytes = file.tell()  # Get the file size
    print(f"Looking into {num_bytes} bytes")

    count = 0
    offsets_found = []
    for i in range(num_bytes):
        if i % 1000 == 0:
            print(f"Offset {i} being read.")
        file.seek(i)
        three_bytes = file.read(3)  # gz signature is 3 bytes long.
        if three_bytes == b"\x1f\x8b\x08":
            offsets_found.append(i)

            if dump_gz:
                gz_size_bytes = file.read("xx")  # TODO: Next bytes are the length
                gz_size = int.from_bytes(gz_size_bytes, byteorder="little", signed=False)

                # Extract gz
                gz_data = file.read(gz_size + 8)  # TODO: why + 8 ??
                with open("gzs/" + str(i) + ".gz", "wb") as outfile:
                    outfile.write(gz_data)

    print(f"Found {len(offsets_found)} offsets.")
    return offsets_found
