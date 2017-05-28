from urllib.parse import ParseResult, urlparse


def get_hostname(url):
    res = urlparse(url)
    assert isinstance(res, ParseResult)
    return res.hostname


def chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]
