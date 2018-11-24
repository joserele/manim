from constants import DEGREES
from constants import PRODUCTION_QUALITY_FRAME_DURATION
from continual_animation.update import ContinualGrowValue
from animation.transform import ApplyMethod
from camera.three_d_camera import ThreeDCamera
from mobject.coordinate_systems import ThreeDAxes
from mobject.geometry import Line
from mobject.three_dimensions import Sphere
from mobject.types.vectorized_mobject import VGroup
from mobject.types.vectorized_mobject import VectorizedPoint
from scene.scene import Scene
from utils.config_ops import digest_config
from utils.config_ops import merge_config


class ThreeDScene(Scene):
    CONFIG = {
        "camera_class": ThreeDCamera,
        "ambient_camera_rotation": None,
        "default_angled_camera_orientation_kwargs": {
            "phi": 70 * DEGREES,
            "theta": -135 * DEGREES,
        }
    }

    def set_camera_orientation(self, phi=None, theta=None, distance=None, gamma=None):
        if phi is not None:
            self.camera.set_phi(phi)
        if theta is not None:
            self.camera.set_theta(theta)
        if distance is not None:
            self.camera.set_distance(distance)
        if gamma is not None:
            self.camera.set_gamma(gamma)

    def begin_ambient_camera_rotation(self, rate=0.02):
        self.ambient_camera_rotation = ContinualGrowValue(
            self.camera.theta_tracker,
            rate=rate
        )
        self.add(self.ambient_camera_rotation)

    def stop_ambient_camera_rotation(self):
        if self.ambient_camera_rotation is not None:
            self.remove(self.ambient_camera_rotation)
        self.ambient_camera_rotation = None

    def move_camera(self,
                    phi=None,
                    theta=None,
                    distance=None,
                    gamma=None,
                    frame_center=None,
                    added_anims=[],
                    **kwargs):
        anims = []
        value_tracker_pairs = [
            (phi, self.camera.phi_tracker),
            (theta, self.camera.theta_tracker),
            (distance, self.camera.distance_tracker),
            (gamma, self.camera.gamma_tracker),
        ]
        for value, tracker in value_tracker_pairs:
            if value is not None:
                anims.append(
                    ApplyMethod(tracker.set_value, value, **kwargs)
                )
        if frame_center is not None:
            anims.append(ApplyMethod(
                self.camera.frame_center.move_to,
                frame_center
            ))
        is_camera_rotating = self.ambient_camera_rotation in self.continual_animations
        if is_camera_rotating:
            self.remove(self.ambient_camera_rotation)
        self.play(*anims + added_anims)
        if is_camera_rotating:
            self.add(self.ambient_camera_rotation)

    def get_moving_mobjects(self, *animations):
        moving_mobjects = Scene.get_moving_mobjects(self, *animations)
        camera_mobjects = self.camera.get_value_trackers()
        if any([cm in moving_mobjects for cm in camera_mobjects]):
            return self.mobjects
        return moving_mobjects

    def add_fixed_orientation_mobjects(self, *mobjects, **kwargs):
        self.add(*mobjects)
        self.camera.add_fixed_orientation_mobjects(*mobjects, **kwargs)

    def add_fixed_in_frame_mobjects(self, *mobjects):
        self.add(*mobjects)
        self.camera.add_fixed_in_frame_mobjects(*mobjects)

    def remove_fixed_orientation_mobjects(self, *mobjects):
        self.camera.remove_fixed_orientation_mobjects(*mobjects)

    def remove_fixed_in_frame_mobjects(self, *mobjects):
        self.camera.remove_fixed_in_frame_mobjects(*mobjects)

    ##
    def set_to_default_angled_camera_orientation(self, **kwargs):
        config = dict(self.default_camera_orientation_kwargs)
        config.update(kwargs)
        self.set_camera_orientation(**config)


class SpecialThreeDScene(ThreeDScene):
    CONFIG = {
        "cut_axes_at_radius": True,
    }

    def __init__(self, **kwargs):
        digest_config(self, kwargs)
        if self.frame_duration == PRODUCTION_QUALITY_FRAME_DURATION:
            high_quality = True
        else:
            high_quality = False
        default_config = self.get_quality_dependent_config(high_quality)
        config = merge_config([self.CONFIG, kwargs, default_config])
        ThreeDScene.__init__(self, **config)

    def get_quality_dependent_config(self, high_quality=True):
        hq_config = {
            "camera_config": {
                "should_apply_shading": True,
                "exponential_projection": True,
            },
            "three_d_axes_config": {
                "num_axis_pieces": 1,
                "number_line_config": {
                    "unit_size": 2,
                    # "tick_frequency": 0.5,
                    "tick_frequency": 1,
                    "numbers_with_elongated_ticks": [0, 1, 2],
                    "stroke_width": 2,
                }
            },
            "sphere_config": {
                "radius": 2,
                "resolution": (24, 48),
            }
        }
        lq_added_config = {
            "camera_config": {
                "should_apply_shading": False,
            },
            "three_d_axes_config": {
                "num_axis_pieces": 1,
            },
            "sphere_config": {
                "resolution": (12, 24),
            }
        }
        if high_quality:
            return hq_config
        else:
            return merge_config([
                lq_added_config,
                hq_config
            ])

    def get_axes(self):
        axes = ThreeDAxes(**self.three_d_axes_config)
        for axis in axes:
            if self.cut_axes_at_radius:
                p0 = axis.main_line.get_start()
                p1 = axis.number_to_point(-1)
                p2 = axis.number_to_point(1)
                p3 = axis.main_line.get_end()
                new_pieces = VGroup(
                    Line(p0, p1), Line(p1, p2), Line(p2, p3),
                )
                for piece in new_pieces:
                    piece.shade_in_3d = True
                new_pieces.match_style(axis.pieces)
                axis.pieces.submobjects = new_pieces.submobjects
            for tick in axis.tick_marks:
                tick.add(VectorizedPoint(
                    1.5 * tick.get_center(),
                ))
        return axes

    def get_sphere(self):
        return Sphere(**self.sphere_config)

    def get_default_camera_position(self):
        return {
            "phi": 70 * DEGREES,
            "theta": -110 * DEGREES,
        }

    def set_camera_to_default_position(self):
        self.set_camera_orientation(
            **self.get_default_camera_position()
        )
