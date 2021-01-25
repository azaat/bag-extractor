# Copyright 2020 Mobile Robotics Lab. at Skoltech
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import csv
import re

ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.tif']


def align_by_ref(time_ref, target_dir, ref_seq):
    """Aligns timestamps of the files in the given directory.
       Writes transformation meta information to _transformation_metainf.csv file.

        Args:
            time_ref: Time reference file with timestamps from another source
            target_dir: Target directory that contains files (e.g. images) with timestamps as filenames
            ref_seq: Sequence from time reference file that matches the time of the first image
    """
    with open(time_ref, 'r') as time_ref_file:
        values = time_ref_file.readlines()[ref_seq - 1].split(',')
        seq = int(values[0])
        ref_timestamp = int(values[1])
        # get list of filenames with timestamps
        filename_timestamps = map(
            lambda x: int(os.path.splitext(x)[0]),
            filter(
                lambda x: os.path.splitext(x)[1] in ALLOWED_EXTENSIONS,
                os.listdir(target_dir)
            )
        )
        filename_timestamps.sort()
        _, extension = os.path.splitext(os.listdir(target_dir)[0])
        timestamp = filename_timestamps[0]
        # obtain delta with the first filename timestamp and reference timestamp
        delta = ref_timestamp - timestamp

        print("Aligning with sequence %d, timestamps %d - %d" % (seq, timestamp, ref_timestamp))
        _align(target_dir, filename_timestamps, extension, delta)


def align_by_delta(time_ref, target_dir, video_path):
    # load frame timestamps csv, rename frames according to it
    video_root, video_filename = os.path.split(video_path)
    video_name, _ = os.path.splitext(video_filename)
    video_date = re.sub(r"VID_((\d|_)*)", r"\1", video_name)

    with open(os.path.join(video_root, video_date, video_name + "_timestamps.csv")) as frame_timestamps_file:
        filename_timestamps = map(
            lambda x: int(x), frame_timestamps_file.readlines()
        )
        _, extension = os.path.splitext(os.listdir(target_dir)[0])
        for i, timestamp in enumerate(filename_timestamps):
            os.rename(
                os.path.join(target_dir, "frame-%d.png" % (i + 1)),
                os.path.join(target_dir, str(timestamp) + extension)
            )
        with open(time_ref, 'r') as time_ref_file:
            values = time_ref_file.readline().split(',')
            seq = int(values[0])
            ref_timestamp = int(values[1])
            timestamp = int(values[2])
            # obtain delta with the info from time reference file
            delta = ref_timestamp - timestamp

            # align with delta
            print("Aligning with sequence %d, timestamps %d - %d" % (seq, timestamp, ref_timestamp))
            _align(target_dir, filename_timestamps, extension, delta)


def _align(target_dir, filename_timestamps, extension, delta):
    with open(os.path.join(target_dir, 'transformation_metainf.csv'), 'w') as transformation_file:
        transformation_writer = csv.DictWriter(
            transformation_file, delimiter=',', fieldnames=['seq', 'old_stamp', 'new_stamp']
        )
        transformation_writer.writeheader()
        for seq, old_stamp in enumerate(filename_timestamps):
            new_stamp = int(old_stamp) + delta
            new_name = str(new_stamp) + extension
            old_name = str(old_stamp) + extension
            print("Old name: %s new name: %s" % (old_name, new_name))

            transformation_writer.writerow({'seq': seq, 'old_stamp': old_stamp, 'new_stamp': new_stamp})
            os.rename(
                os.path.join(target_dir, old_name),
                os.path.join(target_dir, new_name)
            )
