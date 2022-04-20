from source_code.save_parser.bytes_parser import BytesParserSpecializer


# Для того, чтобы благодаря этому скрипту нельзя было узнать то, как в сохранения вписываются порядковые номера,
# и как они проверяются, на гитхабе был выложен данный скрипт не полностью.
# Для полного доступа обратитесь по почте vladsid0601@gmail.com


class SatisfactorySaveParser:
    def __init__(self, save_file: str):
        self.bytes_parser = None
        self.set_save(save_file)

    # получение порядкового номера у сохранения
    def get_order(self) -> int:
        return 1

    # получение id сессии
    def get_session_id(self) -> int:
        return 1

    # установить следующий шифрованный порядковый номер для сохранения
    def next_order(self):
        pass

    # установить новое сохранение классу
    def set_save(self, save_file: str):
        self.bytes_parser = BytesParserSpecializer(save_file)

    # проверить, является ли указанное сохранение следующим
    def is_next_save(self, next_save_file: str) -> bool:
        return True

    # проверить сохранение на правильность содержания данных
    def is_correct_save(self) -> bool:
        return True

    def save(self, file_path: str = None):
        self.bytes_parser.save(file_path)

    # сбрасывание порядкового номера (становится равным 1) и установка session_id
    def reset(self, session_id: int):
        pass
