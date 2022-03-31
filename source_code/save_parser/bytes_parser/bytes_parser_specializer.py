from typing import Union
from source_code.save_parser.bytes_parser.bytes_parser_base import BytesParserBase


# bytes parser, специализированный на отдельных типах
class BytesParserSpecializer(BytesParserBase):
    def read_int32(self, change_offset=True) -> int:
        return self.read_int(4, change_offset=change_offset)

    def read_int64(self, change_offset=True) -> int:
        return self.read_int(8, change_offset=change_offset)

    def read_string_len32(self, change_offset=True) -> str:
        return self.read_string(4, change_offset=change_offset)

    def read_string_len64(self, change_offset=True) -> str:
        return self.read_string(8, change_offset=change_offset)

    def replace_int32(self, num: int, change_offset=True):
        self.replace_int(num, 4, change_offset=change_offset)

    def replace_int64(self, num: int, change_offset=True):
        self.replace_int(num, 8, change_offset=change_offset)

    def replace_string_len32(self, string: Union[str, bytearray], change_offset=True):
        self.replace_string(string, 4, change_offset=change_offset)

    def replace_string_len64(self, string: Union[str, bytearray], change_offset=True):
        self.replace_string(string, 8, change_offset=change_offset)

    def write_int32(self, num: int, change_offset=True):
        self.write_int(num, 4, change_offset=change_offset)

    def write_int64(self, num: int, change_offset=True):
        self.write_int(num, 8, change_offset=change_offset)

    def write_string_len32(self, string: Union[str, bytearray], change_offset=True):
        self.write_string(string, 4, change_offset=change_offset)

    def write_string_len64(self, string: Union[str, bytearray], change_offset=True):
        self.write_string(string, 8, change_offset=change_offset)

    def delete_int32(self):
        self.delete_bytes(4)

    def delete_int64(self):
        self.delete_bytes(8)

    def delete_string_len32(self):
        self.delete_string(4)

    def delete_string_len64(self):
        self.delete_string(8)
