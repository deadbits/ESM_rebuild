#!/usr/bin/env python
##
# Elasticsearch-Mongo rebuilder
# https://github.com/deadbits/ESM_rebuild
#
# author: adam m. swanda
# http://www.deadbits.org
##

import os
import sys
import json
import time
import argparse
import pymongo
import elasticsearch.helpers as es_help

from elasticsearch import Elasticsearch


class ES:
    def __init__(self, server, index):
        self.client = Elasticsearch(server)
        self.index = index


    def create_index(self):
        self.client.indices.create(self.index)
        if not self.client.indices.exists(self.index):
            return False
        return True


    def delete_index(self):
        if not self.client.indices.exists(self.index):
            fatal('Elasticsearch index %s does not exist to be deleted.' % self.index)
        self.client.indices.delete(self.index)
        if self.client.indices.exists(self.index):
            return False
        return True


    def validate_mapping_index(self, mapping, doc_type):
        if mapping.keys()[0] != doc_type:
            fatal('Doctype does not match provide mapping key\n- Mapping: %s\n- Doctype: %s' % (mapping.keys()[0], doc_type))


    def put_mappings(self, map_path, doc_type):
        data = None
        result = {self.index: {'mappings': {}}}
        try:
            with open(map_path, 'rb') as fp:
                data = json.load(fp)
        except Exception as err:
            fatal('Caught exception while reading mapping file:\n%s' % str(err))

        self.validate_mapping_index(data, doc_type)

        try:
            self.client.indices.put_mapping(index=self.index, doc_type=doc_type, body=data)
            result = self.client.indices.get_mapping(index=self.index)
        except Exception as err:
            fatal('Caught exception while adding mapping:\n%s' % str(err))

        return result


    def bulk_insert(self, actions):
        try:
            es_help.bulk(self.client, actions)
        except Exception as err:
            fatal('Caught exception while bulk inserting documents:\n%s' % str(err))
        return True


class Mongo:
    def __init__(self, host, database):
        try:
            self.conn = pymongo.MongoClient(host)
        except Exception as err:
            fatal('Caught exception while connecting to MongoDB:\n%s' % str(err))
        self.db = self.conn[database]


    def iter_search(self, collection, offset=0, size=500):
        docs = []
        coll = self.db[collection]
        docs = list(coll.find({}).sort([('_id', 1)]).limit(size).skip(offset))
        return docs


    def get_documents(self, index, collection, size, verbose):
        run = True
        offset = 0
        bulk_actions = []
        while run:
            if verbose:
                print '\t- Fetching documents %d to %d' % (offset, (offset + size))
            docs = self.iter_search(collection, offset, size)
            run = False
            offset += len(docs)
            run = len(docs) == size
            for doc in docs:
                doc_id = str(doc['_id'])
                doc.pop('_id')
                action = ({'_index': index, '_type': collection, '_id': doc_id, '_source': doc})
                bulk_actions.append(action)
        return bulk_actions


def fatal(msg):
    print 'error: %s' % msg
    sys.exit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='es_rebuild.py')
    task_group = parser.add_argument_group('actions')
    es_group = parser.add_argument_group('elasticsearch')
    mongo_group = parser.add_argument_group('mongodb')

    task_group.add_argument('-R', '--rebuild',
        help='delete index and recreate',
        action='store_true')

    task_group.add_argument('-P', '--push',
        help='index documents from MongoDB collections',
        action='store_true')

    task_group.add_argument('-M', '--mappings',
        help='add document mappings to index',
        action='store_true')

    task_group.add_argument('-v', '--verbose',
        help='verbose messages during MongoDB retrieval (noisy)',
        action='store_true',
        default=False)

    es_group.add_argument('-n', '--node',
        help='node hostname or IP address',
        action='store',
        required=True)

    es_group.add_argument('-i', '--index',
        help='index name',
        action='store',
        required=True)

    es_group.add_argument('-d', '--doctypes',
        help='list of doctypes (MUST match MongoDB collection names)',
        nargs='+',
        action='store')

    es_group.add_argument('-p', '--mappath',
        help='directory path to doctype mappings',
        action='store')

    mongo_group.add_argument('-H', '--host',
        help='hostname or IP address',
        action='store')

    mongo_group.add_argument('-D', '--db',
        help='database name',
        action='store')

    mongo_group.add_argument('-s', '--size',
        help='number of documents to fetch per search iteration',
        action='store',
        type=int,
        default=500)

    args = parser.parse_args()

    # collect arguments
    rebuild = True if args.rebuild else False
    push_docs = True if args.push else False
    update_mappings = True if args.mappings else False
    es_index = args.index if args.index else fatal('No ElasticSearch index specified.')
    es_server = args.node if args.node else fatal('No ElasticSearch server speecified.')
    verbose = True if args.verbose else False
    map_path = args.mappath if args.mappath else None
    mongo_host = args.host if args.host else None
    mongo_db = args.db if args.db else None
    mongo_size = args.size
    doc_types = args.doctypes if args.doctypes else []

    # quick syntax checking
    if not rebuild and not push_docs and not update_mappings:
        fatal('No task selected. Must use any of: --rebuild, --push, --mappings')

    if update_mappings and map_path is None:
        fatal('Update mappings selected without specifying path to document mapping JSON file.')
    if update_mappings:
        if not os.path.exists(map_path):
            fatal('Mappings file specified does not exist. (%s)' % map_path)

    if push_docs and (mongo_host is None or mongo_db is None or len(doc_types) == 0):
        fatal('Rebuild selected without specifying MongoDB host, database name, or ES doctype.')

    # display all options for user to confirm before running
    print '\n[Execution Options]'
    print 'Elasticsearch:'
    print '\tES Node:          \t%s' % es_server
    print '\tES Index:         \t%s' % es_index
    if doc_types:
        print '\tDoc Types:        \t%s' % doc_types
    if update_mappings:
        print '\tMappings Path:     \t%s' % map_path

    print 'Tasks:'
    print '\tRebuild Index:    \t%s' % rebuild
    print '\tUpdate Mappings:  \t%s' % update_mappings
    print '\tIndex Mongo Docs: \t%s' % push_docs
    print '\tVerbose Mongo:    \t%s' % verbose

    if rebuild:
        print 'MongoDB:'
        print '\tServer:           \t%s' % mongo_host
        print '\tDatabase:         \t%s' % mongo_db
        print '\tCollections:      \t%s' % doc_types
        print '\tIteration Size:   \t%d' % mongo_size

    print '\n**IMPORTANT**:'
    print 'Please review the options displayed above and confirm that you wish to proceed.'
    print 'There is the potential of data loss if options are not selected carefully!'
    answer = raw_input('Proceed [y/n]: ').strip()
    if answer.lower() == 'n' or answer.lower() == 'no':
        print '\nYou have selected not to continue execution. Exiting ...'
        sys.exit(0)
    elif answer.lower() == 'y' or answer.lower() == 'yes':
        print '\n'
        print '[-] Starting execution in 5 seconds ...'
        time.sleep(5)
    else:
        fatal('Invalid choice. Please enter one of: yes, y, no, n')

    es = ES(es_server, es_index)

    # perform the work
    if rebuild:
        print '\n+ Rebuilding Index:'
        print '\t- Deleting existing index %s ...' % es_index
        if not es.delete_index():
            fatal('error: failed to delete index.')
        if not es.create_index():
            fatal('error: failed to create index.')

    if update_mappings:
        print '\n+ Update Mappings:'
        for _type in doc_types:
            if os.path.exists(map_path + '/%s.json' % _type):
                map_file = '%s/%s.json' % (map_path, _type)
                print '\t- Sending mapping for doctype %s' % _type
                result = es.put_mappings(map_file, _type)
                if len(result[es_index]['mappings']) == 0:
                    fatal('error: failed to add new mappings.\n%s' % result)
                print '\t\t* Mapping accepted'
            else:
                print 'error: no mapping found for doctype %s\npath: %s/%s.json' % (_type, map_path, _type)

    if push_docs:
        mongo = Mongo(mongo_host, mongo_db)
        print '\n+ Index MongoDB Data:'
        all_docs = []
        for _type in doc_types:
            print '\t- Fetching documents from collection %s ...' % _type
            docs = mongo.get_documents(es_index, _type, mongo_size, verbose)
            print '\t\t- Got %d documents' % len(docs)
            for i in docs:
                all_docs.append(i)
        print '\t- Starting Elasticsearch bulk index action ...'
        es.bulk_insert(all_docs)
        print '\t\t* Successfully indexed all MongoDB documents in Elasticsearch!'

    print '\n[*] Complete! :)'
