#!/usr/bin/env python
# //==============================================================================
# /*
#     Software License Agreement (BSD License)
#     Copyright (c) 2020-2021 Johns Hopkins University (JHU), Worcester Polytechnic Institute (WPI) All Rights Reserved.


#     All rights reserved.

#     Redistribution and use in source and binary forms, with or without
#     modification, are permitted provided that the following conditions
#     are met:

#     * Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.

#     * Redistributions in binary form must reproduce the above
#     copyright notice, this list of conditions and the following
#     disclaimer in the documentation and/or other materials provided
#     with the distribution.

#     * Neither the name of authors nor the names of its contributors may
#     be used to endorse or promote products derived from this software
#     without specific prior written permission.

#     THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
#     "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#     LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
#     FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
#     COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
#     INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
#     BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#     LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
#     CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
#     LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
#     ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
#     POSSIBILITY OF SUCH DAMAGE.


#     \author    <amunawar@jhu.edu>
#     \author    Adnan Munawar
#     \version   1.0
# */
# //==============================================================================
from surgical_robotics_challenge.kinematics.ecmFK import *
from PyKDL import Frame, Rotation, Vector, Twist
import time


class ECM:
    def __init__(self, client, name):
        self.client = client
        self.name = name
        self.camera_handle = self.client.get_obj_handle(name)
        time.sleep(0.1)

        # Transform of Camera in World
        self._T_c_w = None
        # Transform of World in Camera
        self._T_w_c = None
        self._pose_changed = True
        self._num_joints = 5
        self._update_camera_pose()
        self._T_c_w_init = self._T_c_w
        self._measured_jp = np.array([.0, .0, .0, .0])
        self._measured_cp = None
        self._max_vel = 0.002

    def is_present(self):
        if self.camera_handle is None:
            return False
        else:
            return True

    def get_T_c_w(self):
        self._update_camera_pose()
        return self._T_c_w

    def get_T_w_c(self):
        self._update_camera_pose()
        return self._T_w_c

    def has_pose_changed(self):
        return self._pose_changed

    def set_pose_changed(self):
        self._pose_changed = True

    def _update_camera_pose(self):
        if self._pose_changed is True:
            p = self.camera_handle.get_pos()
            q = self.camera_handle.get_rot()
            P_c_w = Vector(p.x, p.y, p.z)
            R_c_w = Rotation.Quaternion(q.x, q.y, q.z, q.w)
            self._T_c_w = Frame(R_c_w, P_c_w)
            self._T_w_c = self._T_c_w.Inverse()
            self._pose_changed = False

    def servo_cp(self, T_c_w):
        if type(T_c_w) in [np.matrix, np.array]:
            T_c_w = convert_mat_to_frame(T_c_w)

        if self._measured_cp is None:
            self._measured_cp = T_c_w
        pe = T_c_w.p - self._measured_cp.p
        len_pe = pe.Norm()
        pe.Normalize()
        if len_pe > self._max_vel:
            p_cmd = pe * self._max_vel
        else:
            p_cmd = pe * len_pe

        # Check for Rotation
        R_diff = self._measured_cp.M.Inverse() * T_c_w.M
        re = Vector(R_diff.GetRPY()[0], R_diff.GetRPY()[1], R_diff.GetRPY()[2])
        len_re = re.Norm()
        re.Normalize()
        if len_re > self._max_vel:
            r_cmd = re * self._max_vel
        else:
            r_cmd = re * len_re

        T_cmd = Frame()
        T_cmd.p = self._measured_cp.p + p_cmd
        T_cmd.M = self._measured_cp.M * Rotation.RPY(r_cmd[0], r_cmd[1], r_cmd[2])
        self._measured_cp = T_cmd
        self.camera_handle.set_pos(T_cmd.p[0], T_cmd.p[1], T_cmd.p[2])
        rpy = T_cmd.M.GetRPY()
        self.camera_handle.set_rpy(rpy[0], rpy[1], rpy[2])
        self._pose_changed = True

    def servo_cv(self, twist, dt):
        if type(twist) in [np.array, np.ndarray]:
            v = Vector(twist[0], twist[1], twist[2]) * dt
            w = Vector(twist[3], twist[4], twist[5]) * dt
        elif type(twist) is Twist:
            v = twist.vel * dt
            w = twist.rot * dt
        else:
            raise TypeError

        T_c_w = self.get_T_c_w()
        T_cmd = Frame(Rotation.RPY(w[0], w[1], w[2]), v)
        self.servo_cp(T_c_w * T_cmd)
        pass

    def servo_jp(self, jp):
        j0 = jp[0]
        j1 = jp[1]
        j2 = jp[2]
        j3 = jp[3]
        cmd = [j0, j1, j2, j3, 0.0]
        T_t_c = convert_mat_to_frame(compute_FK(cmd, 5)) # Tip if camera frame
        self.servo_cp(self._T_c_w_init * T_t_c)

    def measured_cp(self):
        return self.get_T_c_w()

    def measured_jp(self):
        return self._measured_jp

