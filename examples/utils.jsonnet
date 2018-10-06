{
  toEntries(obj): [{ Key: k, Value: obj[k] } for k in std.objectFields(obj)],
}
