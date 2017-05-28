#!/usr/bin/env python
import csv
from argparse import ArgumentParser
from time import sleep

import local_settings as settings
from mozscape import Mozscape
from utils import chunks, get_hostname

client = Mozscape(settings.MOZSCAPE_ACCESS_ID, settings.MOZSCAPE_SECRET_KEY)


def main():
    """
    File structure should be:
    1 row: header
    N row: url, ...any columns

    In the result it will add new columns after first one.
    """
    parser = ArgumentParser()
    parser.add_argument('--no-da', '--no-domain-authority', action='store_true', dest='no_da', help='Do not download information about domain authority')
    args = parser.parse_args()

    filename_in = 'data/in.csv'
    filename_out = 'data/out.csv'
    with open(filename_in) as csvfile:
        with open(filename_out, 'w+') as csvoutfile:
            reader = csv.reader(csvfile)
            writer = csv.writer(csvoutfile)
            row = next(reader, None)  # skip the headers
            assert isinstance(row, list)
            row.insert(1, 'Hostname')
            row.insert(2, 'Domain Authority')
            writer.writerow(row)
            hostnames = set()
            for row in reader:
                url, *d = row
                hostname = get_hostname(url) + '/'
                if hostname not in hostnames:
                    hostnames.add(hostname)
            all_metrics = dict()
            hostnames = list(hostnames)
            print(hostnames)
            if not args.no_da:
                cols = (Mozscape.UMCols.url | Mozscape.UMCols.domainAuthority)
                i = 0
                for hs in chunks(hostnames, 10):
                    print(i)
                    i += 1
                    metrics = client.urlMetrics(hs, cols)
                    all_metrics.update([
                        (metric['uu'], metric['pda']) for metric in metrics
                    ])
                    sleep(4)
                    # print(all_metrics)
                    # exit(0)

            hostnames = set()
            csvfile.seek(1)
            next(reader, 1)  # skip the headers
            for row in reader:
                url, *d = row
                # print(row)
                # exit(1)
                hostname = get_hostname(url) + '/'
                if hostname in hostnames:
                    continue
                hostnames.add(hostname)
                da = round(all_metrics[hostname]) if hostname in all_metrics else '0'
                row = url, hostname[:-1], da, *d
                # print(row)
                # exit(1)
                writer.writerow(row)

    print(len(hostnames), len(hostnames))


if __name__ == '__main__':
    main()
