import json
import traceback
import _jsonnet

def obj_iterate(obj, f):
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


def handler(event, context):
  params = event["params"]
  templateParameterValues = event["templateParameterValues"]
  fragment = event["fragment"]

  preamble = \
    f"local account_id = {event['accountId']};\n" \
    f"local params = {json.dumps(templateParameterValues)};\n" \
    f"local region = \"{event['region']}\";\n" \
    f"local template = {event['fragment']};\n" \
    + "\n".join(
      f"local {name} = {value};" for name, value in params.items()
    )

  try:
    def process(code):
      code = preamble + "\n" + code
      print(code)
      r = _jsonnet.evaluate_snippet("snippet", code)
      return json.loads(r)

    output = obj_iterate(fragment, process)

    return {
      "requestId": event["requestId"],
      "status": "success",
      "fragment": output
    }

  except Exception as e:
    traceback.print_exc()
    return {
      "requestId": event["requestId"],
      "status": "failure",
      "errorMessage": str(e)
    }

