#!/usr/bin/env python

import rospy, math
from ctypes import c_ushort
from rover_msgs.msg import Pololu, Drive, All, JointAngles
from sensor_msgs.msg import Joy, JointState
from std_msgs.msg import String,Float32MultiArray,UInt16MultiArray, Header
import time
import numpy as np


class XBOX():
    def __init__(self):
    # Variables
        self.joy = Joy()
        self.cmd = All()
        self.Xbox_joints = JointState()
        self.dyn = Float32MultiArray()
        self.dyn_cmd = Float32MultiArray()
        self.invkin = UInt16MultiArray()
        self.prev_y = 0
        self.case = 'Arm-xbox'
        self.cam1_sel = 0
        self.cam2_sel = 0
        self.analog_cam = 0

        self.invkin.data.append(0)
        self.invkin.data.append(90)
        self.invkin.data.append(-90)
        self.invkin.data.append(0)
        self.wristangle = Float32MultiArray()
        self.wristangle.data.append(0.0)
        self.wristangle.data.append(0.0)

        self.cmd.lw = 1500
        self.cmd.rw = 1500
        self.cmd.pan = 1500
        self.cmd.tilt = 1500
        self.cmd.camnum = 0
        self.cmd.q1 = 1815
        self.cmd.q2 = 968
        self.cmd.q3 = 2891
        self.cmd.q4 = 1968
        self.cmd.q5 = 0.0
        self.cmd.q6 = 0.0
        self.cmd.grip = 1000
        self.cmd.chutes = 0
        self.cmd.shovel = 1500
        self.check=True
        
        # Initialize Xboxjoints
        self.Xbox_joints.header = Header()
        #self.Xbox_joints.header.seq = ''
        self.Xbox_joints.header.stamp = rospy.Time.now()
        #self.Xbox_joints.header.frame_id = ''
        self.Xbox_joints.name = ['joint1', 'joint2', 'joint3', 'joint4', 'joint5', 'joint6']
        self.Xbox_joints.position = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.Xbox_joints.velocity = []
        self.Xbox_joints.effort = []      

        self.dyn.data.append(0.0)
        self.dyn.data.append(0.0)
        self.dyn_cmd.data.append(0.0)
        self.dyn_cmd.data.append(0.0)

    # Publishers and Subscribers
        self.sub2 = rospy.Subscriber('joy', Joy, self.joyCallback)
        self.sub3 = rospy.Subscriber('dynamixel_feedback', Float32MultiArray,self.dynCallback)
        self.sub4 = rospy.Subscriber('SetJointGoal', JointAngles, self.inversekin)
        self.pub1 = rospy.Publisher('/rover_command', All, queue_size = 10)
        self.pub_joints = rospy.Publisher('/joint_states', JointState, queue_size = 10)
        self.pub3 = rospy.Publisher('/mode', String, queue_size = 10)
        self.pub4 = rospy.Publisher('/dynamixel_command',Float32MultiArray,queue_size = 1)
        self.pub5 = rospy.Publisher('/debug_invkin',UInt16MultiArray, queue_size = 1)

    # Callbacks
    def inversekin(self,msg):
        if msg.solved == 1 and self.check == True:
            self.invkin.data[0] = msg.q[0]
            self.invkin.data[1] = msg.q[1]
            self.invkin.data[2] = msg.q[2]
            self.invkin.data[3] = msg.q[3]
            self.wristangle.data[0] = msg.q[4]
            self.wristangle.data[1] = msg.q[5]


    def joyCallback(self,msg):
        self.joy=msg
        if self.joy.buttons[9] == 1:
            if self.check==False:            
                self.check=True
            else:
                self.check=False

    def dynCallback(self,msg):
        self.dyn.data[0] = msg.data[0]
        self.dyn.data[1] = msg.data[1]

    # Functions
    def check_method(self):
        # Check to see whether driving or using arm and return case
        # [A, B, X, Y] = buttons[0, 1, 2, 3]
        y = self.joy.buttons[3] # toggle between modes
        home = self.joy.buttons[8]
        if y == 1:
            if self.case == 'Drive-Fast' or self.case == 'Drive-Med' or self.case == 'Drive-Slow':
                self.case = 'Arm-xbox'
            elif self.case == 'Arm-xbox':
                self.case = 'Chutes'
            elif self.case == 'Arm-IK':
                self.case = 'Chutes'
            else:
                self.case = 'Drive-Fast'
            time.sleep(.25)
        elif home == 1:
            if self.case == 'Arm-xbox':
                self.case = 'Arm-IK'
            else:
                self.case = 'Arm-xbox'
            time.sleep(.25)

    def slow_check(self):
        rb = self.joy.buttons[5]
        if rb == 1:
            if self.case == 'Drive-Fast':
                self.case = 'Drive-Med'
            elif self.case == 'Drive-Med':
                self.case = 'Drive-Slow'
            elif self.case == 'Drive-Slow':
                self.case = 'Drive-Fast'
            time.sleep(.25)

    def camera_select(self):
        # a selects between cameras 0-2, b selects between cameras 3-5
        # cam1_sel is lower nybble, cam2_sel is upper nybble
        a = self.joy.buttons[0]
        b = self.joy.buttons[1]

        if a == 1:
            if self.cam1_sel == 2:
                self.cam1_sel = 0
            else:
                self.cam1_sel = self.cam1_sel + 1
            time.sleep(.25)
        if b == 1:
            if self.cam2_sel == 2:
                self.cam2_sel = 0
            else:
                self.cam2_sel = self.cam2_sel + 1
            time.sleep(.25)
        # Update command
        self.cmd.camnum = (self.analog_cam << 7) | ((self.cam1_sel & 0x0f) | ((self.cam2_sel & 0x0f) << 4))

    def cam_pan_tilt(self):
        x = self.joy.buttons[2]
        back = self.joy.buttons[6]
        start = self.joy.buttons[7]
        push_right = self.joy.buttons[10]
        push_left = self.joy.buttons[9]

        if x == 1:
            self.cmd.pan = 1500
            self.cmd.tilt = 1500
            time.sleep(.05)
        if start == 1:
            self.cmd.tilt = self.cmd.tilt + 10.0
            time.sleep(.05)
        if back == 1:
            self.cmd.tilt = self.cmd.tilt - 10.0
            time.sleep(.05)
        if push_right == 1:
            self.cmd.pan = self.cmd.pan + 10.0
            time.sleep(.05)
        if push_left == 1:
            self.cmd.pan = self.cmd.pan - 10.0
            time.sleep(.05)
        # bounds check
        if self.cmd.tilt > 2000:
            self.cmd.tilt = 2000
        if self.cmd.tilt < 1000:
            self.cmd.tilt = 1000
        if self.cmd.pan > 2000:
            self.cmd.pan = 2000
        if self.cmd.pan < 1000:
            self.cmd.pan = 1000

    def gripper(self):
        rb = self.joy.buttons[5]
        lb = self.joy.buttons[4]
        if rb == 1:
            self.cmd.grip = 2
        elif lb == 1:
            self.cmd.grip = 1
        else:
            self.cmd.grip = 0

    # ==========================================================================
    # Drive Control ===============================================
    # ==========================================================================
    def driveCommand(self):
        # Check for slow/medium/fast mode
        self.slow_check()

        # Select between camera feeds with A & B on the xbox controller
        self.camera_select()

        # Calculate drive speeds
        if self.case == 'Drive-Fast':
            self.cmd.lw = self.joy.axes[1]*500 + 1500
            self.cmd.rw = self.joy.axes[4]*-500 + 1500
        elif self.case == 'Drive-Med':
            self.cmd.lw = self.joy.axes[1]*250 + 1500
            self.cmd.rw = self.joy.axes[4]*-250 + 1500
        elif self.case == 'Drive-Slow':
            self.cmd.lw = self.joy.axes[1]*175 + 1500
            self.cmd.rw = self.joy.axes[4]*-175 + 1500

        # Pan and Tilt
        self.cam_pan_tilt()

        # Turn analog video on or off with left bumper
        # On/off is most significant bit in camnum in command
        lb = self.joy.buttons[4]
        if lb == 1:
            self.analog_cam ^= 1
            time.sleep(.25)

        # Publish drive commands
        self.pub1.publish(self.cmd)

    # ==========================================================================
    # INVERSE KINEMATICS CONTROL ===============================================
    # ==========================================================================
    def arm_IK(self):

        self.cmd.q1=int(round(-196+(self.invkin.data[0]*np.pi/180.0+3.0*np.pi/4.0)*(4092/(3*np.pi/2))))
        self.cmd.q2=int(round(3696+(-self.invkin.data[1]*np.pi/180)*(4092/(3*np.pi/4))))
        self.cmd.q3=int(round(-2224+(-self.invkin.data[2]*np.pi/180+3*np.pi/4)*(4092/(np.pi))))
        #self.cmd.q4=int(round(945+(self.invkin.data[3]*np.pi/180+15*np.pi/4)*(4092/(15*np.pi))))
        
        # make sure they are valid joint angles between [0, 4095]
        # turret
        if self.cmd.q1 < 0:
            self.cmd.q1 = 0
        elif self.cmd.q1 > 4095:
            self.cmd.q1 = 4095
        # shoulder
        if self.cmd.q2 < 0:
            self.cmd.q2 = 0
        elif self.cmd.q2 > 4095:
            self.cmd.q2 = 4095
        # elbow
        if self.cmd.q3 < 0:
            self.cmd.q3 = 0
        elif self.cmd.q3 > 4095:
            self.cmd.q3 = 4095

        '''
        # forearm
        if self.cmd.q4 < 0:
            self.cmd.q4 = 0
        elif self.cmd.q4 > 4095:
            self.cmd.q4 = 4095

        # wrist tilt
        if self.wristangle.data[0]>90.0:
            self.wristangle.data[0]=90.0
        if self.wristangle.data[0]<-90.0:
            self.wristangle.data[0]=-90.0
        # wrist rotate
        if self.wristangle.data[1]>180.0:
            self.wristangle.data[1]=180.0
        if self.wristangle.data[1]<-180.0:
            self.wristangle.data[1]=-180.0
        # set wrist publisher data
        self.dyn_cmd.data[0]=math.radians(self.wristangle.data[0])
        self.dyn_cmd.data[1]=math.radians(self.wristangle.data[1])
        '''

        # Select between camera feeds with A & B on the xbox controller
        self.camera_select()
        
        # Pan and Tilt
        self.cam_pan_tilt()

        # Gripper
        self.gripper()

        # Shovel
        if self.joy.axes[2] < 0:
            self.cmd.shovel = self.cmd.shovel-10.0
            if self.cmd.shovel < 1000:
                self.cmd.shovel = 1000
        elif self.joy.axes[5] < 0:
            self.cmd.shovel = self.cmd.shovel+10.0
            if self.cmd.shovel > 2000:
                self.cmd.shovel = 2000

        # Publish arm commands
        self.pub1.publish(self.cmd)
        #self.pub4.publish(self.dyn_cmd)

    # ==========================================================================
    # Xbox Arm Control ===============================================
    # ==========================================================================
    def nofeedback(self):
        # Select between camera feeds with A & B on the xbox controller
        self.camera_select()

        # Pan and Tilt
        self.cam_pan_tilt()

        # Calculate how to command arm (position control)
        
        MAX_RATE = 5*np.pi/180
        DEADZONE = 0.1
        
        # Read in axis values
        axes = [self.joy.axes[0], self.joy.axes[1], self.joy.axes[7],
            self.joy.axes[6], self.joy.axes[4], self.joy.axes[3]]
        
        # Set axis to zero in deadzone
        for ax in axes:
            if abs(ax) < DEADZONE:
                ax = 0
                
        # Update joint angles
        for i in range(0,5):
            self.Xbox_joints.position[i] += axes[i]*MAX_RATE
        
        # Set joint angle limits
        for joint in self.Xbox_joints.position:
            if joint > np.pi:
                joint = np.pi
            elif joint < -np.pi:
                joint = -np.pi
            
                
        
        # Joint 1
        if self.joy.axes[0] < -.5:
            self.cmd.q1 = self.cmd.q1-3
            if self.cmd.q1 < 0:
                self.cmd.q1 = int(round(0))
        elif self.joy.axes[0] > .5:
            self.cmd.q1 = self.cmd.q1+3
            if self.cmd.q1 > 4092:
                self.cmd.q1 = int(round(4092))

        # Joint 2
        if self.joy.axes[1] > .5:
            self.cmd.q2 = self.cmd.q2+5.0
            if self.cmd.q2 > 4092:
                self.cmd.q2 = 4092
        elif self.joy.axes[1] < -.5:
            self.cmd.q2 = self.cmd.q2-5.0
            if self.cmd.q2 < 0:
                self.cmd.q2 = 0

        # Joint 3
        if self.joy.axes[7] < -.9:
            self.cmd.q3 = self.cmd.q3-5.0
            if self.cmd.q3 < 0:
                self.cmd.q3 = 0
        elif self.joy.axes[7] > .9:
            self.cmd.q3 = self.cmd.q3+5.0
            if self.cmd.q3 > 4092:
                self.cmd.q3 = 4092

        # Joint 4
        if self.joy.axes[6] < -.9:
            self.cmd.q4 = self.cmd.q4+5.0
            if self.cmd.q4 > 4092:
                self.cmd.q4 = 4092
        elif self.joy.axes[6] > .9:
            self.cmd.q4 = self.cmd.q4-5.0
            if self.cmd.q4 < 0:
                self.cmd.q4 = 0

        # Send moved angles to IK
        #self.invkin.data[0] = -180/np.pi*((self.cmd.q1-3905)*3*np.pi/2/4092-3*np.pi/4)
        #self.invkin.data[1] = -180/np.pi*((self.cmd.q2-3696)*3*np.pi/4/4092)
        #self.invkin.data[2] = 180/np.pi*((self.cmd.q3-1500)*np.pi/4092-3*np.pi/4)
        #self.invkin.data[3] = 180/np.pi((self.cmd.q4-945)*15*np.pi/4092-15*np.pi/4)
        #self.dyn.data[0]=self.dyn_cmd.data[0]
        #self.dyn.data[1]=self.dyn_cmd.data[1]

        # Joint 5
        if self.joy.axes[4] > .5:
            self.dyn_cmd.data[0] = self.dyn.data[0]+math.radians(5.0)
            if self.dyn_cmd.data[0] > math.radians(89.0):
                self.dyn_cmd.data[0] = math.radians(89.0)
        elif self.joy.axes[4]<-.5:
            self.dyn_cmd.data[0] = self.dyn.data[0]-math.radians(5.0)
            if self.dyn_cmd.data[0] < math.radians(-89.0):
                self.dyn_cmd.data[0] = math.radians(-89.0)

        # Joint 6
        if self.joy.axes[3] > .5:
            self.dyn_cmd.data[1] = self.dyn.data[1]-math.radians(5.0)
            if self.dyn_cmd.data[1] < math.radians(-179.0):
                self.dyn_cmd.data[1] = math.radians(-179.0)
        elif self.joy.axes[3]<-.5:
            self.dyn_cmd.data[1] = self.dyn.data[1]+math.radians(5.0)
            if self.dyn_cmd.data[1] > math.radians(179.0):
                self.dyn_cmd.data[1] = math.radians(179.0)

        #self.dyn_cmd.data[0]=-math.pi/2.0
        #self.dyn_cmd.data[1]=0.0

        # Gripper
        self.gripper()

        # Shovel
        if self.joy.axes[2] < 0:
            self.cmd.shovel = self.cmd.shovel-10.0
            if self.cmd.shovel < 1000:
                self.cmd.shovel = 1000
        elif self.joy.axes[5] < 0:
            self.cmd.shovel = self.cmd.shovel+10.0
            if self.cmd.shovel > 2000:
                self.cmd.shovel = 2000

        #self.cmd.q1 = 1850
        #self.cmd.q2 = 968
        #self.cmd.q3 = 2891
        #self.cmd.q4 = 1968
        #self.cmd.q5 = 0.
        #self.cmd.q6 = 0.0
        

        # Publish arm commands
        self.pub1.publish(self.cmd)
        self.pub4.publish(self.dyn_cmd)
        self.pub_joints.publish(self.Xbox_joints)

    # ==========================================================================
    # Chutes mode ===============================================
    # ==========================================================================
    def chutes(self):
        # 7th bit is enable bit - keep it on
        self.cmd.chutes |= 2^6
        # get chute commands
        c1 = self.joy.buttons[1]
        c2 = self.joy.buttons[2]
        c3 = self.joy.buttons[7]
        c4 = self.joy.buttons[6]
        c5 = self.joy.buttons[5]
        c6 = self.joy.buttons[4]
        # toggle whichever chute button was pressed
        if c1 == 1 or c2 == 1 or c3 == 1 or c4 == 1 or c5 == 1 or c6 == 1:
            self.cmd.chutes ^= c1 | (c2 << 1) | (c3 << 2) | (c4 << 3) | (c5 << 4) | (c6 << 5)
            time.sleep(.25)

        # self.cmd.chutes |= self.joy.buttons[1] | (self.joy.buttons[2] << 1) | (self.joy.buttons[7] << 2) | (self.joy.buttons[6] << 3) | (self.joy.buttons[5] << 4) | (self.joy.buttons[4] << 5) | (1 << 6)
        self.pub1.publish(self.cmd)

    # ==========================================================================
    # Main ===============================================
    # ==========================================================================
if __name__ == '__main__':
    rospy.init_node('xbox_control', anonymous = True)
    hz = 60.0
    rate = rospy.Rate(hz)
    xbox=XBOX()

    while not rospy.is_shutdown():

        if len(xbox.joy.buttons) > 0:
            xbox.check_method()
            if xbox.case == 'Drive-Fast' or xbox.case == 'Drive-Med' or xbox.case == 'Drive-Slow':
                xbox.driveCommand()
            elif xbox.case == 'Arm-xbox':
                xbox.nofeedback()
            elif xbox.case == 'Arm-IK':
                xbox.arm_IK()
            else:
                xbox.chutes()

        xbox.pub3.publish(xbox.case)

        rate.sleep()

