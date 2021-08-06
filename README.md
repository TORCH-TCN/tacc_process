# tacc_process
Script tools to process images on the TACC file server

Process.py is a meta script to call the existing script tools we already have for working with files on TACC.

## v2

Basically a clone of Powersorter.py to read the same config file all Jason's scripts use.
Adds zip archive unpacking.
Added back in a setup function that was deleted.
Added new arg '-subset' for running Powersorter + Urlgen in batches instead everything in one go

## wishlist

X detect/unpack "zips"
- sorted option, to run based on parent folder names (eg TX/OK/OTHER)
  - NOT_OK_NOT_TX/OK-20200910SH/TX-20200910SH. Dash not always present
  - which then calls Powersorter
  - which then calls Url_gen
- maybe then call tacc_check/clean?
