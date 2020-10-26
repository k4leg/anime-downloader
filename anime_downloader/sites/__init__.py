"""Anime sites.

This package exports the following modules:
    animevost  'animevost.org'
"""

from anime_downloader.sites import animevost

sites = {
    site: eval(site)
    for site in dir()
    if not site.startswith('__') and not site.endswith('__')
}
