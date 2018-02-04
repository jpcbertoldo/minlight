import pygame
from pygame.locals import *
from src.calculs.modeles.entite_cable_robot import *
from src.calculs.graphics.trackball import Trackball
from OpenGL.GL import *
from OpenGL.GLU import *
from src.calculs.setups.parametres_objets import camera_position1,camera_position2,camera_position3,camera_position4, camera_direction
from src.calculs.graphics.cameraOpening import CameraOpening
import time
from numpy import radians


class RobotVisualization:

    def __init__(self, cable_robot,draw_maisonette ):
        print("Initializing cable robot.")
        self._cable_robot = copy.deepcopy(cable_robot)
        # self.reset_mvt_variables()
        self.light_off()
        self.window_height = 800
        self.window_width = 1200
        self.reset_mvt_variables()
        self.trackball = Trackball(self.window_width, self.window_height)
        self.mouse_position = (0, 0)
        self.draw_maisonette = draw_maisonette

    def light_on(self):
        self.use_shaders = True

    def light_off(self):
        self.use_shaders = False

    def set_display_dimensions(self, height, width):
        print("Setting display dimensions.")
        self.window_height = height
        self.window_width = width

    def set_uniforms(self):
        print("Setting shaders.")
        self.light_position_uniform = glGetUniformLocation(self.gl_program, "light_position")
        self.light_direction_uniform = glGetUniformLocation(self.gl_program, "light_direction")
        self.light_radius_uniform = glGetUniformLocation(self.gl_program, "light_radius")
        self.window_limit_top = glGetUniformLocation(self.gl_program,"window_limit_top")
        self.window_limit_bottom = glGetUniformLocation(self.gl_program, "window_limit_bottom")

    def update_uniforms(self):
        glUniform4fv(self.light_position_uniform, 1, self._cable_robot.get_light_centre() - self._cable_robot.get_centre() + (1,))
        glUniform4fv(self.light_direction_uniform, 1, self._cable_robot.get_light_direction() + (0,))
        glUniform1fv(self.light_radius_uniform, 1, self._cable_robot.get_light_radius())
        #glUniform1fv(self.window_limit_bottom, 1, )
        #glUniform1fv(self.window_limit_top,1, )


    def create_window(self):
        print("Creating window.")
        self.screen = pygame.display.set_mode((self.window_width, self.window_height), DOUBLEBUF | OPENGL | RESIZABLE | OPENGLBLIT)
        glClearColor(1.0, 1.0, 1.0, 1.0)
        pygame.init()

    def set_opengl_parameters(self):
        print("Setting opengl parameters.")
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)
        # setting line smooth parameters
        glEnable(GL_LINE_SMOOTH)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA_SATURATE, GL_ONE)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        glLineWidth(1.5)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        print("opengl parameters set.")
        glRotatef(-90, 1, 0, 0)

    def set_shaders(self):
        print("Setting shaders.")
        v = glCreateShader(GL_VERTEX_SHADER)
        f = glCreateShader(GL_FRAGMENT_SHADER)

        with open("graphics/shaders/simpleshader.frag", "r") as myfile:
            ftext = myfile.readlines()

        with open("graphics/shaders/simpleshader.vert", "r") as myfile:
            vtext = myfile.readlines()

        glShaderSource(v, vtext)
        glShaderSource(f, ftext)

        glCompileShader(v)
        glCompileShader(f)

        p = glCreateProgram()
        glAttachShader(p, v)
        glAttachShader(p, f)

        glLinkProgram(p)
        glUseProgram(p)

        self.gl_program = p

    def close_window(self):
        print("Closing window.")
        pygame.quit()
        quit()

    def reset_mvt_variables(self):
        print("Resetting mvt variables.")
        self.rotateX_CW = False
        self.rotateX_CCW = False
        self.rotateY_CW = False
        self.rotateY_CCW = False
        self.zoomIn = False
        self.zoomOut = False
        self.translate_source_X_pos = False
        self.translate_source_X_neg = False
        self.translate_source_Z_pos = False
        self.translate_source_Z_neg = False
        self.rotate_source_yaw_neg = False
        self.rotate_source_yaw_pos = False
        self.rotate_source_pitch_neg = False
        self.rotate_source_pitch_pos = False
        self.rotate_source_row_neg = False
        self.rotate_source_row_pos = False

    def reset_viewer_matrix(self):
        glLoadIdentity()
        gluPerspective(45, (self.window_width / self.window_height), 0.1, 50.0)
        glTranslatef(0, 0, -15)
        glRotatef(-90, 1, 0, 0)
        glScalef(0.001, 0.001, 0.001)

    def manage_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                self.trackball.startRotation(x, y)
                print("clicou")

            elif event.type == pygame.MOUSEBUTTONUP:
                self.trackball.stopRotation()
                print("soltou")

            elif event.type == pygame.MOUSEMOTION:
                a,b,c = event.buttons
                x,y = event.pos
                if(a or b or c):
                    self.trackball.updateRotation(x, y)

            elif event.type == pygame.KEYDOWN or event.type == KEYDOWN:
                if event.key == pygame.K_p:
                    self.rotateX_CW = True
                elif event.key == pygame.K_l:
                    self.rotateX_CCW = True
                elif event.key == pygame.K_o:
                    self.rotateY_CW = True
                elif event.key == pygame.K_k:
                    self.rotateY_CCW = True
                elif event.key == pygame.K_z:
                    self.zoomIn = True
                elif event.key == pygame.K_x:
                    self.zoomOut = True
                elif event.key == pygame.K_m:
                    self.rotate_source_pitch= True
                elif event.key == pygame.K_w:
                    self.translate_source_X_pos= True
                elif event.key == pygame.K_s:
                    self.translate_source_X_neg= True
                elif event.key == pygame.K_a:
                    self.translate_source_Z_pos = True
                elif event.key == pygame.K_d:
                    self.translate_source_Z_neg = True
                elif event.key == pygame.K_i:
                    self.rotate_source_yaw_pos = True
                elif event.key == pygame.K_j:
                    self.rotate_source_yaw_neg = True
                elif event.key == pygame.K_u:
                    self.rotate_source_pitch_pos = True
                elif event.key == pygame.K_h:
                    self.rotate_source_pitch_neg = True
                elif event.key == pygame.K_y:
                    self.rotate_source_row_pos = True
                elif event.key == pygame.K_g:
                    self.rotate_source_row_neg = True
                elif event.key == pygame.K_r:
                    self.reset_viewer_matrix()
                elif event.key == pygame.K_q:
                    pygame.quit()
                    quit()

            elif event.type == pygame.KEYUP or event.type == KEYUP:
                if event.key == pygame.K_p:
                    self.rotateX_CW = False
                elif event.key == pygame.K_l:
                    self.rotateX_CCW = False
                elif event.key == pygame.K_o:
                    self.rotateY_CW = False
                elif event.key == pygame.K_k:
                    self.rotateY_CCW = False
                elif event.key == pygame.K_z:
                    self.zoomIn = False
                elif event.key == pygame.K_x:
                    self.zoomOut = False
                elif event.key == pygame.K_w:
                    self.translate_source_X_pos= False
                elif event.key == pygame.K_s:
                    self.translate_source_X_neg= False
                elif event.key == pygame.K_a:
                    self.translate_source_Z_pos= False
                elif event.key == pygame.K_d:
                    self.translate_source_Z_neg= False
                elif event.key == pygame.K_m:
                    self.rotate_source_pitch = False
                elif event.key == pygame.K_i:
                    self.rotate_source_yaw_pos = False
                elif event.key == pygame.K_j:
                    self.rotate_source_yaw_neg = False
                elif event.key == pygame.K_u:
                    self.rotate_source_pitch_pos = False
                elif event.key == pygame.K_h:
                    self.rotate_source_pitch_neg = False
                elif event.key == pygame.K_y:
                    self.rotate_source_row_pos = False
                elif event.key == pygame.K_g:
                    self.rotate_source_row_neg = False

    def execute_transformations(self):

            if(self.rotateX_CW == True):
                glRotatef(2, 1, 0, 0)

            elif(self.rotateX_CCW == True):
                glRotatef(-2, 1, 0, 0)

            elif(self.rotateY_CW == True):
                glRotatef(2, 0, 0, 1)
            elif(self.rotateY_CCW == True):
                glRotatef(-2, 0, 0, 1)
            elif(self.zoomIn == True):
                glScalef(1.1,1.1,1.1)
            elif(self.zoomOut == True):
                glScalef(0.9,0.9,0.9)

            elif(self.translate_source_X_neg == True):
                self._cable_robot.translate_source(-5, 0, 0)
            elif(self.translate_source_X_pos == True):
                self._cable_robot.translate_source(5,0,0)
            elif(self.translate_source_Z_neg == True):
                self._cable_robot.translate_source(0,0,-5)
            elif(self.translate_source_Z_pos == True):
                self._cable_robot.translate_source(0,0,5)

            elif(self.rotate_source_yaw_pos == True):
                self._cable_robot.rotate_source(1,0,0)
            elif(self.rotate_source_yaw_neg == True):
                self._cable_robot.rotate_source(-1,0,0)
            elif(self.rotate_source_pitch_pos == True):
                self._cable_robot.rotate_source(0,1,0)
            elif(self.rotate_source_pitch_neg == True):
                self._cable_robot.rotate_source(0,-1,0)
            elif(self.rotate_source_row_pos == True):
                self._cable_robot.rotate_source(0,0,1)
            elif(self.rotate_source_row_neg == True):
                self._cable_robot.rotate_source(0,0,-1)

    def show(self):
        print("start drawing....")
        self.create_window()
        self.set_opengl_parameters()
        if(self.use_shaders):
            self.set_shaders()
            self.set_uniforms()
        origin = self._cable_robot.get_centre()

        self.reset_viewer_matrix()

        my_camera_opening1 = CameraOpening(camera_position1,camera_direction, radians(100))
        my_camera_opening2 = CameraOpening(camera_position2,camera_direction, radians(100))
        my_camera_opening3 = CameraOpening(camera_position3,camera_direction, radians(100))
        my_camera_opening4 = CameraOpening(camera_position4,camera_direction, radians(100))



        while True:
            self.manage_events()
            self.execute_transformations()
            if(self.use_shaders):
                self.update_uniforms()
            glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
            self._cable_robot.draw(origin,self.draw_maisonette)
            my_camera_opening1.draw()
        #    my_camera_opening2.draw()
        #    my_camera_opening3.draw()
        #    my_camera_opening4.draw()
            pygame.display.flip()
            pygame.time.wait(10)

    def draw_trajectory(self,trajectory, time_step,speed):
        print("start drawing trajectory....")
        print("step + " + str(time_step))
        self.create_window()
        self.set_opengl_parameters()
        if(self.use_shaders):
            self.set_shaders()
            self.set_uniforms()
        origin = self._cable_robot.get_centre()
        self.reset_viewer_matrix()
        initial_time = time.time()
        i = 0

        my_camera_opening1 = CameraOpening(camera_position1,camera_direction, radians(100))
        my_camera_opening2 = CameraOpening(camera_position2,camera_direction, radians(100))
        my_camera_opening3 = CameraOpening(camera_position3,camera_direction, radians(100))
        my_camera_opening4 = CameraOpening(camera_position4,camera_direction, radians(100))

        while True:
            self.manage_events()
            self.execute_transformations()
            if(self.use_shaders):
                self.update_uniforms()
            glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
            i = (time.time() - initial_time)
            i = i/time_step
            i = int(i*speed)
            self._cable_robot.set_source_position(trajectory[int(i% len(trajectory))].get_centre())
            self._cable_robot.set_source_angles(trajectory[int(i% len(trajectory))].get_angle())
            self._cable_robot.draw(origin,self.draw_maisonette)
            my_camera_opening1.draw()
            my_camera_opening2.draw()
            my_camera_opening3.draw()
            my_camera_opening4.draw()
            pygame.display.flip()
            pygame.time.wait(10)