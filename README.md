# ESM rebuild
High level client for rebuilding Elasticsearch indexes from MongoDB persisted data.

## Table of Contents
====================
* [Description](#description)
* [Examples](#examples)
    * [Complete rebuild](#all-options)
    * [Index MongoDB data](#index-mongodb-data)
    * [Rebuild and add mappings](#recreate-index-and-add-mappings)
    * [Recreate an index](#recreate-index)
    * [Output](#output)
        * [Help](#help)
        * [Confirmation](#pre-execution)
        * [Running](#running)
* [Caveats](#caveats)
* [Disclaimer](#disclaimer)

## Description
Being pretty new to Elasticsearch, and only running a very basic architecture, I find myself having to re-index documents a lot. 

In the early stages of adding new data sources you will typically create an index, add mappings for your document types, then index some data. Oh, you need to update mappings for existing fields? Go ahead and delete your index, edit and upload the new mapping, then re-index all of that same data. (yes, I know there are [other ways](https://www.elastic.co/blog/changing-mapping-with-zero-downtime) to do this.)

This script tries to alleviate some of that process by automating:
- Deleting and recreating a specified index
- Adding prebuilt mappings for your document types
- Indexing data persisted on a MongoDB instance
    - Mongo docID is used as the Elasticsearch `_id` value

Each of these tasks can be performed individually or all at once if you need to completely rebuild.


## Examples
### All Options
Delete and re-create index named `my_blog`, add mappings from `--mappath` directory to `my_blog` index, fetch all Mongo docs from collections `posts` and `comments`, and then index the docs in ES as doctypes of the same name using a bulk API call:  
- `python esm_rebuild.py --rebuild --push --mappings --node 127.0.0.1 --index my_blog --doctypes "posts, comments" --host mongohost --db mongo_database --mappath /path/to/mapfiles`

### Index MongoDB data
Index all documents from the MongoDB collections `posts` and `comments` to an Elasticsearch instance as doctypes `posts` and `comments`:  
- `python esm_build.py --push --node 127.0.0.1 --index my_blog --doctypes "posts, comments" --host mongohost --db mongo_database`

### Recreate index and add mappings
Recreate index and add any document mappings from my_mappings.json file:  
- `python esm_rebuild.py --rebuild --mappings --node 127.0.0.1 --index my_blog --mappath /path/to/mapfiles`

### Recreate index
Simply delete an existing index and then create an index of the same name:
- `python esm_rebuild.py --rebuild --node 127.0.0.1 --index my_blog`

### Output

#### Help

```
usage: esm_rebuild.py [-h] [-R] [-P] [-M] [-v] -n NODE -i INDEX
                     [-d DOCTYPES [DOCTYPES ...]] [-p MAPPATH] [-H HOST]
                     [-D DB] [-s SIZE]

optional arguments:
  -h, --help            show this help message and exit

actions:
  -R, --rebuild         delete index and recreate
  -P, --push            index documents from MongoDB collections
  -M, --mappings        add document mappings to index
  -v, --verbose         verbose messages during MongoDB retrieval (noisy)

elasticsearch:
  -n NODE, --node NODE  node hostname or IP address
  -i INDEX, --index INDEX
                        index name
  -d DOCTYPES [DOCTYPES ...], --doctypes DOCTYPES [DOCTYPES ...]
                        list of doctypes (MUST match MongoDB collection names)
  -p MAPPATH, --mappath MAPPATH
                        directory path to doctype mappings

mongodb:
  -H HOST, --host HOST  hostname or IP address
  -D DB, --db DB        database name
  -s SIZE, --size SIZE  number of documents to fetch per search iteration
```

#### Pre-execution
Before the script runs it's tasks you will see the output below and be prompted to confirm the options are correct. After you confirm there is a 5 second sleep time before it does run, just incase you keep to quickly Ctrl+C out of there.

```
[Execution Options]
Elasticsearch:
    ES Node:            127.0.0.1
    ES Index:           my_blog
    Doc Types:          ['posts, comments']
    Mapping File:       /Users/adam/Desktop/mappings
Tasks:
    Rebuild Index:      True
    Update Mappings:    True
    Index Mongo Docs:   True
MongoDB:
    Server:             127.0.0.1
    Database:           blog
    Collections:        ['posts, comments']

**IMPORTANT**:
Please review the options displayed above and confirm that you wish to proceed.
Proceed [y/n]: n

You have selected not to continue execution. Exiting ...
```

#### Running
Each stage provides status messages and attempts to catch any errors that might prevent the rest of the tasks from running correctly:

```
[-] Starting execution in 5 seconds ...

+ Rebuilding Index:
    - Deleting existing index my_blog ...
    * Recreated index my_blog
    
+ Update Mappings:
    - Sending mapping for doctype posts
        * Mappings accepted
    - Sending mapping for doctype comments
        * Mapping accepted

+ Index MongoDB Data:
    - Fetching documents from collection posts ...
        - Got 149 documents
    - Fetching documents from collection comments
        - Got 25 documents
    - Starting Elasticsearch bulk index action ...
        * Successfully indexed all MongoDB documents in Elasticsearch!

[*] Complete! :)
```

You can use the `--verbose` argument to see how far along the Mongo retrieval process is. This will print a message for every search iteration so it can be very noisy depending on your `--size` argument and the size of your collections.

## Caveats
- The --mappath argument requires a directory containing 1 JSON file per doctype where the filename is your doctype. For example, specifying the doctype `posts` and `--mappath mappings` will look for `mappings/posts.json`.
- Your Elasticsearch doctype names must match the corresponding MongoDB collection names
- This script does not take into account any index creation options. It simply creates a new index with the provided name.


## Disclaimer 
**I DO NOT RECOMMEND using this in any type of production environment. The script was written very quickly and is meant for small, local ES instances you are playing around with. There is the potential for data loss if the script is used incorrectly. By using this script you acknowledge you are doing so of your own volition and I am not responsible for any data loss or other problems that may arise from it's use.**

