# -*- coding: utf-8 -*-

import json

from io import StringIO
from collections import defaultdict

from Pegasus import yaml
from Pegasus.api.site_catalog import Arch
from Pegasus.api.site_catalog import OS
from Pegasus.api.site_catalog import Site
from Pegasus.api.site_catalog import Directory
from Pegasus.api.site_catalog import FileServer
from Pegasus.api.site_catalog import Operation
from Pegasus.api.site_catalog import Scheduler
from Pegasus.api.site_catalog import SupportedJobs
from Pegasus.api.site_catalog import Grid
from Pegasus.api.site_catalog import SiteCatalog
from Pegasus.api.errors import PegasusError

"""
:mod:`site_catalog` exposes an API to serialize and deserialize Pegasus's site catalog file.

Basic Usage::

    >>> from Pegasus import site_catalog
    >>> site_catalog.loads("... ")
    ...

    >>> print(site_catalog.dumps( ... ))
    ' ... '

.. moduleauthor:: Ryan Tanaka <tanaka@isi.edu>
.. moduleauthor:: Rajiv Mayani <mayani@isi.edu>
"""

from typing import Dict, TextIO

__all__ = (
    "load",
    "loads",
    "dump",
    "dumps",
)


def _to_sc(d: dict) -> SiteCatalog:
    """Convert dict to SiteCatalog
    
    :param d: SiteCatalog represented as a dict
    :type d: dict
    :raises PegasusError: encountered error parsing 
    :return: a SiteCatalog object based on d
    :rtype: SiteCatalog
    """

    try:
        sc = SiteCatalog()

        for s in d["sites"]:
            site = Site(
                s["name"],
                arch=getattr(Arch, s.get("arch").upper()) if s.get("arch") else None,
                os_type=getattr(OS, s.get("os.type").upper())
                if s.get("os.type")
                else None,
                os_release=s.get("os.release"),
                os_version=s.get("os.version"),
                glibc=s.get("glibc"),
            )

            # add directories
            for _dir in s["directories"]:
                directory = Directory(
                    getattr(Directory, _dir["type"].upper()), _dir["path"]
                )

                # add file servers
                for fs in _dir["fileServers"]:
                    file_server = FileServer(
                        fs["url"], getattr(Operation, fs["operation"].upper())
                    )

                    # add profiles
                    if fs.get("profiles"):
                        file_server.profiles = defaultdict(dict, fs.get("profiles"))

                    # add file server to this directory
                    directory.add_file_server(file_server)

                # add directory to this site
                site.add_directory(directory)

            # add grids
            if s.get("grids"):
                for gr in s.get("grids"):
                    grid = Grid(
                        getattr(Grid, gr["type"].upper()),
                        gr["contact"],
                        getattr(Scheduler, gr["scheduler"].upper()),
                        job_type=getattr(SupportedJobs, gr.get("jobtype").upper())
                        if gr.get("jobtype")
                        else None,
                        free_mem=gr.get("freeMem"),
                        total_mem=gr.get("totalMem"),
                        max_count=gr.get("maxCount"),
                        max_cpu_time=gr.get("maxCPUTime"),
                        running_jobs=gr.get("runningJobs"),
                        jobs_in_queue=gr.get("jobsInQueue"),
                        idle_nodes=gr.get("idleNodes"),
                        total_nodes=gr.get("totalNodes"),
                    )

                    # add grid to this site
                    site.add_grid(grid)

            # add profiles
            if s.get("profiles"):
                site.profiles = defaultdict(dict, s.get("profiles"))

            # add site to sc
            sc.add_site(site)

        return sc

    except KeyError:
        raise PegasusError("error parsing {}".format(d))


def load(fp: TextIO, *args, **kwargs) -> SiteCatalog:
    """
    Deserialize ``fp`` (a ``.read()``-supporting file-like object containing a SiteCatalog document) to a :py:class:`~Pegasus.api.site_catalog.SiteCatalog` object.

    :param fp: file like object to load from 
    :type fp: TextIO
    :return: deserialized SiteCatalog object
    :rtype: SiteCatalog
    """
    return _to_sc(yaml.load(fp))


def loads(s: str, *args, **kwargs) -> SiteCatalog:
    """
    Deserialize ``s`` (a ``str``, ``bytes`` or ``bytearray`` instance containing a SiteCatalog document) to a :py:class:`~Pegasus.api.site_catalog.SiteCatalog` object.

    :param s: string to load from 
    :type s: str
    :return: deserialized SiteCatalog object
    :rtype: SiteCatalog
    """
    return _to_sc(yaml.load(s))


def dump(obj: SiteCatalog, fp: TextIO, _format="yml", *args, **kwargs) -> None:
    """
    Serialize ``obj`` as a :py:class:`~Pegasus.api.site_catalog.SiteCatalog` formatted stream to ``fp`` (a ``.write()``-supporting file-like object).

    :param obj: SiteCatalog to serialize
    :type obj: SiteCatalog
    :param fp: file like object to serialize to
    :type fp: TextIO
    :param _format: format to write to if fp does not have an extension; can be one of ["yml" | "yaml" | "json"], defaults to "yml"
    :type _format: str
    :rtype: NoReturn
    """
    obj.write(fp, _format=_format)


def dumps(obj: SiteCatalog, _format="yml", *args, **kwargs) -> str:
    """
    Serialize ``obj`` to a :py:class:`~Pegasus.api.site_catalog.SiteCatalog` formatted ``str``.

    :param obj: SiteCatalog to serialize
    :type obj: SiteCatalog
    :param _format: format to write to if fp does not have an extension; can be one of ["yml" | "yaml" | "json"], defaults to "yml"
    :type _format: str
    :return: SiteCatalog serialized as a string
    :rtype: str
    """
    with StringIO() as s:
        obj.write(s, _format=_format)
        s.seek(0)
        return s.read()