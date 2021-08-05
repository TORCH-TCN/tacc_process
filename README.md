# tacc_process
Script tools to process images on the TACC file server

## v1

Basically a clone of Powersorter.py to read the same config file all Jason's scripts use.
Adds zip archive unpacking.

## wishlist

- detect/unpack "zips"
- sorted option, to run based on parent folder names (eg TX/OK/OTHER)
  - which then calls Powersorter
  - which then calls Url_gen
- maybe then call tacc_check/clean?
