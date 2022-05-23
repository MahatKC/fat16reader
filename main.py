import os

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

def remove_filename_spaces(filename):
    name_without_spaces = ""
    split_list = filename.split(" ")
    first_word = True
    for element in split_list:
        if len(element)>0:
            if first_word:
                first_word = False
            else:
                name_without_spaces += '.'
            name_without_spaces += element

    return name_without_spaces

def read_directory(directory_starting_index):
    #Receives integer with index of the directory start
    #Read directory information and returns the information about its contents

    i = directory_starting_index*2
    content_info = []

    while(hexdata[i:i+2] != '00'):
        attribute = hexdata[i+22:i+24]

        if attribute=='0f' or hexdata[i:i+2]=='e5':
            i += 64
            continue
        else:
            name_hex = hexdata[i:i+22]
            name_string = hex_to_string(name_hex)
            name = remove_filename_spaces(name_string)
            first_cluster_hex = hexdata[i+52:i+56]
            first_cluster = little_endian_to_int(first_cluster_hex)
            file_size_hex = hexdata[i+56:i+64]
            file_size = little_endian_to_int(file_size_hex)

            if attribute == '10':
                print(f"/"+ name + " "*(24-len(name)) + f"SIZE: {file_size}B")
                content_info.append([name, first_cluster, attribute])
            elif attribute == '01' or attribute == '20':
                print(name + " "*(25-len(name)) + f"SIZE: {file_size}B")
                content_info.append([name, first_cluster, attribute])

        i += 64

    return content_info

def check_valid_choice(content_info, open_choice):
    #Check if the filename the user wants to open is in the current directory

    #close program
    if open_choice.lower()=='x':
        return True, []
    #keep on current folder
    elif open_choice == '.':
        return True, ['.']
    else:
        for content in content_info:
            if open_choice in content:
                return True, content

        return False, []

def input_content(old_open_choice):
    #Gets input from user and calls function to check if input is valid
    #Returns the info from the file/subdirectory the user wants to open

    is_valid, content = check_valid_choice(content_info, input())
    while(not is_valid):
        print("Invalid name, try again")
        is_valid, content = check_valid_choice(content_info, input())
    if len(content)==1:
        return old_open_choice

    return content

def clear():
    #clears terminal
    os.system('cls' if os.name == 'nt' else 'clear')

def check_fat_table(cluster_number):
    final_cluster = cluster_number
    fc_address = (first_fat_start_index+final_cluster)*2
    next_cluster = little_endian_to_int(hexdata[fc_address:fc_address+4])
    while(next_cluster != 255):
        final_cluster += 1
        fc_address = (first_fat_start_index+final_cluster)*2
        next_cluster = little_endian_to_int(hexdata[fc_address:fc_address+4])
    return final_cluster

def cluster_address(cluster_number):
    #receives integer with the number of the first cluster of the data and returns its starting address and
    #final address

    if cluster_number == 0:
        return root_dir_start_index, data_start_index
    else:
        final_cluster = check_fat_table(cluster_number)
        starting_address = (cluster_number-2)*sectors_per_cluster*bytes_per_sector + data_start_index
        final_address = (final_cluster-2)*sectors_per_cluster*bytes_per_sector + data_start_index

        return starting_address, final_address
    
def read_file(starting_address, final_address):
    f_seek = starting_address*2
    while(hexdata[f_seek:f_seek+2]!='00' and f_seek<final_address*2):
        f_seek += 2
        
    print(hex_to_string(hexdata[starting_address*2:f_seek]))

def standard_print():
    print("-"*36)
    print("Write the name of the file or subdirectory (without preceding /) to be opened or input X to close program.")

if __name__ == '__main__':
    image_name = input("Insert FAT16 image name to be read\n")
    with open(image_name, 'rb') as f:
        hexdata = f.read().hex()
        f.close()

    clear()
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
    data_start_index = root_dir_start_index + (number_of_dir_entries*32)

    open_choice = ["ROOT", 0, "10"]
    content_info = read_directory(root_dir_start_index)
    standard_print()
    open_choice = input_content(open_choice)

    while(len(open_choice)>0):
        if open_choice[2] == '10':
            clear()
            starting_address, final_address = cluster_address(open_choice[1])
            content_info = read_directory(starting_address)
            standard_print()
        elif open_choice[2] == '01' or open_choice[2] == '20':
            
            starting_address, final_address = cluster_address(open_choice[1])
            print("-"*36)
            read_file(starting_address, final_address)
            standard_print()
        open_choice = input_content(open_choice)
    
