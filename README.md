# Elasticsearch integration pack

Pack provides many operations helping to manage your Elasticsearch indices and snapshots.

## Configuration

Copy the example configuration in [elasticsearch.yaml.example](./elasticsearch.yaml.example)
to `/opt/stackstorm/configs/elasticsearch.yaml` and edit as required.

It must contain:

* ``host`` - Host where Elasticsearch is running
* ``port`` - Elasticsearch port - default 9200
* ``query_window`` - Rolling window size in seconds. Default 30s
* ``query_string`` - Query string
* ``cooldown_multiplier`` - Multiple of query window to cooldown after successful hit. Default 2
* ``count_threshold`` - Minimum number of hits before emitting trigger. Default 5
* ``index`` - Index to query - e.g. 'logstash*'

You can also use dynamic values from the datastore. See the
[docs](https://docs.stackstorm.com/reference/pack_configs.html) for more info.

**Note** : When modifying the configuration in `/opt/stackstorm/configs/` please
           remember to tell StackStorm to load these new values by running
           `st2ctl reload --register-configs`

## Curator based actions

These actions operate similar to [curator](https://www.elastic.co/guide/en/elasticsearch/client/curator/current/actions.html) for Elasticsearch.

Action | Description
------ | -----------
**cluster.cluster_routing** | This action changes the shard routing allocation for the selected indices.
**indices.alias** | Add indices to or remove them from aliases.
**indices.allocation** | Set routing allocation based on tags.
**indices.close** | Close indices.
**indices.create_index** | Create index.
**indices.delete_indices** | Delete indices.
**indices.forcemerge** | Perform a forceMerge on the selected indices, merging them to max_num_segments per shard.
**indices.index_settings** | Update the specified index settings for the selected indices.
**indices.open** | Opens the seleted indices.
**indices.optimize** | Optimizes the selected indices.
**indices.reindex** | Reindex selected indices.
**indices.replicas** | Set replica count per shard.
**indices.rollover** | Rolls an alias over to a new index when the existing index is considered to be too large or too old.
**indices.show** | Show indices.
**indices.shrink** | Shrink indices.
**indices.snapshot** | Capture snapshot of indices.
**search.body** | Search query using request body.
**search.q** | Search query using query string as a parameter.
**snapshots.delete_snapshots** | Delete selected snapshots from 'repository'.
**snapshots.restore** | Restore all indices in the most recent snapshot with state SUCCESS.
**snapshots.show** | Show snapshots.

Actions invocation parameters will be described further. But for more detailed description what each action actually does please also refer to the [curator docs](http://www.elastic.co/guide/en/elasticsearch/client/curator/current/), it is more in-depth.

### Common parameters

These parameters include general options such as elasticsearch host, port etc.

Parameter | Description | Default
------------ | ------------ | ------------
**host** | Specifies Elasticsearch host to connect to. | `none`
**url_prefix** | Specifies Elasticsearch http url prefix. | `/`
**port** | Specifies port remote Elasticsearch instance is running on. | `9200`
**use_ssl** | Set to `true` to connect to Elasticsearch through SSL. | `false`
**http_auth** | Colon separated string specifying HTTP Basic Authentication. | `none`
**master_only** | Set to `true` to allow operation only on elected master. If a host you connect to is not a master node then the operation will fail. | `false`
**timeout** | Specifies Elasticsearch operation timeout in seconds. | `600`
**log_level** | Specifies log level \[critical\|error\|warning\|info\|debug\]. | `warn`
**dry_run** | Set to `true` to enable *dry run* mode not performing any changes. | `false`

### Filtering the list of indices and/or snapshots

Please see details on how to select indices or snapshots using filters:

  https://www.elastic.co/guide/en/elasticsearch/client/curator/current/filters.html

## Search actions

Search actions perform a specified query in Elasticsearch. There are two search actions available: **search.q** and **search.body**. The first one takes a query string (given in lucene syntax), while the former allows to perform more sophisticated searches using Elasticsearch query DSL.

Both search actions use the same *common parameters* as curator based actions.

### search.q specific parameters

This action is enhanced with *index selection* parameters to simplify indices matching.

Parameter | Description
------------ | ------------
**q** | Query in the Lucene query string syntax (**required**).
**df** | The default field to use when no field prefix is defined within the query.
**default_operator** | The default operator to be used, can be AND or OR. Defaults to OR.
**from** | The starting from index of the hits to return. Defaults to 0.
**size** | The number of hits to return. Defaults to 10.
**pretty** | Set to `true` to pretty print JSON response.

### search.body specific parameters

Parameter | Description
------------ | ------------
**body** | The search definition using the Query DSL (**required**).
**indices** | A comma-separated list of index names to search. Defaults to `"_all"`.
**from** | The starting from index of the hits to return. Defaults to 0.
**size** | The number of hits to return. Defaults to 10.
**pretty** | Set to `true` to pretty print JSON response.

## Usage and examples

Performing *curator operations* on indices or snapshots **at least one** filtering parameter must be specified. This's a generic rule applied to all of curator actions except. However *show* actions can be invoked without any filtering parameters, in this case *show*  actions will display full list of indices or snapshots.

Now let's have a look at a few invocation examples.

### Showing and deleting indices

* Show indices older than 2 days:
```
st2 run elasticsearch.indices.show host=elk older_than=2 timestring=%Y.%m.%d
```
Shows this on my node:
```json
{
    "result": null,
    "exit_code": 0,
    "stderr": "",
    "stdout": "logstash-2015.05.02
logstash-2015.05.04
"
}
```
* Delete all indices matching *^logstash.\**:

```
st2 run elastic.indices.delete host=elk prefix=logstash
```

### Snapshot operations

* Create a snapshot of indices  based on time range criteria:
```
st2 run elasticsearch.indices.snapshot host=elk repository=my_backup newer_than=20 older_than=10 timestring=%Y.%m.%d
```

This command will create a snapshot of indices newer than 20 days and older than 10 days. Notice that filtering parameters of snapshot command *apply to indices* not to snapshots. That's why it's important not to mess it up. For example, the timestring parameter when created by curator with default options has a different time scheme.

* Delete specific snapshots:
```
st2 run elasticsearch.snapshots.delete host=elk repository=my_backup snapshot=curator-20150506155615,curator-20150506155619
```
* Delete all snapshots:
```
st2 run elasticsearch.snapshots.delete host=elk repository=my_backup all_indices=true
```

### Querying Elasticsearch

| Return Code | Reason                                                      |
|-------------|-------------------------------------------------------------|
| `0`         | Successful search (total hits > 0 or returned hits > 0)     |
| `1`         | No documents found (total hits == 0)                        |
| `2`         | `hits.total` not present in response and returned hits == 0 |
| `99`        | Other execution errors                                      |

Let's look at a few examples:

* Run query using DSL syntax:
```
st2 run elasticsearch.search.body host=elk body='{"query":{"match_all":{}}}' pretty=true
```

* Run query using URI syntax where **q** is a Lucene string:
```
st2 run elasticsearch.search.q host=elk q='message:my_log_event' prefix=logstash
```

## License and Authors

* Author:: StackStorm (st2-dev) (<info@stackstorm.com>)
* Author:: Denis Baryshev (<dennybaa@gmail.com>)
