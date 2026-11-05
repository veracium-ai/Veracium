import sys,inspect
from veracium.store.migration import migrate_store
r=migrate_store(sys.argv[1])
print(getattr(r,'resulting_version',r))
