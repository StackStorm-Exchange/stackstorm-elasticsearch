# CREATE_INDEX
st2 run -d elasticsearch.indices.create_index host=elk name=orange-55 extra_settings='{ "settings" : {"number_of_shards" : 3, "number_of_replicas": 0}, "mappings": {"type1": {"properties": { "field1": {"type": "string", "index": "not_analyzed"}}}}}' | sed -e 's/\\n/\n/g' | sed -e 's/\\"/"/g'
st2 run -d elasticsearch.indices.create_index host=elk name=apple-14 extra_settings='{ "settings" : {"number_of_shards" : 1, "number_of_replicas": 0}, "mappings": {"type1": {"properties": { "field1": {"type": "string", "index": "not_analyzed"}}}}}' | sed -e 's/\\n/\n/g' | sed -e 's/\\"/"/g'

# ALIAS
st2 run -d elasticsearch.indices.alias host=elk name='apple' extra_settings='{}' add='{"filtertype": "pattern", "kind": "prefix", "value": "apple-14"}' | sed -e 's/\\n/\n/g' | sed -e 's/\\"/"/g'

# ALLOCATION
st2 run -d elasticsearch.indices.allocation host=elk key=tag | sed -e 's/\\n/\n/g' | sed -e 's/\\"/"/g'

# CLOSE
st2 run -d elasticsearch.indices.close host=elk filters='{"filtertype": "pattern", "kind": "prefix", "value": "app"}'  | sed -e 's/\\n/\n/g' | sed -e 's/\\"/"/g'

# SHOW
st2 run -d elasticsearch.indices.show host=elk dry_run=true | sed -e 's/\\n/\n/g' | sed -e 's/\\"/"/g'

# OPEN
st2 run -d elasticsearch.indices.open host=elk filters='{"filtertype": "opened"}' | sed -e 's/\\n/\n/g' | sed -e 's/\\"/"/g'

# SHOW
st2 run -d elasticsearch.indices.show host=elk dry_run=true | sed -e 's/\\n/\n/g' | sed -e 's/\\"/"/g'

# FORCEMERGE
st2 run -d elasticsearch.indices.forcemerge host=elk max_num_segments=1 filters='{"filtertype": "pattern", "kind": "prefix", "value": "apple-14"}' | sed -e 's/\\n/\n/g' | sed -e 's/\\"/"/g'

# INDEX_SETTINGS
st2 run -d elasticsearch.indices.index_settings host=elk index_settings='{"index": {"refresh_interval": "5s"}}' | sed -e 's/\\n/\n/g' | sed -e 's/\\"/"/g'

# REINDEX
st2 run -d elasticsearch.indices.reindex host=elk request_body='{"source": {"index": ["index1", "index2", "index3"]}, "dest": {"index": "apple-14"}}' | sed -e 's/\\n/\n/g' | sed -e 's/\\"/"/g'

# REPLICAS
st2 run -d elasticsearch.indices.replicas count=3 host=elk filters='{"filtertype": "pattern", "kind": "suffix", "value": "14"}' | sed -e 's/\\n/\n/g' | sed -e 's/\\"/"/g'

# ROLLOVER
st2 run -d elasticsearch.indices.rollover host=elk name='apple' conditions='{"max_age": "1d"}'

# SHOW
st2 run -d elasticsearch.indices.show host=elk | sed -e 's/\\n/\n/g' | sed -e 's/\\"/"/g'

# SHRINK
# st2 run -d elasticsearch.indices.shrink host=elk filters='{"filtertype": "pattern", "kind": "prefix", "value": "orange"}' | sed -e 's/\\n/\n/g' | sed -e 's/\\"/"/g'

# SNAPSHOT
# st2 run -d elasticsearch.indices.snapshot host=elk | sed -e 's/\\n/\n/g' | sed -e 's/\\"/"/g'

# DELETE_INDICES
st2 run -d elasticsearch.indices.delete_indices host=elk filters='{"filtertype": "pattern", "kind": "prefix", "value": "app"}' | sed -e 's/\\n/\n/g' | sed -e 's/\\"/"/g'
st2 run -d elasticsearch.indices.delete_indices host=elk filters='{"filtertype": "pattern", "kind": "prefix", "value": "ora"}' | sed -e 's/\\n/\n/g' | sed -e 's/\\"/"/g'
