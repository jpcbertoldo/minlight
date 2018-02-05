from deprecated import deprecated
from copy import deepcopy

import numpy as np

from numpy import cos, sin, pi, matrix, sqrt, ndarray
from numpy.linalg import norm

from src.enums import RotationAngleEnum, AngleUnityEnum, RotationOrderEnum


class Vec3(matrix):
    """3D vector. Used to perform vector operations."""

    @staticmethod
    def vec3_from_ndarray(ndarray_: ndarray) -> 'Vec3':
        return Vec3(ndarray_.item(0), ndarray_.item(1), ndarray_.item(2))

    def __new__(cls, x, y, z):
        """Vector 3D from its 3 euclidean coordinates."""
        return super(Vec3, cls).__new__(cls, "{}; {}; {}".format(x, y, z))

    @deprecated
    def set_xyz(self, x, y, z):
        self[0] = x
        self[1] = y
        self[2] = z

    @deprecated
    def get_x(self):
        return self.item(0)

    @deprecated
    def get_y(self):
        return self.item(1)

    @deprecated
    def get_z(self):
        return self.item(2)

    @property
    def x(self) -> float:
        return self.item(0)

    @property
    def y(self) -> float:
        return self.item(1)

    @property
    def z(self) -> float:
        return self.item(2)

    def get_tuple(self):
        """Return a tuple with the 3 coordinates (x, y, z)."""
        return self.item(0), self.item(1), self.item(2)

    @property
    def norm(self) -> float:
        """Euclidean norm of the vector."""
        return norm(self)

    @property
    def direction(self) -> 'Vec3':
        """Return a normalized instance of itself (same direction, norm = 1)."""
        # noinspection PyTypeChecker
        return Vec3.vec3_from_ndarray(deepcopy(self) / self.norm)

    def inner(self, v) -> float:
        """Inner product of self * other ('Scalar product')."""
        x1, y1, z1 = self.get_tuple()
        x2, y2, z2 = v.get_tuple()
        return sqrt(x1 * x2 + y1 * y2 + z1 * z2)

    def cross(self, v: 'Vec3') -> 'Vec3':
        """Cross product of self * other."""
        res = np.cross(self.T, v.T)
        return Vec3(res[0, 0], res[0, 1], res[0, 2])

    def __str__(self):
        """Vec(x, y, z)"""
        return f'Vec3({self["x"]:.1f}, {self["y"]:.1f}, {self["z"]:.1f})'

    def __repr__(self):
        """Vec(x, y, z)"""
        return str(self)

    def __getitem__(self, item):
        """Elements accessible via 0, 1, 2 or x, y, z."""
        # 0 or x
        if item == 0 or str(item).lower() == 'x':
            return self.item(0)
        # 1 or y
        elif item == 1 or str(item).lower() == 'y':
            return self.item(1)
        # 2 or z
        elif item == 2 or str(item).lower() == 'z':
            return self.item(2)
        # error
        else:
            raise IndexError('Elements are only accessible via 0, 1, 2 or x, y, z.')


class Point:
    """Point 3D. It represents an entity (object like)."""

    @staticmethod
    def _point_from_vec3(vec: Vec3) -> 'Point':
        """Create a Point from a Vec3."""
        return Point(*vec.get_tuple())

    def __init__(self, x, y, z, name: str = None):
        """Create a Point from its 3 coordinates (x, y, z)."""
        self._vec3 = Vec3(x, y, z)
        self._name = name

    def set_xyz(self, x, y, z):
        """Set all 3 coordinates at a time."""
        self._vec3 = Vec3(x, y, z)

    @property
    def name(self) -> str:
        return self._name

    @property
    def x(self) -> float:
        """X component getter."""
        return self._vec3.item(0)

    @x.setter
    def x(self, value: float):
        """X component setter."""
        self._vec3 = Vec3(value, self._vec3.y, self._vec3.z)

    @property
    def y(self) -> float:
        """Y component setter."""
        return self._vec3.item(1)

    @y.setter
    def y(self, value: float):
        """Y component setter."""
        self._vec3 = Vec3(self._vec3.x, value, self._vec3.z)

    @property
    def z(self) -> float:
        """Z component setter."""
        return self._vec3.item(2)

    @z.setter
    def z(self, value: float):
        """Z component setter."""
        self._vec3 = Vec3(self._vec3.x, self._vec3.y, value)

    def get_tuple(self):
        """Return a tuple with the 3 coordinates (x, y, z)."""
        return self._vec3.get_tuple()

    def __add__(self, other: Vec3) -> 'Point':
        """Addition of a point and a vector (gives a Point)."""
        return Point._point_from_vec3(self._vec3 + other)

    def __sub__(self, other: 'Point') -> Vec3:
        """Subtraction of two points (gives a Vector)."""
        return self._vec3 - other._vec3

    def __str__(self):
        """(name): Point(x, y, z)."""
        str_ = f"{self._name}: " if self._name else ""
        return str_ + f"Point({self.x:.1f}, {self.y:.1f}, {self.z:.1f})"

    def __repr__(self):
        """Point(x, y, z)."""
        return str(self)


class Orientation:
    """Represent the orientation of a rigid body with 3 rotation angles in a specific order."""

    @staticmethod
    def zero():
        """Zero rotation dans toutes les directions (0, 0, 0)."""
        return Orientation(0, 0, 0)

    def __init__(self, row: float, pitch: float, yaw: float,
                 order: RotationOrderEnum = RotationOrderEnum.ypr,
                 unite: AngleUnityEnum = AngleUnityEnum.degree):
        self._row = row
        self._pitch = pitch
        self._yaw = yaw
        self._order = order
        self._unite = unite
        self._recalculer_matrice = True

        self._matrix_x = RotationMatrix(
            angle=RotationAngleEnum.row,
            valeur=self._row,
            unite=self._unite
        )

        self._matrix_y = RotationMatrix(
            angle=RotationAngleEnum.pitch,
            valeur=self._pitch,
            unite=self._unite
        )

        self._matrix_z = RotationMatrix(
            angle=RotationAngleEnum.yaw,
            valeur=self._yaw,
            unite=self._unite
        )

        if self._order == RotationOrderEnum.rpy:
            self._matrice_rotation = self._matrix_x.dot(self._matrix_y.dot(self._matrix_z))
        elif self._order == RotationOrderEnum.ypr:
            self._matrice_rotation = self._matrix_z.dot(self._matrix_y.dot(self._matrix_x))
        else:
            raise Exception('RotationOrderEnum inconu')

    def incrementer(self, delta_yaw, delta_pitch, delta_row):
        self._yaw += delta_yaw
        self._pitch += delta_pitch
        self._row += delta_row
        self._recalculer_matrice = True

    def get_angles(self):
        def rpy(): return self._row, self._pitch, self._yaw

        def ypr(): return self._yaw, self._pitch, self._row

        switch = {
            RotationOrderEnum.rpy: rpy,
            RotationOrderEnum.ypr: ypr
        }

        return switch[self._order]()

    def get_unite(self):
        return self._unite

    def get_matrice_rotation(self):
        if self._recalculer_matrice:
            self._matrix_x = RotationMatrix(
                angle=RotationAngleEnum.row,
                valeur=self._row,
                unite=self._unite
            )

            self._matrix_y = RotationMatrix(
                angle=RotationAngleEnum.pitch,
                valeur=self._pitch,
                unite=self._unite
            )

            self._matrix_z = RotationMatrix(
                angle=RotationAngleEnum.yaw,
                valeur=self._yaw,
                unite=self._unite
            )

            if self._order == RotationOrderEnum.rpy:
                self._matrice_rotation = self._matrix_x.dot(self._matrix_y.dot(self._matrix_z))
            elif self._order == RotationOrderEnum.ypr:
                self._matrice_rotation = self._matrix_z.dot(self._matrix_y.dot(self._matrix_x))
            self._recalculer_matrice = False
        return self._matrice_rotation

    def get_tuple_angles_pour_inverser_rotation(self):
        return Orientation(
            row=-self._row,
            pitch=-self._pitch,
            yaw=-self._yaw,
            order=RotationOrderEnum.rpy if self._order == RotationOrderEnum.ypr else
            RotationOrderEnum.ypr if self._order == RotationOrderEnum.rpy else
            RotationOrderEnum.unknown,
            unite=self._unite
        )


class RotationMatrix(matrix):
    """Rotation matrix for a specific orientation."""

    _ROTATION_X_STR = '1,   0,    0 ;' + \
                      '0, {c}, -{s} ;' + \
                      '0, {s},  {c}  '

    _ROTATION_Y_STR = ' {c}, 0, {s} ;' + \
                      '   0, 1,   0 ;' + \
                      '-{s}, 0, {c}  '

    _ROTATION_Z_STR = '{c}, -{s}, 0 ;' + \
                      '{s},  {c}, 0 ;' + \
                      '  0,    0, 1  '

    _ROTATION_STR_SWITCH = {
        RotationAngleEnum.row: _ROTATION_X_STR,
        RotationAngleEnum.pitch: _ROTATION_Y_STR,
        RotationAngleEnum.yaw: _ROTATION_Z_STR
    }

    def __new__(cls, angle: RotationAngleEnum, valeur: float, unite: AngleUnityEnum = AngleUnityEnum.degree):
        radians = valeur if unite == AngleUnityEnum.radian else valeur * pi / 180
        str_ = cls._ROTATION_STR_SWITCH[angle]
        str_ = str_.format(s=sin(radians), c=cos(radians))
        return super(RotationMatrix, cls).__new__(cls, str_)

    def __init__(self, angle: RotationAngleEnum, valeur: float, unite: AngleUnityEnum = AngleUnityEnum.degree):
        self._angle = angle
        self._valeur = valeur
        self._unite = unite

    def __mul__(self, other):
        if type(other) == Vec3:
            return Vec3.vec3_from_ndarray(self.dot(other))
        elif type(other) == RotationMatrix:
            return self.dot(other)
        else:
            raise Exception(f'Operation not defined for {type(self)} * {type(other)}.')

    def __add__(self, other):
        raise Exception(f'Operation not defined for {type(self)}.')

    def __sub__(self, other):
        raise Exception(f'Operation not defined for {type(self)}.')

    def __truediv__(self, other):
        raise Exception(f'Operation not defined for {type(self)}.')


class SphericalCoordinates:
    """Point in spherical coordinates (roh, theta, phi)."""

    def __init__(self, roh: float, theta: float, phi: float, unity: AngleUnityEnum = AngleUnityEnum.degree):
        """Roh (mm), theta (unity), phi (unity)."""
        self.roh = roh
        self.theta = theta
        self.phi = phi
        self.unity = unity

    def get_tuple(self, output_unity: AngleUnityEnum = AngleUnityEnum.degree):
        """Return a tuple of (roh, theta, phi) with the angles in the given unity."""

        if output_unity == self.unity:
            return self.roh, self.theta, self.phi

        elif output_unity == AngleUnityEnum.degree and self.unity == AngleUnityEnum.radian:
            return self.roh, self.theta * 180 / pi, self.phi * 180 / pi

        elif output_unity == AngleUnityEnum.radian and self.unity == AngleUnityEnum.degree:
            return self.roh, self.theta * pi / 180, self.phi * pi / 180

        else:
            raise Exception('Could not define the correct unity.')


class SystemeRepereSpherique:
    def __init__(self, centre, ypr_angles):
        self.centre = centre
        self.ypr_angles = ypr_angles

    def get_centre_et_ypr_angles(self):
        return self.centre, self.ypr_angles

    def convertir_en_cartesien(self, coordonnees_spheriques):
        roh, theta, phi = coordonnees_spheriques.get_tuple(output_unity=AngleUnityEnum.radian)

        return Vec3(roh * cos(phi) * cos(theta),
                    roh * cos(phi) * sin(theta),
                    roh * sin(phi))


class Interval:
    def __new__(cls, a, b, step):
        return np.arange(start=a, stop=b, step=step)


class SpaceRechercheAnglesLimites:
    def __init__(self, intervalle_rho, intervalle_phi, intervalle_theta, unite):
        self.intervalle_rho = intervalle_rho
        self.intervalle_phi = intervalle_phi
        self.intervalle_theta = intervalle_theta
        self.unite = unite

    def get_intervalles(self):
        return self.intervalle_rho, self.intervalle_phi, self.intervalle_theta
