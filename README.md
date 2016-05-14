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
* [Caveats](#caveats)
* [Disclaimer](#disclaimer)

## Description
Being pretty new to Elasticsearch, and only running a very basic architecture, I find myself having to re-index documents a lot. 

In the early stages of adding new data sources you will typically create an index, add mappings for your document types, then index some data. Oh, you need to update mappings for existing fields? Go ahead and delete your index, edit and upload the new mapping, then re-index all of that same data.

This script tries to alleviate some of that process by automating:
- Deleting and recreating a specified index
- Adding prebuilt mappings for your document types
- Indexing data persisted on a MongoDB instance

Each of these tasks can be performed individually or all at once if you need to completely rebuild.


## Examples
### All Options
Delete and re-create index named `my_index`, put the document mappings from `my_mappings.json` into `my_index`, fetch all Mongo docs from collections `posts` and `comments`, and then index the docs in ES as doctypes of the same name:  
- `python esm_rebuild.py --rebuild --push --mappings --node 127.0.0.1 --index my_index --doctypes "posts, comments" --host mongohost --db mongo_database --mapfile my_mappings.json`

### Index MongoDB data
Index all documents from the MongoDB collections `posts` and `comments` to an Elasticsearch instance as doctypes `posts` and `comments`:  
- `python esm_build.py --push --node 127.0.0.1 --index my_index --doctypes "posts, comments" --host mongohost --db mongo_database`

### Recreate index and add mappings
Recreate index and add any document mappings from my_mappings.json file:  
- `python esm_rebuild.py --rebuild --mappings --node 127.0.0.1 --index my_index --mapfile my_mappings.json`

### Recreate index
Simply delete an existing index and then create an index of the same name:
- `python esm_rebuild.py --rebuild --node 127.0.0.1 --index my_index`


## Caveats
- Your document mappings must exist in a single JSON file
- Your Elasticsearch doctype names must match the corresponding MongoDB collection names
- This script does not take into account any index creation options. It simply creates a new index with the provided name.


## Disclaimer 
**I DO NOT RECOMMEND using this in any type of production environment. The script was written very quickly and is meant for small, local ES instances you are playing around with. There is the potential for data loss if the script is used incorrectly. By using this script you acknowledge you are doing so of your own volition and I am not responsible for any data loss or other problems that may arise from it's use.**
