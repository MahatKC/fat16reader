with open('fat16_1sectorpercluster.img', 'rb') as f:
    hexdata = f.read().hex()
    f.close()

def little_endian_to_big_endian(little_endian_hex):
    #receives a string of a hex in little endian representation and returns its big endian representation as a string

    size_in_bytes = len(little_endian_hex)//2
    big_endian = ""
    for i in range(1,size_in_bytes+1):
        index = -i*2
        if i==1:
            big_endian += little_endian_hex[index:]
        else:
            big_endian += little_endian_hex[index:index+2]
    return big_endian

def hex_to_int(hex_value):
    #receives a string with a hex value and returns its integer in base 10

    return int(hex_value, 16)

def little_endian_to_int(hex_value):
    #encapsulates two functions above

    return hex_to_int(little_endian_to_big_endian(hex_value))

def get_value(fat_offset, size):
    #receives the offset (in bytes) and size (in bytes) for an entry and returns its integer value

    little_endian_value = hexdata[fat_offset*2:(fat_offset+size)*2]
    big_endian_value = little_endian_to_big_endian(little_endian_value)
    return hex_to_int(big_endian_value)

def hex_to_string(hex_value):
    #receives a hex value, converts each of its bytes to characters and returns the resulting string

    string = ""

    for i in range(len(hex_value)//2):
        string += chr(hex_to_int(hex_value[i*2:i*2 + 2]))
    
    return string

def read_directory(directory_starting_index):
    i = directory_starting_index*2
    content_fc_pairs = []

    while(hexdata[i:i+2] != '00'):
        attribute = hexdata[i+22:i+24]

        if attribute=='0f' or hexdata[i:i+2]=='e5':
            i += 64
            continue
        else:
            name_hex = hexdata[i:i+22]
            name = hex_to_string(name_hex)
            first_cluster_hex = hexdata[i+52:i+56]
            first_cluster = little_endian_to_int(first_cluster_hex)
            file_size_hex = hexdata[i+56:i+64]
            file_size = little_endian_to_int(file_size_hex)

            if attribute == '10':
                print(f"/"+ name + " "*9 + f"SIZE: {file_size}B")
                content_fc_pairs.append([name, first_cluster])
            elif attribute == '01' or attribute == '20':
                print(name + " "*10 + f"SIZE: {file_size}B")
                content_fc_pairs.append([name, first_cluster])

        i += 64

    return content_fc_pairs

#FAT info
bytes_per_sector = get_value(11, 2)
sectors_per_cluster = get_value(13,1)
reserved_sectors = get_value(14, 2)
number_of_fats = get_value(16, 1)
number_of_dir_entries = get_value(17, 2)
total_sectors = get_value(19, 2)
sectors_per_fat = get_value(22, 2)

first_fat_start_index = reserved_sectors*bytes_per_sector
root_dir_start_index = first_fat_start_index + number_of_fats*sectors_per_fat*bytes_per_sector
data_start_index = root_dir_start_index + (number_of_dir_entries*32)//bytes_per_sector

read_directory(root_dir_start_index)