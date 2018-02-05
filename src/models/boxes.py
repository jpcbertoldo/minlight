from OpenGL.GL import *
from numpy import arcsin, degrees, radians, cos, sin, sqrt

from src.enums import RotationOrderEnum, AngleUnityEnum
from src.math_entities import Vec3, Orientation
from src.toolbox.useful import get_plane_normal
from src.visualization.outils import Surface


class BoxDimensions:
    """Length, width, height. Imutable."""

    def __init__(self, length: float, width: float, height: float):
        """Everythin in mm."""
        self._dimensions = {'length': length, 'width': width, 'height': height}

    def __getitem__(self, key):
        """Key e {length, width, height}."""
        return self._dimensions[key]

    def get_tuple(self):
        """Return the tuple (length, width, height)."""
        return self._dimensions['length'], self._dimensions['width'], self._dimensions['height']

    @property
    def length(self) -> float:
        return self._dimensions['length']

    @property
    def width(self) -> float:
        return self._dimensions['width']

    @property
    def height(self) -> float:
        return self._dimensions['height']


class Box:
    noms_sommets_pave = ('S000', 'S001', 'S010', 'S011', 'S100', 'S101', 'S110', 'S111')

    @staticmethod
    def point_appartient_pave_origine(point, dimensions):
        """
        Fonction qui teste si un point est dans le volume d'un pavé localisé à l'origine.
        :param point:
        :param dimensions: (dictionnaire) length, width, height du pave de la source
        :return: False/True
        """

        long, larg, haut = dimensions.get_tuple()

        demi_long, demi_larg, demi_haut = long / 2, larg / 2, haut / 2

        x, y, z = point.get_tuple()

        return -demi_long <= x <= demi_long and \
               -demi_larg <= y <= demi_larg and \
               -demi_haut <= z <= demi_haut

    def __init__(self, centre, ypr_angles, dimensions):
        self.centre = centre
        self.ypr_angles = ypr_angles
        self.dimensions = dimensions
        self.sommets_origine = self.set_sommets_pave_origine()
        self.sommets = self.get_sommets_pave()

    def rotate(self, delta_yaw, delta_pitch, delta_row):
        self.ypr_angles.incrementer(delta_yaw, delta_pitch, delta_row)
        self.update_sommets()

    def translate(self, delta_x, delta_y, delta_z):
        self.centre += Vec3(delta_x, delta_y, delta_z)
        self.update_sommets()

    def set_position(self, centre):
        self.centre = centre
        self.update_sommets()

    def set_angles(self, ypr_angles):
        self.ypr_angles = ypr_angles
        self.update_sommets()

    def changer_systeme_repere_pave_vers_globale(self, point):
        # matrice de rotation
        Rot = self.ypr_angles.get_matrice_rotation()

        res = (Rot * point) + self.centre

        # il faut faire ça sinon le retour est une matrice rot
        return Vec3(res.__getitem__((0, 0)), res.__getitem__((1, 0)), res.__getitem__((2, 0)))

    def set_sommets_pave_origine(self):
        # dimensions
        long, larg, haut = self.dimensions.get_tuple()

        # sommets (coins) du pavé centré dans l'origine
        s000 = Vec3(- long / 2, - larg / 2, - haut / 2)
        s100 = Vec3(+ long / 2, - larg / 2, - haut / 2)
        s010 = Vec3(- long / 2, + larg / 2, - haut / 2)
        s110 = Vec3(+ long / 2, + larg / 2, - haut / 2)
        s001 = Vec3(- long / 2, - larg / 2, + haut / 2)
        s101 = Vec3(+ long / 2, - larg / 2, + haut / 2)
        s011 = Vec3(- long / 2, + larg / 2, + haut / 2)
        s111 = Vec3(+ long / 2, + larg / 2, + haut / 2)

        # sommets (coins) de la source repérés par rapport à son centre
        return [s000, s001, s010, s011, s100, s101, s110, s111]

    def sommets_pave_origine(self):
        return self.sommets_origine

    def get_centre(self):
        return self.centre

    def get_sommets_pave(self):
        """
        convention utilisé pour les rotations : z-y’-x″ (intrinsic rotations) = Yaw, pitch, and roll rotations
        http://planning.cs.uiuc.edu/node102.html
        http://planning.cs.uiuc.edu/node104.html
        https://en.wikipedia.org/wiki/Euler_angles#Tait.E2.80.93Bryan_angles
        https://en.wikipedia.org/wiki/Euler_angles#Rotation_matrix

        On suppose qu'on veut orienter le centre de la source par des angles
        et la position du centre, on calcule les positios des sommets (les coins de la source).
        :return: liste des sommets de la source par rapport au système de repère de la chambre
        """

        s_origine = self.sommets_pave_origine()
        return [self.changer_systeme_repere_pave_vers_globale(s) for s in s_origine]

    def sommets_pave(self):
        return self.sommets

    def get_dictionnaire_sommets(self):
        return {nom: sommet for nom, sommet in zip(self.noms_sommets_pave, self.sommets)}

    def point_appartient_pave(self, point):
        '''
        Fonction qui teste si un point est dans le volume d'un pavé localisé à l'origine.
        :param dimensions: (dictionnaire) length, width, height du pave de la source
        :param centre: centre du pavé repéré dans le sys de coordonnées globale
        :return: False/True
        '''
        Rot = self.ypr_angles \
            .get_tuple_angles_pour_inverser_rotation() \
            .get_matrice_rotation()

        point_repere_pave = Rot * (point - self.centre)

        # il faut faire ça parce que l'operation cidessus renvoie une matrice rotation
        point_repere_pave = Vec3(point_repere_pave.__getitem__((0, 0)),
                                 point_repere_pave.__getitem__((1, 0)),
                                 point_repere_pave.__getitem__((2, 0)))

        return self.point_appartient_pave_origine(point_repere_pave, self.dimensions)

    def test_colision_en_autre_pave(self, pave2, k_discretisation_arete=10):

        '''
        Tests if there are points on pave1's faces inside pave2.
        the function needs to be called twice to be sure that there are no intersections
        pave1: dictionary with dimensions(dictionary),centre(matrix 3x1), ypr_angles(dictionary)
        k: (k+1)^2 = number of points to be tested on each face, the greater the k, the plus reliable the result
        '''

        k = k_discretisation_arete

        length, width, height = self.dimensions.get_tuple()

        points_to_be_tested = []

        for i in range(k + 1):
            for j in range(k + 1):
                x = i * length / k
                z = j * height / k
                points_to_be_tested.append(Vec3(x, 0, z))
                points_to_be_tested.append(Vec3(x, width, z))

                x = i * length / k
                y = j * width / k
                points_to_be_tested.append(Vec3(x, y, 0))
                points_to_be_tested.append(Vec3(x, y, height))

                y = i * width / k
                z = j * height / k
                points_to_be_tested.append(Vec3(0, y, z))
                points_to_be_tested.append(Vec3(length, y, z))

        for index in range(len(points_to_be_tested)):
            points_to_be_tested[index] = (self.ypr_angles.get_matrice_rotation()) * points_to_be_tested[index]

            # next line converts from 3d rotation matrix to vecteur3d
            points_to_be_tested[index] = Vec3(points_to_be_tested[index].__getitem__((0, 0)),
                                              points_to_be_tested[index].__getitem__((1, 0)),
                                              points_to_be_tested[index].__getitem__((2, 0)))

            points_to_be_tested[index] = points_to_be_tested[index] + self.centre - Vec3(length / 2, width / 2,
                                                                                         height / 2)

            if pave2.point_appartient_pave(points_to_be_tested[index]):
                return True

        return False

    def intersection_avec_autre_pave(self, pave, k_discretisation_arete=10):

        """
        Tests if there are inserctions between pave1 and pave2,
        pave1: dictionary with dimensions(dictionary),centre(matrix 3x1), ypr_angles(dictionary)
        pave2: dictionary with dimensions(dictionary),centre(matrix 3x1), ypr_angles(dictionary)
        k: (k+1)^2 = number of points to be tested on each face, the greater the k, the more reliable the result
        return True if there are no intersections, returns False otherwise
        """
        if self.test_colision_en_autre_pave(pave, k_discretisation_arete):
            return True

        if pave.test_colision_en_autre_pave(self, k_discretisation_arete):
            return True

        return False
        # FIX POINT_APPARTIENT_PAVE AND POINT_3d

    def entierement_dans_autre_pave(self, autre):
        return all(autre.point_appartient_pave(sommet) for sommet in self.sommets_pave())

    def changer_a_partir_de_coordonnes_spheriques(self, coordonnees_spheriques, systeme_spherique):
        '''
        source changed to self, not sure if it works
        '''
        roh, theta, phi = coordonnees_spheriques.get_coordonnees_spheriques(unite_desiree=AngleUnityEnum.degree)

        # p = centre de la source pour le systeme cartesien à partir du quel le spherique est defini
        p = systeme_spherique.convertir_en_cartesien(coordonnees_spheriques)

        centre_systeme, ypr_angles_systeme = systeme_spherique.get_centre_et_ypr_angles()

        Rot = ypr_angles_systeme.get_tuple_angles_pour_inverser_rotation() \
            .get_matrice_rotation()

        res = Rot * p + centre_systeme

        # il faut faire ça sinon le retour est une matrice rot
        self.centre = Vec3(res.__getitem__((0, 0)), res.__getitem__((1, 0)), res.__getitem__((2, 0)))

        self.ypr_angles = \
            Orientation(
                row=0,
                pitch=phi,
                yaw=theta,
                sequence=RotationOrderEnum.ypr,
                unite=AngleUnityEnum.degree  # !!!!!!!!!!!!!!!!!!!!!!!!
            )

    def update_sommets(self):
        newSommets = []
        Rot = self.ypr_angles.get_matrice_rotation()
        for sommet in self.sommets_origine:
            newPoint = (Rot * sommet) + self.centre
            newSommets.append(newPoint)
        for i in range(len(newSommets)):
            self.sommets[i].set_xyz(newSommets[i].item(0), newSommets[i].item(1), newSommets[i].item(2))

    def draw(self, origin, color=(0.45, 0.45, 0.45, 1.0), drawFaces=True):
        edges = (
            (0, 1),
            (0, 2),
            (0, 4),
            (1, 3),
            (1, 5),
            (7, 3),
            (7, 5),
            (7, 6),
            (6, 2),
            (6, 4),
            (3, 2),
            (5, 4)
        )
        surfaces = (
            (0, 2, 6, 4),
            (5, 7, 3, 1),
            (4, 6, 7, 5),
            (1, 3, 2, 0),
            (6, 2, 3, 7),
            (1, 0, 4, 5)
        )

        verticies = self.sommets_pave()
        verticiesInOrigin = []

        for v in verticies:
            verticiesInOrigin.append(v - origin)

        if drawFaces:
            glBegin(GL_QUADS)
            for surface in surfaces:
                normal = get_plane_normal(surface, self.sommets, self.centre)
                normal_tuple = normal.get_tuple()
                for vertex in surface:
                    glColor4fv(color)
                    glNormal3fv(normal_tuple)
                    glVertex3fv(verticiesInOrigin[vertex])
            glEnd()

        glBegin(GL_LINES)
        for edge in edges:
            for vertex in edge:
                glColor4fv((0.0, 0.0, 0.0, 1.0))
                glNormal3fv((0.0, 0.0, 0.0))
                glVertex3fv(verticiesInOrigin[vertex])
        glEnd()


class Chambre(Box):
    def __init__(self, centre, ypr_angles, dimensions):
        super().__init__(centre, ypr_angles, dimensions)

    def draw(self, origin, color=(0.2, 0.2, 0.2, 1.0), drawFaces=True):
        edges = (
            (0, 1),
            (0, 2),
            (0, 4),
            (1, 3),
            (1, 5),
            (7, 3),
            (7, 5),
            (7, 6),
            (6, 2),
            (6, 4),
            (3, 2),
            (5, 4)
        )
        ground = (4, 6, 2, 0)

        normal = get_plane_normal(ground, self.sommets, -self.centre)
        normal_tuple = normal.get_tuple()

        glBegin(GL_QUADS)
        for vertex in ground:
            glColor4fv(color)
            glNormal3fv(normal_tuple)
            glVertex3fv(self.sommets[vertex] - origin)
        glEnd()

        glBegin(GL_LINES)
        for edge in edges:
            for vertex in edge:
                glColor4fv((0.0, 0.0, 0.0, 1.0))
                glNormal3fv((0.0, 0.0, 0.0))
                glVertex3fv(self.sommets[vertex] - origin)
        glEnd()


class Source(Box):
    def __init__(self, centre, ypr_angles, dimensions):
        super().__init__(centre, ypr_angles, dimensions)
        self.create_parable()

    def get_light_radius(self):
        length, width, height = self.dimensions.get_tuple()
        return height / 2

    def get_light_centre(self):

        return (self.sommets[5] + self.sommets[7] + self.sommets[6] + self.sommets[
            4]) / 4  # 5,7,6,4 are the verticies of the light face

    def get_light_direction(self):
        return (self.get_light_centre() - self.centre).direction()

    def create_parable(self):  # creates visualization of the parable, must finish!!!!!!!
        length, width, height = self.dimensions.get_tuple()
        r = ((height * height / 4) + length * length) / (2 * length)
        self.angle_ouverture = degrees(arcsin(height / (2 * r)))
        self.points_parable_origin = []
        self.points_parable = []
        rotation = Orientation(0, 90, 0)
        self.points_per_level = 10
        self.angle_levels = 10
        matRot = rotation.get_matrice_rotation()
        for theta in range(0, int(self.angle_ouverture), self.angle_levels):
            for phi in range(0, 360, int(360 / self.points_per_level)):
                theta_rad = radians(theta)
                phi_rad = radians(phi)
                x0 = r * sin(theta_rad) * cos(phi_rad)
                y0 = r * sin(theta_rad) * sin(phi_rad)
                z0 = r * (1 - sqrt(1 - sin(theta_rad) * sin(theta_rad)))
                p = Vec3(x0, y0, z0)
                p = matRot * p - Vec3(length / 2, 0, 0)
                p = Vec3(p.item(0), p.item(1), p.item(2))
                p2 = Vec3(p.item(0), p.item(1), p.item(2))
                self.points_parable_origin.append(p)
                self.points_parable.append(p2)
        self.squares_edges = []
        # for()
        self.update_sommets()

    def update_sommets(self):
        length, width, height = self.dimensions.get_tuple()
        newSommets = []
        newSommetsParable = []
        Rot = self.ypr_angles.get_matrice_rotation()
        for sommet in self.sommets_origine:
            newPoint = (Rot * sommet) + self.centre
            newSommets.append(newPoint)
        for i in range(len(newSommets)):
            self.sommets[i].set_xyz(newSommets[i].item(0), newSommets[i].item(1), newSommets[i].item(2))

        for sommet in self.points_parable_origin:
            newPoint = (Rot * sommet) + self.centre
            newSommetsParable.append(newPoint)
        for i in range(len(self.points_parable)):
            self.points_parable[i].set_xyz(newSommetsParable[i].item(0), newSommetsParable[i].item(1),
                                           newSommetsParable[i].item(2))


            #    def draw_parable(self):

    def draw_parable(self, origin):
        number_levels = int(self.angle_ouverture / self.angle_levels)
        #    self.points_per_level = len(self.points_parable)
        glBegin(GL_QUADS)
        for j in range(number_levels - 2):
            for i in range(self.points_per_level):
                glColor4fv((0.95, 0.95, 0, 1.0))
                glNormal3fv((0.0, 0.0, 0.0))
                glVertex3fv(self.points_parable[i % self.points_per_level + (j + 1) * self.points_per_level] - origin)
                glVertex3fv(self.points_parable[i + 1 + (j + 1) * self.points_per_level] - origin)
                glVertex3fv(self.points_parable[(i + 1) % self.points_per_level + j * self.points_per_level] - origin)
                glVertex3fv(self.points_parable[i + j * self.points_per_level] - origin)
        glEnd()
        glBegin(GL_LINES)
        for j in range(number_levels):
            for i in range(self.points_per_level):
                glColor4fv((0.5, 0.5, 0.5, 1.0))
                glNormal3fv((0.0, 0.0, 0.0))
                glVertex3fv(self.points_parable[i + j * self.points_per_level] - origin)
                glVertex3fv(self.points_parable[(i + 1) % self.points_per_level + j * self.points_per_level] - origin)
        glEnd()

        glBegin(GL_LINES)
        for i in range(len(self.points_parable) - self.points_per_level):
            for j in (i, i + self.points_per_level):
                glColor4fv((0.5, 0.5, 0.5, 1.0))
                glNormal3fv((0.0, 0.0, 0.0))
                glVertex3fv(self.points_parable[j] - origin)
        glEnd()

    def draw(self, origin):
        self.draw_parable(origin)
        edges = (
            (0, 1),
            (0, 2),
            (0, 4),
            (1, 3),
            (1, 5),
            (7, 3),
            (7, 5),
            (7, 6),
            (6, 2),
            (6, 4),
            (3, 2),
            (5, 4)
        )

        #    edges = ()
        surfaces = (
            (1, 3, 2, 0),
            (1, 0, 4, 5),
            (0, 2, 6, 4),
            (1, 3, 7, 5),
            (7, 3, 2, 6)
        )

        light = (1, 3, 2, 0)

        normal = get_plane_normal(light, self.sommets, self.centre)
        normal_tuple = normal.get_tuple()
        glBegin(GL_QUADS)
        for vertex in light:
            glNormal3fv(normal_tuple)
            glColor4fv((1.0, 1.0, 1.0, 1.0))
            glVertex3fv(self.sommets[vertex] - origin)
        glEnd()

        glBegin(GL_LINES)
        for edge in edges:
            for vertex in edge:
                glColor4fv((0.0, 0.0, 0.0, 1.0))
                glNormal3fv((0.0, 0.0, 0.0))
                glVertex3fv(self.sommets[vertex] - origin)
        glEnd()


class Maisonette(Box):
    def __init__(self, centre, ypr_angles, dimensions, window_dimensions, wall_width=150):
        super().__init__(centre, ypr_angles, dimensions)
        self.window_dimensions = window_dimensions
        self.wall_width = wall_width
        self.set_sommets_inside()

    def set_sommets_inside(self):
        S0 = self.sommets[0] - Vec3(-self.wall_width, -self.wall_width, -self.wall_width)
        S1 = self.sommets[1] - Vec3(-self.wall_width, -self.wall_width, self.wall_width)
        S2 = self.sommets[2] - Vec3(-self.wall_width, self.wall_width, -self.wall_width)
        S3 = self.sommets[3] - Vec3(-self.wall_width, self.wall_width, self.wall_width)

        S4 = self.sommets[4] - Vec3(self.wall_width, -self.wall_width, -self.wall_width)
        S5 = self.sommets[5] - Vec3(self.wall_width, -self.wall_width, self.wall_width)
        S6 = self.sommets[6] - Vec3(self.wall_width, self.wall_width, -self.wall_width)
        S7 = self.sommets[7] - Vec3(self.wall_width, self.wall_width, self.wall_width)

        S4 = self.sommets[4] - Vec3(self.wall_width, -self.wall_width, -self.wall_width)
        S5 = self.sommets[5] - Vec3(self.wall_width, -self.wall_width, self.wall_width)
        S6 = self.sommets[6] - Vec3(self.wall_width, self.wall_width, -self.wall_width)
        S7 = self.sommets[7] - Vec3(self.wall_width, self.wall_width, self.wall_width)

        length, width, height = self.dimensions.get_tuple()

        # window_inside_points

        S8 = self.sommets[1] - Vec3(-self.wall_width, -(width / 2 - self.window_dimensions['width'] / 2),
                                    (height / 2 - self.window_dimensions['height'] / 2))
        S9 = self.sommets[3] - Vec3(-self.wall_width, (width / 2 - self.window_dimensions['width'] / 2),
                                    (height / 2 - self.window_dimensions['height'] / 2))
        S10 = self.sommets[2] - Vec3(-self.wall_width, (width / 2 - self.window_dimensions['width'] / 2),
                                     -(height / 2 - self.window_dimensions['height'] / 2))
        S11 = self.sommets[0] - Vec3(-self.wall_width, -(width / 2 - self.window_dimensions['width'] / 2),
                                     -(height / 2 - self.window_dimensions['height'] / 2))

        #  window_outside_points

        S12 = self.sommets[1] - Vec3(0, -(width / 2 - self.window_dimensions['width'] / 2),
                                     (height / 2 - self.window_dimensions['height'] / 2))
        S13 = self.sommets[3] - Vec3(0, (width / 2 - self.window_dimensions['width'] / 2),
                                     (height / 2 - self.window_dimensions['height'] / 2))
        S14 = self.sommets[2] - Vec3(0, (width / 2 - self.window_dimensions['width'] / 2),
                                     -(height / 2 - self.window_dimensions['height'] / 2))
        S15 = self.sommets[0] - Vec3(0, -(width / 2 - self.window_dimensions['width'] / 2),
                                     -(height / 2 - self.window_dimensions['height'] / 2))

        S16 = self.sommets[0]
        S17 = self.sommets[1]
        S18 = self.sommets[2]
        S19 = self.sommets[3]

        self.sommets_extras = [S0, S1, S2, S3, S4, S5, S6, S7, S8, S9, S10, S11, S12, S13, S14, S15, S16, S17, S18, S19]

    def draw_inside(self, origin):
        edges = (
            (0, 1),
            (0, 2),
            (0, 4),
            (1, 3),
            (1, 5),
            (7, 3),
            (7, 5),
            (7, 6),
            (6, 2),
            (6, 4),
            (3, 2),
            (5, 4),
            # windows inside
            (8, 9),
            (9, 10),
            (10, 11),
            (11, 8),
            # window outside
            (12, 13),
            (13, 14),
            (14, 15),
            (15, 12),
            # wall between windows
            (8, 12),
            (9, 13),
            (10, 14),
            (11, 15)

        )
        surfaces_inside = (
            #####inside
            Surface((5, 7, 6, 4), (-1, 0, 0)),
            Surface((5, 4, 0, 1), (0, 1, 0)),
            Surface((7, 3, 2, 6), (0, -1, 0)),
            Surface((4, 6, 2, 0), (0, 0, 1)),
            Surface((1, 3, 7, 5), (0, 0, 1))
        )
        surfaces_outside = (
            #####outside front face
            Surface((16, 17, 12, 15), (-1, 0, 0)),
            Surface((19, 13, 12, 17), (-1, 0, 0)),
            Surface((13, 19, 18, 14), (-1, 0, 0)),
            Surface((16, 15, 14, 18), (-1, 0, 0)),
            #####
            Surface((8, 11, 15, 12), (0, -1, 0)),
            Surface((12, 13, 9, 8), (0, 0, -1)),
            Surface((13, 14, 10, 9), (0, 1, 0)),
            Surface((14, 15, 11, 10), (0, 0, 1))
        )
        verticies = self.sommets_extras
        verticiesInOrigin = []
        for v in verticies:
            verticiesInOrigin.append(v - origin)
        glBegin(GL_QUADS)
        for surface in surfaces_outside:
            for vertex in surface.edges:
                glColor4fv((0.4, 0.4, 0.4, 1.0))
                glNormal3fv(surface.normal)
                glVertex3fv(verticiesInOrigin[vertex])
        for surface in surfaces_inside:
            for vertex in surface.edges:
                glColor4fv((0.6, 0.6, 0.6, 1.0))
                glNormal3fv(surface.normal)
                glVertex3fv(verticiesInOrigin[vertex])
        glEnd()
        glBegin(GL_LINES)
        for edge in edges:
            for vertex in edge:
                glColor4fv((0.0, 0.0, 0.0, 1.0))
                glNormal3fv((0.0, 0.0, 0.0))
                glVertex3fv(verticiesInOrigin[vertex])
        glEnd()

    def draw(self, origin):
        self.draw_inside(origin)
        edges = (
            (0, 1),
            (0, 2),
            (0, 4),
            (1, 3),
            (1, 5),
            (7, 3),
            (7, 5),
            (7, 6),
            (6, 2),
            (6, 4),
            (3, 2),
            (5, 4)
        )
        surfaces = (
            #    Surface((0,2,6,4),(0,0,1)), #ground
            Surface((5, 7, 3, 1), (0, 0, 1)),  # ceiling
            Surface((4, 6, 7, 5), (1, 0, 0)),  # back face
            Surface((6, 2, 3, 7), (0, 1, 0)),  # left face looking from source
            Surface((1, 0, 4, 5), (0, -1, 0))  # right face looking from source

        )

        verticies = self.sommets_pave()
        verticiesInOrigin = []
        for v in verticies:
            verticiesInOrigin.append(v - origin)

        glBegin(GL_QUADS)
        for surface in surfaces:
            for vertex in surface.edges:
                glColor4fv((0.4, 0.4, 0.4, 1.0))
                glNormal3fv(surface.normal)
                glVertex3fv(verticiesInOrigin[vertex])
        glEnd()

        glBegin(GL_LINES)
        for edge in edges:
            for vertex in edge:
                glColor4fv((0.0, 0.0, 0.0, 1.0))
                glNormal3fv((0.0, 0.0, 0.0))
                glVertex3fv(verticiesInOrigin[vertex])
        glEnd()