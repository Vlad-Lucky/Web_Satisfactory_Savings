from typing import Union


# parser для байтовых файлов
class BytesParserBase:
    def __init__(self, file_path: str, starting_offset=0):
        self.base_file_path = file_path
        self.bytes = bytearray(open(self.base_file_path, 'rb').read())
        # переменная смещения, отвечающая за нынешнее положение "курсора" в байт-файле
        self.offset = starting_offset

    def reset_offset(self):
        """сброс смещения"""
        self.offset = 0

    def save(self, file_path: str = None):
        """сохранение байтового файла"""
        if file_path is None:
            file_path = self.base_file_path
        with open(file_path, 'wb') as f:
            f.write(self.bytes)

    def delete_bytes(self, num_bytes: int):
        """удаление определенного количества байт"""
        if num_bytes == 0:
            return
        for i in range(num_bytes):
            del self.bytes[self.offset]

    def delete_string(self, num_bytes_len: int):
        """удаление строки"""
        if num_bytes_len == 0:
            return
        string_len = self.read_int(num_bytes_len, change_offset=False)
        self.delete_bytes(string_len + num_bytes_len)

    def write_bytes(self, bytes: bytearray, change_offset=True):
        """добавление байт"""
        if len(bytes) == 0:
            return
        for byte in bytes:
            self.bytes.insert(self.offset, byte)
        if change_offset:
            self.offset += len(bytes)

    def write_int(self, num: int, num_bytes: int, change_offset=True):
        """добавление числа"""
        if num_bytes == 0:
            return
        for i in range(num_bytes, 0, -1):
            self.bytes.insert(self.offset, (num >> ((i - 1) * 8)) & 0xff)
        if change_offset:
            self.offset += num_bytes

    def write_string(self, string: Union[str, bytearray], num_bytes_len: int, change_offset=True):
        """добавление строки"""
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

    def replace_bytes(self, bytes: bytearray, change_offset=True):
        """переписывание байт"""
        if len(bytes) == 0:
            return
        for i, byte in enumerate(bytes):
            self.bytes[self.offset + i] = byte
        if change_offset:
            self.offset += len(bytes)

    def replace_int(self, num: int, num_bytes: int, change_offset=True):
        """переписывание числа"""
        if num_bytes == 0:
            return
        for i in range(1, num_bytes + 1):
            self.bytes[self.offset + i - 1] = (num >> ((i - 1) * 8)) & 0xff
        if change_offset:
            self.offset += num_bytes

    def replace_string(self, string: Union[str, bytearray], num_bytes_len: int, change_offset=True):
        """замена строки"""
        if num_bytes_len == 0:
            return
        self.delete_string(num_bytes_len)
        self.write_string(string, num_bytes_len, change_offset=False)
        if change_offset:
            self.offset += num_bytes_len + len(string)

    def read_bytes(self, num_bytes: int, change_offset=True) -> bytearray:
        """чтение байт"""
        res = self.bytes[self.offset:self.offset + num_bytes]
        if change_offset:
            self.offset += num_bytes
        return res

    def read_int(self, num_bytes: int, change_offset=True) -> int:
        """чтение числа"""
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
        """чтение строки"""
        if num_bytes_len == 0:
            return ''
        string_len = self.read_int(num_bytes_len, change_offset=False)
        string = ''.join([chr(self.bytes[self.offset + num_bytes_len + i]) for i in range(string_len - 1)])
        if change_offset:
            self.offset += num_bytes_len + string_len
        return string
