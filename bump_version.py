import logging
import re
from collections import deque
from typing import Iterable, Any

import github_actions

# Regex matching semantic versions as specified in https://semver.org/
SEMVER_REGEX = re.compile(
    r'(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)'
    r'(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?'
    r'(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$'
)


_no_fill = object()


def ngrams(iterable: Iterable, n: int = 2, fillvalue: Any = _no_fill) -> Iterable:
    """
    Yield subsequent overlapping tuples of size n from iterable.
    """
    if n < 1:
        raise ValueError('n must be a positive integer.')

    iterator = iter(iterable)

    # Populate the history with n elements, fill it up with fillvalues if the iterable is too small.
    history = deque(maxlen=n)
    fill_size = 0
    for _ in range(n):
        try:
            history.append(next(iterator))
        except StopIteration:
            if fillvalue is _no_fill:
                return
            history.append(fillvalue)
            fill_size += 1

    for element in iterator:
        yield tuple(history)
        history.append(element)

    yield tuple(history)

    if fillvalue is not _no_fill:
        for _ in range(n-fill_size-1):
            history.append(fillvalue)
            yield tuple(history)


class NoVersionUpdated(Exception):
    pass


class MarkerNotFoundException(Exception):
    pass


def bump_versions(file, version, marker):
    found_marker = False
    version_bump_count = 0

    for previous, line in ngrams(file, 2, fillvalue=None):
        if marker in previous:
            found_marker = True
            if line is not None:
                line, k = re.subn(SEMVER_REGEX, version, line)
                version_bump_count += k
        yield previous

    if not found_marker:
        raise MarkerNotFoundException("Found no marker '%s'", marker)
    
    if not version_bump_count:
        raise NoVersionUpdated("No line following a marker contained a semantic version.")


def bump_file(file, version, marker):
    with open(file, encoding='utf-8') as i:
        # TODO do not load into memory
        output = list(bump_versions(i, version, marker))
    with open(file, 'w', encoding='utf-8') as o:
        o.writelines(output)


def bump_files(files, version, marker):
    for file in files:
        try:
            bump_file(file, version, marker)
            yield file
        except (NoVersionUpdated, MarkerNotFoundException) as e:
            logging.warning("Version in file '%s' was not updated, caused by: %s", file, e)


def main():
    files = github_actions.get_input('files').split()
    version = github_actions.get_input('version')
    marker = github_actions.get_input('marker')

    bumped_files = bump_files(files, version, marker)

    github_actions.set_output('files', ' '.join(bumped_files))


if __name__ == '__main__':
    main()
