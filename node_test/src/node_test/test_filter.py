#!/usr/bin/env python
"""
@package node_test
@file test_filter
@author Anthony Remazeilles
@brief perform a unittest on a ROS message filter like behavior

Copyright (C) 2020 Tecnalia Research and Innovation
Distributed under the Apache 2.0 license.

"""

import sys
import unittest
import rospy
import rostopic
import rosmsg
import rostest
import genpy
from rospy_message_converter import message_converter

CLASSNAME = 'filterTest'


class FilterMsgTest(unittest.TestCase):
    def __init__(self, *args):
        super(FilterMsgTest, self).__init__(*args)

        self.filter_msg = None
        self.filter_stamp = None
        self.is_received = False

    def setUp(self):
        rospy.init_node(CLASSNAME)

    def test_filter(self):
        try:
            #todo could use directly remapping functionality
            topic_in = rospy.get_param('~topic_in')
            topic_out = rospy.get_param('~topic_out')
            msg_in = rospy.get_param('~msg_in')
            msg_out = rospy.get_param('~msg_out')
            timeout = rospy.get_param('~timeout', None)
        except KeyError as err:
            msg_err = "filter_test not initialized properly \n"
            msg_err += " Parameter [%s] not set. \n" % (str(err))
            msg_err += " Caller ID: [%s] Resolved name: [%s]\n" % (
                rospy.get_caller_id(),
                rospy.resolve_name(err.args[0]))
            self.fail(msg_err)

        rospy.loginfo("Testing filtering {}-{}".format(topic_in, topic_out))
        self._test_filter(topic_in, topic_out, msg_in, msg_out, timeout)

    def _filter_cb(self, msg):
        self.filter_msg = msg
        self.filter_stamp = rospy.get_time()
        rospy.loginfo("Message received!")
        self.is_received = True

    def _test_filter(self, topic_in, topic_out, msg_in, msg_out, timeout):
        self.assert_(topic_in)
        self.assert_(topic_out)
        self.assert_(msg_in)
        self.assert_(msg_out)

        l_pub = rospy.get_published_topics()
        rospy.loginfo("Detected topics: {}".format(l_pub))

        # getting message to send
        msg_in_type = rostopic.get_topic_type(topic_in)[0]
        rospy.loginfo("Type transiting on {}: {}".format(topic_in, msg_in_type))
        self.assert_(msg_in_type is not None)

        rospy.loginfo("Converting {} into {}".format(msg_in, msg_in_type))
        try:
            ros_msg_in = message_converter.convert_dictionary_to_ros_message(msg_in_type, msg_in)
            rospy.loginfo("Generated message: [%s]" % (ros_msg_in))
        except ValueError as err:
            msg_err = "Prb in message in contruction \n"
            msg_err += "Expected type: [%s]\n" % (msg_in_type)
            msg_err += "dictionary: [%s]\n" % (msg_in)
            msg_err += "Erorr: [%s]\n" % (str(err))
            self.fail(msg_err)

        # getting message to receive
        msg_out_type = rostopic.get_topic_type(topic_out)[0]
        rospy.loginfo("Type transiting on {}: {}".format(topic_out, msg_out_type))
        self.assert_(msg_out_type is not None)

        rospy.loginfo("Converting {} into {}".format(msg_out, msg_out_type))
        try:
            ros_msg_out = message_converter.convert_dictionary_to_ros_message(msg_out_type, msg_out)
            rospy.loginfo("Generated message: [%s]" % (ros_msg_out))
        except ValueError as err:
            msg_err = "Prb in message in contruction \n"
            msg_err += "Expected type: [%s]\n" % (msg_out_type)
            msg_err += "dictionary: [%s]\n" % (msg_out)
            msg_err += "Erorr: [%s]\n" % (str(err))
            self.fail(msg_err)

        # subscription
        # make sure no reception done before publication
        self.is_received = False
        pub = rospy.Publisher(topic_in, ros_msg_in.__class__, queue_size=1)
        sub = rospy.Subscriber(topic_out, ros_msg_out.__class__, self._filter_cb, queue_size=1)
        rospy.sleep(0.5)
        self.assert_(not self.is_received, "No message should be recieved before publication!")
        time_pub = rospy.get_time()
        pub.publish(ros_msg_in)
        # make sure one message gets received in the defined time.
        is_too_long = False
        while not self.is_received:
            if timeout is not None:
                if rospy.get_time() - time_pub > timeout:
                    is_too_long = True
                    break
            rospy.sleep(0.1)

        self.assert_(not is_too_long, 'filter out not received within indicated duration: [%s]' % timeout)

        rospy.loginfo("A message has been received!")
        rospy.loginfo("{} at {}".format(self.filter_msg, self.filter_stamp))
        duration = self.filter_stamp - time_pub
        rospy.loginfo("Filter duration: {}".format(duration))
        # check the receive message
        self.assertEqual(self.filter_msg, ros_msg_out)


def main():
    try:
        rostest.run('rostest', CLASSNAME, FilterMsgTest, sys.argv)
    except KeyboardInterrupt:
        pass
    print("{} exiting".format(CLASSNAME))
