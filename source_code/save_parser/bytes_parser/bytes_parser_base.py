from typing import Union


class BytesParserBase:
    def __init__(self, file_path: str, starting_offset=0):
        self.offset = starting_offset
        self.base_file_path = file_path
        self.bytes = bytearray(open(self.base_file_path, 'rb').read())

    def save(self, file_path: str = None):
        if file_path is None:
            file_path = self.base_file_path
        with open(file_path, 'wb') as f:
            f.write(self.bytes)

    def delete_bytes(self, num_bytes: int):
        if num_bytes == 0:
            return
        for i in range(num_bytes):
            del self.bytes[self.offset]

    def delete_string(self, num_bytes_len: int):
        if num_bytes_len == 0:
            return
        string_len = self.read_int(num_bytes_len, change_offset=False)
        self.delete_bytes(string_len + num_bytes_len)

    def replace_int(self, num: int, num_bytes: int, change_offset=True):
        if num_bytes == 0:
            return
        for i in range(1, num_bytes + 1):
            self.bytes[self.offset + i - 1] = (num >> ((i - 1) * 8)) & 0xff
        if change_offset:
            self.offset += num_bytes

    def write_int(self, num: int, num_bytes: int, change_offset=True):
        if num_bytes == 0:
            return
        for i in range(num_bytes, 0, -1):
            self.bytes.insert(self.offset, (num >> ((i - 1) * 8)) & 0xff)
        if change_offset:
            self.offset += num_bytes

    def write_string(self, string: Union[str, bytearray], num_bytes_len: int, change_offset=True):
        if num_bytes_len == 0:
            return
        if type(string) is str:
            string += chr(0)
        else:
            string.append(0)
        self.write_int(len(string), num_bytes_len, change_offset=False)
        for i, char in enumerate(string[::-1]):
            self.bytes.insert(self.offset + num_bytes_len, ord(char) if type(string) is str else char)
        if change_offset:
            self.offset += num_bytes_len + len(string)

    def replace_string(self, string: Union[str, bytearray], num_bytes_len: int, change_offset=True):
        if num_bytes_len == 0:
            return
        self.delete_string(num_bytes_len)
        self.write_string(string, num_bytes_len, change_offset=False)
        if change_offset:
            self.offset += num_bytes_len + len(string)

    def read_int(self, num_bytes: int, change_offset=True) -> int:
        if num_bytes == 0:
            return 0
        left_shift = 0
        ans = self.bytes[self.offset]
        for i in range(1, num_bytes):
            left_shift += 8
            ans |= self.bytes[self.offset + i] << left_shift
        if change_offset:
            self.offset += num_bytes
        return ans

    def read_string(self, num_bytes_len: int, change_offset=True) -> str:
        if num_bytes_len == 0:
            return ''
        string_len = self.read_int(num_bytes_len, change_offset=False)
        string = ''.join([chr(self.bytes[self.offset + num_bytes_len + i]) for i in range(string_len - 1)])
        if change_offset:
            self.offset += num_bytes_len + string_len
        return string
