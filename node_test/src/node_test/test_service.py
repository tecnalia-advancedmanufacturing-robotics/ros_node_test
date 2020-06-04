#!/usr/bin/env python
"""
@package node_test
@file test_service
@author Anthony Remazeilles
@brief perform a unittest on a ROS service call

Copyright (C) 2020 Tecnalia Research and Innovation
Distributed under the Apache 2.0 license.

"""

import sys
import unittest
import rospy
import rosservice
import rostest
import genpy
from rospy_message_converter import message_converter

CLASSNAME = 'servicetest'


class ServiceTest(unittest.TestCase):
    def __init__(self, *args):
        super(ServiceTest, self).__init__(*args)

    def setUp(self):
        rospy.init_node(CLASSNAME)

    def test_service(self):
        try:
            srv_name = rospy.get_param('~service_name')
            srv_input = rospy.get_param('~service_input')
            srv_output = rospy.get_param('~service_output')
        except KeyError as err:
            msg_err = "service_test not initialized properly"
            msg_err += " Parameter [%s] not set." % (str(err))
            msg_err += " Caller ID: [%s] Resolved name: [%s]" % (
                rospy.get_caller_id(),
                rospy.resolve_name(err.args[0]))
            self.fail(msg_err)

        rospy.loginfo("Testing service {} with input parameters {}".format(
            srv_name,
            srv_input))
        self._test_service(srv_name, srv_input, srv_output)

    def _test_service(self, srv_name, srv_input, srv_output):
        self.assert_(srv_name)

        all_services = rosservice.get_service_list()
        self.assertIn(srv_name, all_services)

        srv_class = rosservice.get_service_class_by_name(srv_name)

        try:
            srv_proxy = rospy.ServiceProxy(srv_name, srv_class)
        except KeyError as err:
            msg_err = "Service proxy could not be created"
            self.fail(msg_err)

        try:
            srv_resp = srv_proxy(**srv_input)
        except (genpy.SerializationError, rospy.ROSException), err:
            msg_err = "Service proxy error: {}".format(err.message)
            self.fail(msg_err)
        srv_dic = message_converter.convert_ros_message_to_dictionary(srv_resp)

        self.assertDictEqual(srv_dic, srv_output)


def main():
    try:
        rostest.run('rostest', CLASSNAME, ServiceTest, sys.argv)
    except KeyboardInterrupt:
        pass
    print("{} exiting".format(CLASSNAME))
