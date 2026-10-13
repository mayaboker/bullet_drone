"""Passive adapters record each real call once and delegate its behavior."""
from bullet_drone.contracts import MotorDynamics, PropellerModel, StabilizationController


class StabilizationProbe:
    def __init__(self, delegate: StabilizationController):
        self.delegate = delegate
        self.feedback = self.wrench = None

    def reset(self):
        self.feedback = self.wrench = None
        self.delegate.reset()

    def update(self, command, feedback, dt_s):
        result = self.delegate.update(command, feedback, dt_s)
        self.feedback, self.wrench = feedback, result
        return result


class MotorProbe:
    def __init__(self, delegate: MotorDynamics):
        self.delegate = delegate
        self.targets = self.actual = (0.,0.,0.,0.)

    def reset(self):
        self.targets = (0.,0.,0.,0.)
        self.actual = self.delegate.reset()
        return self.actual

    def update(self, targets_rad_s, dt_s):
        result = self.delegate.update(targets_rad_s, dt_s)
        self.targets, self.actual = targets_rad_s, result
        return result


class PropellerProbe:
    def __init__(self, delegate: PropellerModel):
        self.delegate = delegate
        self.output = None

    def calculate(self, speeds_rad_s):
        result = self.delegate.calculate(speeds_rad_s)
        self.output = result
        return result
