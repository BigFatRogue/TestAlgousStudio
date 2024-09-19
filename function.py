import ffmpeg
import os
import pathlib


def filename_to_sequence(filename: str) -> tuple:
    """
    :param filename: blood.0002.jpg or fire_232 321.jpg
    :return: (blood., '%04d', 'jpg', '0002') or (fire_232., '%34d', 'jpg', '321')
    """
    filename = pathlib.Path(filename)
    name = filename.stem
    suffix = filename.suffix
    l = []
    for s in name[::-1]:
        if not s.isdigit():
            break
        l.append(str(s))
    if l:
        return name[:len(name) - len(l)], f'%0{len(l)}d', suffix, ''.join(l)[::-1]


def get_sequence(path: str) -> dict:
    """
    Рекурсивный перебор указанного каталога, поиск секвенций и добавления их в словарь
    :param path: путь к каталогу
    :return: {'seq_name': {'pattern': str 'count_file': int, 'root': str, 'suffix': str, 'start_number': str}}
    """
    result = {}
    for root, folders, files in os.walk(path):
        for file in files:
            seq_tuple = filename_to_sequence(file)
            if seq_tuple:
                seq, pattern, suffix, start_number = seq_tuple
                if seq not in result:
                    result[seq] = {'pattern': pattern, 'count_file': 1, 'root': root, 'suffix': suffix, 'start_number': start_number}
                else:
                    result[seq]['count_file'] += 1
    return result


def convert_to_mp4(seq_name: str, root: str, out_path: str, pattern: str, fps: int, suffix: str, out_name: str, start_number: str) -> None:
    (
        ffmpeg
        .input(os.path.join(root, seq_name + pattern + suffix), framerate=fps, start_number=int(start_number))
        .output(os.path.join(out_path, out_name + '.mp4'))
        .run()
    )


def main(path) -> None:
    """
    Конвертация найденных секвенций в заданном каталоге в mp4
    :param path:
    :return:
    """
    data = get_sequence(path)
    if data:
        out_path = os.path.join(os.getcwd(), 'result')
        if not os.path.exists(out_path):
            os.mkdir(out_path)

        for seq, value in data.items():
            convert_to_mp4(seq_name=seq,
                           root=value['root'],
                           suffix= value['suffix'],
                           pattern=value['pattern'],
                           start_number=value['start_number'],
                           fps=24,
                           out_name=seq.strip(),
                           out_path=out_path)


if __name__ == '__main__':
    PATH = r'YOR PATH (absolute or relative)'
    main(PATH)


