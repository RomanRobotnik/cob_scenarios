#!/usr/bin/python
#################################################################
##\file
#
# \note
#   Copyright (c) 2010 \n
#   Fraunhofer Institute for Manufacturing Engineering
#   and Automation (IPA) \n\n
#
#################################################################
#
# \note
#   Project name: care-o-bot
# \note
#   ROS stack name: cob_scenarios
# \note
#   ROS package name: cob_generic_states
#
# \author
#   Florian Weisshardt, email:florian.weisshardt@ipa.fhg.de
#
# \date Date of creation: Aug 2011
#
# \brief
#   Implements generic states which can be used in multiple scenarios.
#
#################################################################
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     - Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer. \n
#     - Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution. \n
#     - Neither the name of the Fraunhofer Institute for Manufacturing
#       Engineering and Automation (IPA) nor the names of its
#       contributors may be used to endorse or promote products derived from
#       this software without specific prior written permission. \n
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License LGPL as 
# published by the Free Software Foundation, either version 3 of the 
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License LGPL for more details.
# 
# You should have received a copy of the GNU Lesser General Public 
# License LGPL along with this program. 
# If not, see <http://www.gnu.org/licenses/>.
#
#################################################################

import roslib
roslib.load_manifest('cob_generic_states')
import rospy
import smach
import smach_ros
from nav_msgs.msg import Odometry

from simple_script_server import *
sss = simple_script_server()

## Approach pose state
#
# This state will try forever to move the robot to the given pose.
class approach_pose(smach.State):

	def __init__(self, pose = "", mode = "omni", move_second = "False"):
		smach.State.__init__(
			self,
			outcomes=['succeeded', 'failed'],
			input_keys=['base_pose'])

		self.pose = pose
		self.mode = mode
		self.move_second = move_second
		self.is_moving = False



	def execute(self, userdata):

		#Callback for the /base_controller/odometry subscriber
		def callback(data):
			self.is_moving = True
			#rospy.loginfo("/base_controller/odometry is publishing a message")

		# determine target position
		if self.pose != "":
			pose = self.pose
		elif type(userdata.base_pose) is str:
			pose = userdata.base_pose
		elif type(userdata.base_pose) is list:
			pose = []
			pose.append(userdata.base_pose[0])
			pose.append(userdata.base_pose[1])
			pose.append(userdata.base_pose[2])
		else: # this should never happen
			rospy.logerr("Invalid userdata 'pose'")
			return 'failed'

		# try reaching pose
		handle_base = sss.move("base", pose, mode=self.mode, blocking=False)
		move_second = self.move_second
		is_moving = self.is_moving

		timeout = 0
		while True:
			if (handle_base.get_state() == 3) and (not move_second):
				# do a second movement to place the robot more exactly
				handle_base = sss.move("base", pose, mode=self.mode, blocking=False)
				move_second = True
			elif (handle_base.get_state() == 3) and (move_second):
				return 'succeeded'			

			# Subscriber to base_odometry
			rospy.Subscriber("/base_controller/odometry", Odometry, callback)
	
			#Check if the base is moving , with a subcriber to the topic /base_controller/odometry
			if not is_moving: # robot stands still
				if timeout > 10:
					sss.say(["I can not reach my target position because my path or target is blocked"],False)
					timeout = 0
				else:
					timeout = timeout + 1
					rospy.sleep(1)
			else:
				timeout = 0

## Approach pose state (without retry)
#
# This state tries once to move the robot to the given pose.
class approach_pose_without_retry(smach.State):

	def __init__(self, pose = "", mode = "omni", move_second = "False"):
		smach.State.__init__(
			self,
			outcomes=['succeeded', 'failed'],
			input_keys=['base_pose'])

		self.pose = pose
		self.mode = mode
		self.move_second = move_second
		self.is_moving = False

	def execute(self, userdata):
		#Callback for the /base_controller/odometry subscriber
		def callback(data):
			self.is_moving = True
			#rospy.loginfo("/base_controller/odometry is publishing a message")

		# determine target position
		if self.pose != "":
			pose = self.pose
		elif type(userdata.base_pose) is str:
			pose = userdata.base_pose
		elif type(userdata.base_pose) is list:
			pose = []
			pose.append(userdata.base_pose[0])
			pose.append(userdata.base_pose[1])
			pose.append(userdata.base_pose[2])
		else: # this should never happen
			rospy.logerr("Invalid userdata 'pose'")
			return 'failed'

		# try reaching pose
		handle_base = sss.move("base", pose, mode=self.mode, blocking=False)
		move_second = self.move_second
		is_moving = self.is_moving

		timeout = 0
		while True:
			if (handle_base.get_state() == 3) and (not move_second):
				# do a second movement to place the robot more exactly
				handle_base = sss.move("base", pose, mode=self.mode, blocking=False)
				move_second = True
			elif (handle_base.get_state() == 3) and (move_second):
				return 'succeeded'		

			# Subscriber to base_odometry
			rospy.Subscriber("/base_controller/odometry", Odometry, callback)

		
			# evaluate sevice response
			if not is_moving: # robot stands still
				if timeout > 10:
					sss.say(["I can not reach my target position because my path or target is blocked, I will abort."],False)
					rospy.wait_for_service('base_controller/stop',10)
					try:
						stop = rospy.ServiceProxy('base_controller/stop',Trigger)
						resp = stop()
					except rospy.ServiceException, e:
						error_message = "%s"%e
						rospy.logerr("calling <<%s>> service not successfull, error: %s",service_full_name, error_message)
					return 'failed'
				else:
					timeout = timeout + 1
					rospy.sleep(1)
			else:
				timeout = 0
