import json
import veracium.store.schema_version as sv
print(json.dumps({v:sorted(sv.accepted_digests(v)) for v in range(1,17)}))
