import requests
import time
import yadisk
import datetime
from progress.bar import IncrementalBar

APP_ID = 7535898
VK_SERVICE_KEY = '2711e5862711e5862711e586fd2763189c227112711e5867818f4dc214d9ce650b8675b'


class User:
    def __init__(self, user_id, album_id, yd_token, count=5):
        self.user_id = user_id
        self.album_id = album_id
        self.yd_token = yadisk.YaDisk(token=yd_token)
        self.count = count

    # Запрос на получение фотографий, возвращает ответ в виде файла в формате json.
    def get_photo_json(self):
        response = requests.get(
            'https://api.vk.com/method/photos.get',
            params={'access_token': VK_SERVICE_KEY,
                    'owner_id': self.user_id,
                    'album_id': self.album_id,
                    'count': self.count,
                    'v': 5.118,
                    'extended': 1}
        )
        json_dict = response.json()
        return json_dict

    # Достает из json ссылки на фотографии с максимальным размером и помещает их в список из словарей
    # (каждая ссылка хранится в отдельном словаре, вместе с ней хранится уникальное имя,
    # которое будет нужно для дальнейшего сохранения фотографии на диске, а также размер файла.
    def make_list_with_unique_names(self):
        json_dict = self.get_photo_json()
        pict_list = []
        for item in json_dict['response']['items']:
            pict_dict = {'count': item['likes']['count'],
                         'url': item['sizes'][len(item['sizes']) - 1]['url'],
                         'size': item['sizes'][len(item['sizes']) - 1]['type'],
                         'date': item['date']}
            pict_list.append(pict_dict)
        for element in pict_list:
            element_count = 0
            for name in pict_list:
                if name['count'] == element['count']:
                    element_count += 1
                    if element_count <= 1:
                        name['name'] = str(name['count'])
                    else:
                        timestamp = name['date']
                        date = datetime.datetime.fromtimestamp(timestamp)
                        name['name'] = str(name['count']) + '_' + str(date.strftime('%Y-%m-%d.%H.%M.%S'))
        for element in pict_list:
            del (element['count'], element['date'])
        return pict_list

    # Загрузка фотографий на Яндекс.Диск.
    # Создает для фотографий отдельную папку (по умолчанию - 'vk_images').
    # Создает файл в формате json со сведениями об имени фотографий и их размере.
    def upload_photos(self, dir_path='vk_images'):
        pictures_list = self.make_list_with_unique_names()
        progress_bar = IncrementalBar('Загрузка фотографий на ЯД', max=len(pictures_list))
        try:
            self.yd_token.mkdir(dir_path)
        except yadisk.exceptions.PathExistsError:
            pass
        info_json = open(f'info.json', 'w')
        for image in pictures_list:
            to_json = {'file_name': image['name'], 'size': image['size']}
            info_json.write(str(to_json) + '\n')
            try:
                self.yd_token.upload_url(image['url'], f"{dir_path}/{image['name']}.jpg")
            except yadisk.exceptions.PathExistsError:
                pass
            progress_bar.next()
            time.sleep(1)
        progress_bar.finish()
        info_json.close()


def get_user_id():
    print('Необходимо ввести ID пользователя или имя из короткой ссылки.'
          '\nНажмите 1 для ввода ID.'
          '\nНажмите 2 для ввода screen name из короткой ссылки.')
    input_key = input('Введите команду: ')
    if input_key == '1':
        input_id = input('Введите ID: ')
        return input_id
    elif input_key == '2':
        while True:
            input_sn = input('Введите screen_name из короткой ссылки на страницу: ')
            response = requests.get(
                'https://api.vk.com/method/utils.resolveScreenName',
                params={'access_token': VK_SERVICE_KEY,
                        'screen_name': input_sn,
                        'v': 5.118})
            if response.json()['response']:
                input_sn = response.json()['response']['object_id']
                return input_sn
            else:
                print('Ошибка. Пользователя с таким screen name не найден.')
    else:
        print('Извините, такая команда отсутствует.')


if __name__ == '__main__':
    user_id = get_user_id()
    yd_token = input('Введите OAuth-токен из Яндекс.Полигона: ')
    photo_count = int(input('Введите количество фотографий, которые вы ходите сохранить на ЯД: '))
    test_user = User(user_id, 'profile', yd_token, photo_count)
    test_user.upload_photos()