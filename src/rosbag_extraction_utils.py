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

import cv2
import os

import numpy as np
from cv_bridge import CvBridge
import csv


def make_dir_if_needed(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)


def get_timestamp_filename(timestamp, extension):
    return "%d.%s" % (timestamp.secs * 1e9 + timestamp.nsecs, extension)


def make_topic_dirs(out_dir, topics):
    count = 0
    topic_dirs = {}
    for topic in topics:
        topic_dirs[topic] = "./%s/%s" % (out_dir, topic.replace('/', '_'))
        make_dir_if_needed(topic_dirs[topic])
        count += 1
    return topic_dirs


class RosbagUtils:
    def __init__(self, bag, output):
        self.bag = bag
        make_dir_if_needed(output)
        self.output = output

    def extract_images(self, topics, use_depth=False):
        topic_dirs = make_topic_dirs(self.output, topics)
        bridge = CvBridge()
        for topic, msg, t in self.bag.read_messages(topics=topics):
            cv_img = bridge.imgmsg_to_cv2(msg, "passthrough")
            if use_depth:
                # ROS writes 32F images, so conversion is needed
                depth_array = np.array(cv_img, dtype=np.float32)
                extension = "npy"
                filename = get_timestamp_filename(msg.header.stamp, extension)
                path = os.path.join(topic_dirs[topic], filename)
                np.save(path, depth_array)
            else:
                extension = "png"
                filename = get_timestamp_filename(msg.header.stamp, extension)
                path = os.path.join(topic_dirs[topic], filename)
                cv2.imwrite(path, cv_img)
                print("Wrote image %s" % filename)

    def extract_time_ref(self, topics):
        topic_dirs = make_topic_dirs(self.output, topics)
        for topic in topics:
            path = os.path.join(topic_dirs[topic], "time_ref.csv")
            with open(path, "w+") as time_ref_file:
                writer = csv.writer(time_ref_file, delimiter=',')
                for i, (_, msg, t) in enumerate(
                        self.bag.read_messages(topics=topic)
                ):
                    writer.writerow(
                        [i, msg.header.stamp, msg.time_ref]
                    )

    def extract_imu(self, topics, temp_topics):
        topic_dirs = make_topic_dirs(self.output, topics)

        for topic, temp_topic in zip(topics, temp_topics):
            path = os.path.join(topic_dirs[topic], "imu.csv")
            with open(path, "w+") as imu_file:
                writer = csv.writer(imu_file, delimiter=',')
                imu_msgs = self.bag.read_messages(topics=topic)
                temp_msgs = self.bag.read_messages(topics=temp_topic)
                count = 0
                for (_, imu_msg, imu_t), (_, temp_msg, temp_t) in zip(imu_msgs, temp_msgs):
                    la = imu_msg.linear_acceleration
                    av = imu_msg.angular_velocity
                    temp_stamp = imu_msg.header.stamp
                    imu_stamp = temp_msg.header.stamp

                    assert imu_stamp == temp_stamp, "Timestamp in temperature file did not match IMU timestamp"
                    writer.writerow(
                        [imu_stamp, av.x, av.y, av.z, la.x, la.y, la.z, temp_msg.temperature]
                    )
                    count += 1
            print("Written %d IMU rows for %s" % (count, topic))
