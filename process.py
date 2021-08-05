import json
#import re
import os
from pathlib import Path
import shutil
import datetime
#import csv
import pwd
import argparse
import datetime
import sys
import glob
from zipfile import ZipFile

print(f'STARTING')

CONFIG_FORMAT_REQUIRED = '3.0'
sorted_file_count = 0
unmoved_file_count = 0

def scan_for_archives(dir):
    '''
    Scans a dir for registered archive file extensions
    Registered means Zip or anything shutil can unzip.
    '''
    result = []

    other_exts = [i[1] for i in shutil.get_unpack_formats()]
    ext_patterns = ['*' + i for g in other_exts for i in g]
    # print(ext_patterns)
    try:
        folders = [f for f in Path(dir).iterdir()]
        archives = [f for f in Path(dir).iterdir() if any(f.match(p) for p in ext_patterns)]
        print(f'found', len(archives), 'archives to unpack out of', len(folders), 'total folders')
        result = archives
    except:
        print(dir, 'not a valid path')

    return result


def unpack_archives(archive_paths, delete_archive=True):
    '''
    Accepts a list of folder(s) (paths?). Replaces them with unzipped folder of the same name.
    Zips it tests for corruptions then only extracts the JPG and DNG file extensions found.
    Other archive types are handled by shutil.
    '''
    result = []

    for arc in archive_paths:
        # default location is cwd, instead parse name and path out to create new folder
        loc = arc.parent
        name = arc.stem
        # ext = arc.suffixes
        new_folder = os.path.join(loc, name)

        try:
            # if zip, just unpack JPG/DNG using ZipFile
            if arc.suffix.lower() == '.zip':
                with ZipFile(arc, 'r') as zip_object:
                    # test the archive first to see if it's corrupt
                    ret = zip_object.testzip()
                    if ret is not None:
                        print(f'First bad file in zip:', ret)
                    else:
                        print(f'Zip archive is good.')

                    list_names = zip_object.namelist()
                    for file_name in list_names:
                        if file_name.lower().endswith(tuple(['.jpg', '.jpeg', '.dng'])):
                            # Extract any file with these exts from zip
                            zip_object.extract(file_name, arc.parent)
                            print(f'Extracting', file_name)
            # otherwise, fallback to shutil
            else:
                # 3.6 this can't handle path objects
                shutil.unpack_archive(str(arc), arc.parent)
            result.append(new_folder)
            # print('unpacked', new_folder)

            # remove the archive if everything worked
            if delete_archive:
                os.remove(arc)
        except ValueError:
            print(arc.stuffix, 'was not valid unpack archive type:', shutil.get_unpack_formats())
        except:
            print(f"Unexpected error:", sys.exc_info()[0])
            # print("Unexpected error:")
            raise

    return result

def scan_files(path=None, pattern=None, file_type=None):
    """
    Scan the directory for files matching the provided pattern.
    Extract relevant parts from file for organization and sorting
    Return a list of matching files
    """
    matches = []
    # print('pattern:', pattern)
    file_pattern = re.compile(pattern)
    for root, dirs, files in os.walk(path):
        #print(len(files))
        for file in files:
            # print(os.path.join(root, file))
            m = file_pattern.match(file)
            if m:
                # print('matched', file, m.groupdict())
                file_dict = m.groupdict()
                file_path = os.path.join(root, file)
                file_dict['file_path'] = file_path
                file_dict['file_type'] = file_type
                matches.append(file_dict)
    print(f'match count', len(matches))
    return matches


class Settings():
    def __init__(self, prefix=None, dry_run=None, verbose=None, force_overwrite=None):
        self.prefix = prefix
        self.dry_run = dry_run
        self.verbose = verbose
        self.force_overwrite = force_overwrite

    def load_config(self, config_file=None):
        # load config file
        if config_file:
            with open(config_file) as f:
                config = json.load(f)
                # print(config)
                self.versions = config.get('versions', None)
                self.config_format = self.versions.get('config_format')
                self.collection = config.get('collection', None)
                self.collection_prefix = self.collection.get('prefix', None)
                self.catalog_number_regex = self.collection.get('catalog_number_regex', None)
                self.files = config.get('files', None)
                self.folder_increment = int(self.files.get('folder_increment', 1000))
                self.log_directory_path = Path(self.files.get('log_directory_path', None))
                self.number_pad = int(self.files.get('number_pad', 7))
                self.output_base_path = Path(self.files.get('output_base_path', None))
                # Get the type of files and patterns that will be scanned and sorted
                self.file_types = config.get('file_types', None)


if __name__ == '__main__':
    # initialize settings
    # set up argparse
    args = arg_setup()
    # print(args)
    config_file = args['config']
    dry_run = args['dry_run']
    verbose = args['verbose']
    force_overwrite = args['force']
    input_path_override = args['input_path']

    """
    #TODO reactivate input path override
    if input_path_override:
        input_path = Path(input_path_override)
    else:
        input_path = Path(files.get('input_path', None))

    # Check existence of input path
    if input_path:
        # test to ensure input directory exists
        if input_path.is_dir():
            print('Sorting files from input_path:', input_path)
        else:
            print(f'ERROR: directory {input_path} does not exist.')
            print('Terminating script.')
            quit()
    """
    # Confirm force overwrite
    force_overwrite_confirmed = False
    if force_overwrite:
        print('Files with identical names will be overwritten if you proceed.')
        response = input('Type \'overwrite\' and [RETURN/ENTER] to confirm desire to overwrite files: ')
        if response == 'overwrite':
            print('Will overwrite duplicate file names...')
            force_overwrite_confirmed = True
        else:
            print('Overwrite not confirmed. Exiting...')
            force_overwrite_confirmed = False
            sys.exit()

    settings = Settings(dry_run=dry_run, verbose=verbose, force_overwrite=force_overwrite_confirmed)
    # Load settings from config
    settings.load_config(config_file=config_file)

    # Check required config_file version
    if not str(settings.config_format) == CONFIG_FORMAT_REQUIRED:
        print('Wrong config format version:', settings.config_format, 'Required:', CONFIG_FORMAT_REQUIRED)
        sys.exit()

    # Generate log file name and path
    now = datetime.datetime.now()
    log_filename = settings.collection_prefix + '_' + str(now.strftime('%Y-%m-%dT%H%M%S'))
    if dry_run:
        log_filename = log_filename + '_DRY-RUN'
    log_filename = log_filename + '.csv'
    log_file_path = settings.log_directory_path.joinpath(log_filename)

    # get current username
    try:
        username = pwd.getpwuid(os.getuid()).pw_name
    except:
        print(f'ERROR - Unable to retrieve username.')
        username = None

    #csvfile = open(log_file_path, 'w', newline='')
    #fieldnames = ['timestamp', 'username', 'action', 'result', 'details', 'filetype', 'source', 'destination']
    #writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    #writer.writeheader()

    input_path = Path(settings.files.get('input_path', None))
    # print(settings.catalog_number_regex)

    # verify path exists before starting
    try:
        os.path.isdir(input_path)
    except:
        print(f'Input_path was not valid.')

    # scan for archives
    archives = scan_for_archives(input_path)
    print(f'archives found:', archives)
    # if any archives, unpack them
    if archives:
        unpacked = unpack_archives(archives)#, delete_archive=False
        print(f'unpacked archives :', unpacked)

    # subset based on parent folders, if flag says to

    # start sorting
    # call powersorter.py

    # call url_gen.py

    #csvfile.close()
    # Summary report
    print(f'PROCESS COMPLETE')
    if verbose:
        print('sorted_file_count', sorted_file_count)
        print('unmoved_file_count', unmoved_file_count)
    print(f'xLog file written to:', log_file_path)
