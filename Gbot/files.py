from .Gbot import GeorgeBot, telebot

class FilesMixin:

    def document_download(self:GeorgeBot, message: telebot.types.Message, user:dict, folder_path) -> tuple[str, dict]:
        try:
            document:telebot.types.Document = getattr(message, "document", None)
            audio: telebot.types.Audio = getattr(message, "audio", None)
            if document is None:
                document = audio
            file_info = self.get_file(document.file_id)
            file_bytes = self.download_file(file_info.file_path)
            file = {
                'tg_id': document.file_id,
                'name': document.file_name,
                'folder': folder_path,
                'bytes': file_bytes,
            }
            ID = self.files_data.download_file(file)
            if ID is None:
                raise Exception("File doesn`t downloaded")
            user.update({"file_name": file.get('name')})
            self.display(user, "good_file")
            return file_info
        except Exception as e:
            self.edit_message_text(e, user.get('load_cht_id'), user.get('load_msg_id'))
        finally:
            # self.delete_message(user.get('load_cht_id'), user.get('load_msg_id'))
            self.download_buffer.remove(user.get('load_cht_id'))

    def document_upload(self:GeorgeBot, file_info:dict, f_id) -> str|bytes:
        try:
            tg_id = file_info.get('tg_id')
            file_info = self.get_file(tg_id)
            return {'document': tg_id}
        except:
            f_name = file_info.get('f_name')
            file = self.files_data.upload_file(f_id)
            return {'document': file, 'visible_file_name': f_name}
