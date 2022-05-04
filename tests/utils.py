import tarfile
import json
import io


def create_tar_buffer(files_data, encoding='utf-8', meta_encoding='utf-8',
                      compression_algo='gz'):
    """Generate a file buffer based off a dictionary."""
    if not isinstance(files_data, (dict,)):
        return None
    if not all(isinstance(v, (str, dict)) for v in files_data.values()):
        return None
    tar_buffer = io.BytesIO()
    mode = f'w:{compression_algo}'
    with tarfile.open(fileobj=tar_buffer, mode=mode) as tar_file:
        for file_name, file_content in files_data.items():
            if 'metadata.json' in file_name:
                file_buffer = \
                    io.BytesIO(json.dumps(file_content).encode(meta_encoding))
            elif file_name.endswith('json'):
                file_buffer = \
                    io.BytesIO(json.dumps(file_content).encode(encoding))
            elif file_name.endswith('csv'):
                file_buffer = io.BytesIO(file_content.encode(encoding))
            else:
                return None
            info = tarfile.TarInfo(name=file_name)
            info.size = len(file_buffer.getvalue())
            tar_file.addfile(tarinfo=info, fileobj=file_buffer)
    tar_buffer.seek(0)
    return tar_buffer.getvalue()
