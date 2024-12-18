import hashlib
import math
import os
import random
import string
import sys
import time
from urllib import request
from urllib.parse import quote

import oss2
from loguru import logger
import pdb
import time



def oss_progress(bytes_consumed, total_bytes):
    ratio = int(bytes_consumed * 100) // int(total_bytes)
    print('\r', end='')
    print('Upload progress: {}%: '.format(ratio), '▋' * (ratio // 2), end='')
    sys.stdout.flush()


def oss_upload_simple(bucket, key, content):
    resp = bucket.put_object(key,
                             content,
                             headers={'content-length': str(len(content))},
                             progress_callback=oss_progress)
    if resp.status < 200 or resp.status > 299:
        return 'simple upload fail'
    return None


def oss_upload_multipart(bucket, key, content):
    begin = time.time()
    # 也可以直接调用分片上传接口。
    # 首先可以用帮助函数设定分片大小，设我们期望的分片大小为128KB
    total_size = len(content)
    part_size = oss2.determine_part_size(total_size, preferred_size=128 * 1024)

    # 初始化分片上传，得到Upload ID。接下来的接口都要用到这个Upload ID。
    upload_id = bucket.init_multipart_upload(key).upload_id

    # 逐个上传分片
    # 其中oss2.SizedFileAdapter()把fileobj转换为一个新的文件对象，新的文件对象可读的长度等于size_to_upload
    parts = []
    part_number = 1
    offset = 0
    while offset < total_size:
        size_to_upload = min(part_size, total_size - offset)

        part = content[offset:offset + size_to_upload]
        result = bucket.upload_part(key, upload_id, part_number, part)
        parts.append(
            oss2.models.PartInfo(part_number,
                                 result.etag,
                                 size=size_to_upload,
                                 part_crc=result.crc))

        offset += size_to_upload
        part_number += 1

        ratio = offset * 100 // total_size
        print('\r', end='')
        print('multipart upload progress: {}%: '.format(ratio),
              '▋' * (ratio // 2),
              end='')
        sys.stdout.flush()

    timecost = time.time() - begin
    print('averge speed {} KB/s\n'.format(
        math.ceil(total_size / 1024 / timecost)))

    # 完成分片上传
    bucket.complete_multipart_upload(key, upload_id, parts)
    return None


def accelerate_download_url(url):
    # https://openmmlab-deploee.oss-cn-shanghai.aliyuncs.com/model/mmdet3d-voxel/pointpillars-ort1.8.1-gvQ78l.zip
    from_domain = 'openmmlab-deploee.oss-cn-shanghai.aliyuncs.com'
    to_domain = 'openmmlab-deploee.oss-accelerate.aliyuncs.com'
    return url.replace(from_domain, to_domain)


def upload_param():
    # login
    # jsonobj = {
    #     'OSS_TEST_ACCESS_KEY_ID': 'LTAI5t5eMPYGKGtXuQJ4TQ9A',
    #     'OSS_TEST_ACCESS_KEY_SECRET': '7Kh74tpNocDnR6FelMfB5ZodcUTtHs',
    #     'OSS_TEST_BUCKET': 'deploee',
    #     'OSS_TEST_ENDPOINT': 'oss-cn-shanghai.aliyuncs.com'
    # }
    jsonobj = {
        'OSS_TEST_ACCESS_KEY_ID': 'LTAI5tHsCF8Z8sf2nYVEaRtK',
        'OSS_TEST_ACCESS_KEY_SECRET': 'Spkho47sJ4gNDnOz1LQCSvuOPlJEQq',
        'OSS_TEST_BUCKET': 'openmmlab-deploee',
        'OSS_TEST_ENDPOINT': 'oss-cn-shanghai.aliyuncs.com'
    }
    return jsonobj['OSS_TEST_ACCESS_KEY_ID'], jsonobj[
        'OSS_TEST_ACCESS_KEY_SECRET'], jsonobj['OSS_TEST_BUCKET'], jsonobj[
            'OSS_TEST_ENDPOINT']


def download_cache_url(url: str):
    return 'http://10.1.52.36:10009/getFile?url={}'.format(url)


def sdk_url(filename):
    _, __, bucket_name, endpoint = upload_param()
    download_url = 'https://{}.{}/sdk/{}.zip'.format(bucket_name, endpoint,
                                                     quote(filename))
    return download_url


def oss_url(prefix, filename, suffix):
    _, __, bucket_name, endpoint = upload_param()
    download_url = 'https://{}.{}/{}{}{}'.format(bucket_name, endpoint, prefix,
                                                 quote(filename), suffix)
    return download_url


def oss_sign_url(prefix, suffix):
    randstr = ''.join(random.sample(string.ascii_letters + string.digits, 6))

    key = prefix + randstr + suffix

    access_key_id, access_key_secret, bucket_name, endpoint = upload_param()
    bucket = oss2.Bucket(oss2.Auth(access_key_id, access_key_secret),
                         'https://{}'.format(endpoint), bucket_name)

    headers = dict()
    upload_url = bucket.sign_url('PUT',
                                 key,
                                 3600,
                                 slash_safe=True,
                                 headers=headers)
    download_url = 'https://{}.{}/{}{}{}'.format(bucket_name, endpoint, prefix,
                                                 quote(randstr), suffix)
    return upload_url, download_url


def oss_upload(prefix, filename, suffix, content):
    key = prefix + filename + suffix

    length = len(content)
    if content is None or length < 1:
        return '', Exception(message='abnormal content length 0')

    access_key_id, access_key_secret, bucket_name, endpoint = upload_param()
    error = None
    try:
        bucket = oss2.Bucket(oss2.Auth(access_key_id, access_key_secret),
                             endpoint, bucket_name)

        multipart_threshold = 2 * 1024 * 1024
        if length > multipart_threshold:
            error = oss_upload_multipart(bucket, key, content)
        else:
            error = oss_upload_simple(bucket, key, content)

    except Exception as e:
        logger.error('upload fail {}'.format(e))
        error = 'upload failed'
    finally:

        download_url = 'https://{}.{}/{}{}{}'.format(bucket_name,
                                                     endpoint, prefix,
                                                     quote(filename), suffix)
        return download_url, error


def oss_upload_with_hash(prefix, suffix, content):
    if content is None or len(content) == 0:
        return None, 'input content empty'

    md5 = hashlib.md5()

    if type(content) is str:
        md5.update(content.encode('utf8'))
    else:
        md5.update(content)
    filename = md5.hexdigest()[0:6]

    url = oss_url(prefix, filename, suffix)
    try:
        with request.urlopen(url) as f:
            if f.status == 200:
                # already exists, skip upload
                logger.info('url already exists {}'.format(url))
                return url, None
    except Exception:
        pass

    url, upload_fail = oss_upload(prefix, filename, suffix, content)
    if upload_fail is not None:
        return url, 'process_success upload fail'
    return url, None


def oss_download(directory, url, use_cache=True):
    localpath = ''
    os.makedirs(directory, exist_ok=True)
    localpath = os.path.join(directory, url[url.rfind('/') + 1:])

    error = None

    if use_cache:
        cache_url = 'http://10.1.52.36:10009/getFile?url={}'.format(url)
        try:
            with request.urlopen(cache_url) as f:
                if f.status == 200:
                    # use cache
                    os.system(
                        'wget -N --quiet --show-progress {} -O {}'.format(
                            cache_url, localpath))

                    if not os.path.exists(localpath):
                        error = 'cache url download failed {}'.format(
                            cache_url)

                    return localpath, error
        except Exception:
            pass

    try:
        with request.urlopen(url) as f:
            pass
    except Exception:
        logger.error('{} not exist'.format(url))
        return localpath, '下载异常'

    try:
        os.system('wget -N --quiet --show-progress {} -O {}'.format(
            url, localpath))

        if not os.path.exists(localpath):
            error = 'url download failed {}'.format(url)
    except Exception as e:
        logger.error('download faild{}'.format(e))
        error = 'download failed'
    finally:
        return localpath, error


if __name__ == '__main__':
    _bytes = None
    import sys
    # fasta_path1 = '/share/appspace_data/shared_groups/yzwl_wangxy_wangxy_konghj_chenyf/T2TID_AA_fasta'
    # fasta_path2 = '/share/appspace_data/shared_groups/yzwl_wangxy_wangxy_konghj_chenyf/T2TID_CDS_fasta'
    file_extension = '.zip'
    # for path in [fasta_path1, fasta_path2]:
    #     for filename in os.listdir(path):
    #         if not filename.endswith(file_extension):
    #             continue

    #         filepath = os.path.join(path, filename)
            
    with open("seed_repo_09_24.zip", 'rb') as f:
        _bytes = f.read()
            
    #         filename_without_extension, _ = os.path.splitext(filename)
    #         # print(path, filename_without_extension, file_extension)
    print(oss_upload('seedllm/repo', "seed_repo_09_24", file_extension, _bytes))
            # pdb.set_trace()
    # oss_upload('seedllm/', filename_without_extension, file_extension, _bytes)
