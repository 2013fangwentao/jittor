# ***************************************************************
# Copyright (c) 2020 Jittor. Authors: 
#     Guoye Yang <498731903@qq.com>
#     Dun Liang <randonlang@gmail.com>. 
# All Rights Reserved.
# This file is subject to the terms and conditions defined in
# file 'LICENSE.txt', which is part of this source code package.
# ***************************************************************
import unittest
import jittor as jt
import random
import os

mid = 0
if os.uname()[1] == "jittor-ce":
    mid = 1

def resize_and_crop(x, bbox, interpolation="nearest", out_size=[224,224]):
    N, k = bbox.shape
    H, W, C = x.shape
    assert k==4
    shape = [N, out_size[0], out_size[1], C]
    # shape = [N,H,W]
    #      fx   x  cx
    #    +------------>
    # fy | a dx |  b
    #    | dy    
    #  y | -    o  -
    #    |
    # cy | c    |  d
    #    v
    img = x
    bb = [ bbox.reindex(shape, ["i0", str(i)]) for i in range(4) ]
    hid = jt.index(shape, dim=1)
    wid = jt.index(shape, dim=2)
    cid = jt.index(shape, dim=3)
    one = jt.array(1.0).broadcast(shape)
    x = bb[0]*(H-1.0)+hid*((H-1)*1.0/(shape[1]-1))*(bb[2]-bb[0])
    y = bb[1]*(W-1.0)+wid*((W-1)*1.0/(shape[2]-1))*(bb[3]-bb[1])
    if interpolation=="nearest":
        return img.reindex([x.round(), y.round(), cid])
    if interpolation=="bilinear":
        fx, fy = x.floor(), y.floor()
        cx, cy = fx+one, fy+one
        dx, dy = x-fx, y-fy
        a = img.reindex_var([fx, fy, cid])
        b = img.reindex_var([cx, fy, cid])
        c = img.reindex_var([fx, cy, cid])
        d = img.reindex_var([cx, cy, cid])
        dnx, dny = one-dx, one-dy
        ab = dx*b + dnx*a
        cd = dx*d + dnx*c
        o = ab*dny + cd*dy
        return o
    raise(f"Not support {interpolation}")

def test_case(box_num, out_size, time_limit):
    boxes = []
    for i in range(box_num):
        t = [random.random() * 0.9, random.random() * 0.9, random.random() * 0.9, random.random() * 0.9]
        t2 = [min(t[0], t[2]), min(t[1], t[3]), max(t[0], t[2]) + 0.1, max(t[1], t[3]) + 0.1]
        boxes.append(t2)
    img = jt.random([121, 121, 3])
    out = resize_and_crop(img, jt.array(boxes), interpolation='bilinear', out_size=out_size)
    with jt.profile_scope() as rep:
        our_out = out.data
    t = 0
    fused_op_num = 0
    for i in range(1, len(rep)):
        t += float(rep[i][3]) / 1e9
        name = rep[i][0]
        if name.startswith('[') and (not '[graph:]' in name):
            fused_op_num += 1
    assert fused_op_num == 1, fused_op_num
    assert t <= time_limit, t

class TestResizeAndCrop(unittest.TestCase):
    def test(self):
        test_case(100, [224, 224], 0.45)
        test_case(100, [180, 224], 0.3)
        test_case(20, [1024, 1024], [1.2, 1.8][mid])
        test_case(20, [1024, 666], [0.8,1.0][mid])

if __name__ == "__main__":
    unittest.main()