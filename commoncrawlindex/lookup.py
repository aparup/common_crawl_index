# Copyright [2012] [Triv.io, Scott Robertson]
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
"""Looks up URLs in the Common Crawl URL Index.

Usage: %s <url prefix>

Prints a list of URLs that match the specified prefix along with metadata.
"""

import struct
import sys

import boto

import commoncrawlindex
from commoncrawlindex import pbtree


class BotoMap(object):
  def __init__(self, bucket, key_name, access_key=None, access_secret=None):
    if access_key and access_secret:
      self.conn = boto.connect_s3(access_key, access_secret)
    else:
      self.conn = boto.connect_s3(anon=True)
    bucket = self.conn.lookup(bucket)
    self.key = bucket.lookup(key_name)
    self.block_size = 2 ** 16
    self.cached_block = -1

  def __getitem__(self, i):
    if isinstance(i, slice):
      start = i.start
      end = i.stop - 1
    else:
      start = i
      end = start + 1
    return self.fetch(start, end)

  def fetch(self, start, end):
    try:
      return self.key.get_contents_as_string(
        headers={'Range': 'bytes={0}-{1}'.format(start, end)}
      )
    except boto.exception.S3ResponseError, e:
      # invalid range, we've reached the end of the file.
      if e.status == 416:
        return ''


def print_usage():
  usage_doc = sys.modules[__name__].__doc__
  usage_doc = usage_doc.replace('%s', sys.argv[0])
  sys.stderr.write(usage_doc)


def main():
  if len(sys.argv) != 2:
    print_usage()
    sys.exit(2)

  mmap = BotoMap(
    'aws-publicdatasets',
    '/common-crawl/projects/url-index/url-index.1356128792'
    )

  reader = pbtree.PBTreeDictReader(
    mmap,
    value_format="<QQIQI",
    item_keys=(
      'arcSourceSegmentId',
      'arcFileDate',
      'arcFilePartition',
      'arcFileOffset',
      'compressedSize'
    )
  )

  try:
    for url, d in reader.itemsiter(sys.argv[1]):
      print url, d
  except KeyboardInterrupt:
    pass


if __name__ == "__main__":
  main()
