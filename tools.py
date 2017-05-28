#!/usr/bin/env python
import csv
import logging
from time import sleep
from urllib.error import HTTPError

import local_settings as settings
from mozscape import Mozscape, MozscapeError
from utils import chunks, get_hostname


def filter_and_add_da(file_in, file_out):
    client = Mozscape(settings.MOZSCAPE_ACCESS_ID, settings.MOZSCAPE_SECRET_KEY)
    reader = csv.reader(file_in)
    writer = csv.writer(file_out)
    row = next(reader, None)  # skip the headers
    assert isinstance(row, list), row
    row.insert(1, 'Hostname')
    row.insert(2, 'Domain Authority')
    writer.writerow(row)

    # getting Domain Authority
    hostnames = set(get_hostname(row[0]) for row in reader)
    all_metrics = dict()
    cols = Mozscape.UMCols.url | Mozscape.UMCols.domainAuthority
    for hs in chunks(list(hostnames), 10):
        metrics = None
        while True:
            try:
                metrics = client.urlMetrics(hs, cols)
                break
            except MozscapeError as err:
                # MozscapeError: HTTP Error 429: Permission denied: ...
                if isinstance(err.value, HTTPError) and err.value.code == 429:
                    sleep(3)
                else:
                    logging.exception(err)
                    break
        if metrics:
            all_metrics.update((metric['uu'], metric['pda']) for metric in metrics)

    # filtering and adding new columns
    hostnames = set()
    file_in.seek(0)
    next(reader, 1)  # skip the headers
    for row in reader:
        url, *d = row
        hostname = get_hostname(url) + '/'
        if hostname in hostnames:
            continue
        hostnames.add(hostname)
        da = round(all_metrics[hostname]) if hostname in all_metrics else '0'
        row = url, hostname[:-1], da, *d
        writer.writerow(row)
