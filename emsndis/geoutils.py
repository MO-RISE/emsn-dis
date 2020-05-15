"""
emsndis.geoutils
~~~~~~~~~~~~~~~~~
A module containing utilities for Geospatial calculations.

Reference:

[1] Koks, D. (2008). Using Rotations to Build Aerospace Coordinate Systems.
  Australian Goverment Department of Defence.
"""

import numpy as np

# WGS84 Semimajor axis length (m)
a = 6378137

# WGS84 Semiminor axis length (m)
b = 6356752.3142

def rad2deg(rad):
  return rad * 180 / np.pi

def deg2rad(deg):
  return deg * np.pi / 180

def lla2XYZ(lla):
  """Transform polar-type (latitude, longitude, altitude) cooordinates to
  Earth Centered Earth Fixed (ECEF) coordinates (X, Y, Z) using the geodetic
  WGS84.

  Arguments:

    lla (tuple)
      Contains: (latitude(deg), longitude(deg), altitude (m))

  Output:
     (X (m), Y (m), Z (m))

  Usage:

    >>> lla2XYZ((0,0,0))
    (6378137.0,0,0)
  """
  lat = deg2rad(lla[0])
  lon = deg2rad(lla[1])
  h = lla[2]
  X = (a / np.sqrt(np.cos(lat)**2 + (b**2 / a**2) * np.sin(lat)**2) + h) * \
    np.cos(lat) * np.cos(lon)
  Y = (a / np.sqrt(np.cos(lat)**2 + (b**2 / a**2) * np.sin(lat)**2) + h) * \
    np.cos(lat) * np.sin(lon)
  Z = (b / np.sqrt((a**2 / b**2) * np.cos(lat)**2 + np.sin(lat)**2) + h) * \
    np.sin(lat)
  return (X, Y, Z)

def xyz2lla(xyz, tolerance=1e-9):
  x, y, z = xyz
  lon = np.arctan2(y, x)
  if z == 0:
    lat = 0
  else:
    lat = np.arctan((a**2 * z)/(b**2 * np.sqrt(x**2 + y**2)))
    p_lat = 90
    while abs(lat - p_lat) >= tolerance:
      p_lat = lat
      lat =np.arctan(a**2 * np.sin(lat)**2 / (b**2 * np.sin(lat) * \
        np.cos(lat) +(np.sqrt(x**2 + y**2) * np.sin(lat) - z * np.cos(lat)) * \
        np.sqrt(a**2 * np.cos(lat)**2 + b**2 * np.sin(lat)**2 )))
  h = np.sqrt(x**2 + y**2) / np.cos(lat) - \
    a**2 / np.sqrt(a**2 * np.cos(lat)**2 + b**2 * np.sin(lat)**2)
  return (rad2deg(lat), rad2deg(lon), h)


def qrotate(v, w, n):
  """Rotate a vector about an axis a certain angle with quaternions.

  Arguments:

    v (x, y, z)
      Vector to be rotated.
    w (rad)
      Rotation angle.
    n (x, y, z)
      Rotation axis.

  Output:
    (x_n, y_n, z_n)

  """
  q = _quaternion(w,n)
  qn = _quaternion(w, (-n[0], -n[1], -n[2]))
  b = np.array((0,v[0],v[1],v[2]))
  ra = _mult_quaternion(q,b)
  rb = _mult_quaternion(ra,qn)
  return np.array(rb[1:])

def _mult_quaternion(qa, qb):
  """Multiply two quaternions.
  """
  a0 = qa[0]
  a  = qa[1:]
  b0 = qb[0]
  b  = qb[1:]
  n = a0*b + b0*a + np.cross(a,b)
  w = a0*b0 - np.dot(a,b)
  return np.array((w,n[0],n[1],n[2]))

def _quaternion(w, n):
  """Create a quaternion.
  """
  q = (np.cos(w/2), n[0]*np.sin(w/2), n[1]*np.sin(w/2), n[2]*np.sin(w/2))
  return np.array(q)

def get_ned(lat,lon):
  """Get the North-East-Down vectors at a coordinate.
  """
  no = (0,0,1)
  eo = (0,1,0)
  e = qrotate(eo,deg2rad(lon),no)
  n = qrotate(no,deg2rad(lat),-e)
  d = np.cross(n,e)
  return n, e, d

def to_dis(position, attitude, deg=True):
  if deg:
    attitude = [deg2rad(a) for a in attitude]
  lat, lon, alt = position
  psi, theta, phi = attitude
  ned = get_ned(lat, lon)
  xyz_local = rotate_zyx(ned, attitude)
  xyz_global = ((1,0,0),(0,1,0),(0,0,1))

  euler = get_euler(xyz_global, xyz_local)
  return (lla2XYZ(position), euler)

def from_dis(xyz, euler, deg=True):
  lat, lon, alt = xyz2lla(xyz)
  xyz_global = ((1,0,0), (0,1,0), (0,0,1))
  xyz_local = rotate_zyx(xyz_global, euler)
  ned = get_ned(lat, lon)
  attitude = get_euler(ned, xyz_local)
  if deg:
    attitude = [rad2deg(a) for a in attitude]
  return (lat, lon, alt), attitude

def xyz2XYZ(position, attitude, p, deg=True):
  """
  Transform the coordinates of a point in the DIS local coordinate system
  (xyz) to the DIS world coordinate system (XYZ).

  Arguments:
  -----------

  position:
    Position of an entity in as a (latitude, longitude, altitude) tuple.
    Latitude and longitude in degrees and altitude in meters.

  attitude:
    Orientation of an entity with respect to its local coordinate system
    as (yaw, pitch, roll) angles in radians.

  xyz:
    Coordinates of a point in the local coordinate system of an entity.
    All coordinates in meters.

  Returns:
  --------

  XYZ:
    Coordinates of the point in the DIS world coordinate system.

  """
  lat, lon, alt = position
  dx, dy, dz = p
  if deg:
    attitude = [deg2rad(a) for a in attitude]
  XYZ = lla2XYZ(position)
  ned = get_ned(lat, lon)
  x, y, z = rotate_zyx(ned, attitude)
  XYZp = np.array(XYZ) + x*dx + y*dy + z*dz
  return XYZp


def rotate_zyx(cs, euler):
  x0, y0, z0 = cs
  psi, theta, phi = euler
  x1 = qrotate(x0, psi, z0)
  y1 = qrotate(y0, psi, z0)
  z1 = z0
  x2 = qrotate(x1, theta, y1)
  y2 = y1
  z2 = qrotate(z1, theta, y1)
  x3 = x2
  y3 = qrotate(y2, phi, x2)
  z3 = qrotate(z2, phi, x2)
  return (x3, y3, z3)

def get_euler(xyz0, xyz3):
  x0, y0, z0 = xyz0
  x3, y3, z3 = xyz3
  psi = np.arctan2(np.dot(x3,y0), np.dot(x3,x0))
  theta = np.arctan2(-np.dot(x3,z0), \
    np.sqrt(np.dot(x3,x0)**2 + np.dot(x3,y0)**2))
  y2 = qrotate(y0, psi, z0)
  z2 = qrotate(z0, theta, y2)
  phi = np.arctan2(np.dot(y3,z2), np.dot(y3,y2))
  return (psi, theta, phi)
