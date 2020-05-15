import pytest
import os
import sys
import math
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pytest import approx
from emsndis import geoutils as geo

# WGS84 Semimajor axis length (m)
a = 6378137.0
# WGS84 Semiminor axis length (m)
b = 6356752.3142

def assert_coord(result, solution):
  assert len(result) == len(solution)
  for i in range(len(result)):
    assert pytest.approx(result[i]) == solution[i]

def test_lla2XYZ():
  assert geo.lla2XYZ((0,0,0)) == approx((a,0,0))
  assert geo.lla2XYZ((0,90,0)) == approx((0,a,0), abs=1e-6)
  # 30,000 m over Adeleide
  assert geo.lla2XYZ((-34.9,138.5,30000)) == approx((-3.94e6, 3.49e6, -3.65e6), abs=1e4)
  # 30,000 m over Sydney
  assert geo.lla2XYZ((-33.9,151.2,30000)) == approx((-4.67e6, 2.57e6, -3.55e6), abs=1e4)

def test_xyz2lla():
  assert geo.xyz2lla((a,0,0)) == approx((0,0,0))
  assert geo.xyz2lla((0,a,0)) == approx((0,90,0))
  pos = (30,30,30)
  assert geo.xyz2lla(geo.lla2XYZ(pos)) == approx(pos)

def test_qrotate():
  assert geo.qrotate((2,0,0),math.pi/2,(0,1,0)) == approx((0,0,-2), abs=1e-5)

def test_rotate_zyx():
  pos = (-34.9, 138.5, 10000)
  euler = (135, 20, 30)
  euler_r = [geo.deg2rad(a) for a in euler]
  lat, lon, alt = pos
  ned = geo.get_ned(lat, lon)
  xyz = geo.rotate_zyx(ned, euler_r)
  x, y, z = xyz
  assert x == approx([-0.366, -0.564, -0.741], abs=1e-3)
  assert y == approx([0.928, - 0.165, -0.333], abs=1e-3)
  assert z == approx([0.065, -0.809, 0.584], abs=1e-3)

def test_to_dis():
  pos = (0,0,0)
  att = (0,90,0)
  xyz, ea = geo.to_dis(pos,att)
  assert xyz == approx((a,0,0))
  assert ea == approx((0,0,0))
  pos = (0,0,0)
  att = (-90,0,0)
  # Aedeleide
  pos = (-34.9, 138.5, 10000)
  att = (135, 20, 30)
  xyz, euler = geo.to_dis(pos, att)
  euler = [geo.rad2deg(a) for a in euler]
  assert euler == approx([-123.0, 47.8, -29.7], abs=1e-1)

def test_from_dis_cs():
  pos = (0,0,0)
  att = (0,90,0)
  xyz, ea = geo.to_dis(pos,att)
  pos2, att2 = geo.from_dis(xyz, ea)
  assert pos2 == pos
  assert att == approx(att2, abs=1e-1)
  pos = (-34.9, 138.5, 10000)
  att = (135, 20, 30)
  xyz, euler = geo.to_dis(pos, att)
  pos2, att2 = geo.from_dis(xyz, euler)
  assert pos2 == approx(pos, abs=1e-2)
  assert att == approx(att2, abs=1e-1)

def test_xyz2XYZ():
  position = (0,0,0)
  attitude = (0,0,0) # Heading North, no pitch or roll
  xyz = (10, 20, 30)
  x, y , z = xyz
  X, Y, Z = geo.lla2XYZ(position)
  Xp, Yp, Zp = geo.xyz2XYZ(position, attitude, xyz)
  assert Xp == X - z
  assert Yp == Y + y
  assert Zp == Z + x

  position = (0,0,0)
  attitude = (180,0,0) # Heading South, no pitch or roll.
  xyz = (10, 20, 30)
  x, y , z = xyz
  X, Y, Z = geo.lla2XYZ(position)
  Xp, Yp, Zp = geo.xyz2XYZ(position, attitude, xyz)
  assert Xp == approx(X - z, abs=1e-2)
  assert Yp == approx(Y - y, abs=1e-2)
  assert Zp == approx(Z - x, abs=1e-2)

  position = (0,90,0)
  attitude = (180,0,0) # Heading South, no pitch or roll.
  xyz = (10, 20, 30)
  x, y , z = xyz
  X, Y, Z = geo.lla2XYZ(position)
  Xp, Yp, Zp = geo.xyz2XYZ(position, attitude, xyz)
  assert Xp == approx(X + y, abs=1e-2)
  assert Yp == approx(Y - z, abs=1e-2)
  assert Zp == approx(Z - x, abs=1e-2)




