import boto3
import botocore
import io
import json
import traceback
import _jsonnet

from pathlib import Path
from zipfile import ZipFile
from urllib.parse import urlparse


def download_from_s3(s3_url, fileobj):
    """Download a file from a url of the form s3:///bucket/path/to/key
    to download_path."""

    u = urlparse(s3_url)
    bucket_name = u.netloc
    key = u.path[1:]  # skip the leading /

    s3 = boto3.resource('s3')

    try:
        s3.Bucket(bucket_name).download_fileobj(key, fileobj)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == '404':
            print("The object does not exist.")
        else:
            raise


def obj_iterate(obj, f):
    """Walk through a dict of dicts, lists and strings applying f to all
    strings that start with #!jsonnet."""

    if isinstance(obj, dict):
        for k in obj:
            obj[k] = obj_iterate(obj[k], f)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            obj[i] = obj_iterate(v, f)
    elif isinstance(obj, str):
        if obj.startswith("#!jsonnet"):
            obj = f(obj)
    return obj


def make_import_callback(libzip):
    """Create a callback that reads into a zipfile."""

    def import_callback(dir, rel):
        """Import callback for jsonnet runtime."""

        full_path = Path(dir, rel).as_posix()
        try:
            content = libzip.read(full_path).decode()
            return full_path, content
        except KeyError as e:
            raise RuntimeError(*e.args)

    return import_callback


def handler_prime(event, context):
    region = event['region']
    accountId = event['accountId']
    template = event['fragment']
    templateParameterValues = event['templateParameterValues']

    if 'JsonnetLibraryUri' in template:
        jsonnetLibraryUri = template['JsonnetLibraryUri']

        buf = io.BytesIO()
        download_from_s3(jsonnetLibraryUri, buf)
        buf.seek(0)
        zipfile = ZipFile(buf)
        import_callback = make_import_callback(zipfile)
    else:
        import_callback = None

    preamble = \
        f"local region = {json.dumps(region)};\n" \
        f"local accountId = {accountId};\n" \
        f"local template = {json.dumps(template)};\n" \
        f"local templateParams = {json.dumps(templateParameterValues)};"

    def process(code):
        code = preamble + "\n" + code

        if import_callback:
            r = _jsonnet.evaluate_snippet(
              "snippet", code,
              import_callback=import_callback
            )
        else:
            r = _jsonnet.evaluate_snippet("snippet", code)

        return json.loads(r)

    output = obj_iterate(template, process)

    if 'JsonnetLibraryUri' in template:
        del template['JsonnetLibraryUri']

    return {
        "requestId": event["requestId"],
        "status": "success",
        "fragment": output
    }


def handler(event, context):
    requestId = event['requestId']

    try:
        return handler_prime(event, context)
    except Exception as e:
        traceback.print_exc()
        return {
            "requestId": requestId,
            "status": "failure",
            "errorMessage": str(e)
        }
