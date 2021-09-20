from csaf.core.system import System
import typing
import f16lib.components as f16c


class F16Simple(System):
    components = {
        "plant": f16c.F16PlantComponent,
        "llc": f16c.F16LlcComponent,
        "autopilot": f16c.F16GcasComponent
    }

    connections = {
        ("llc", "inputs_pstates"): ("plant", "states"),
        ("llc", "inputs_poutputs"): ("plant", "outputs"),
        ("llc", "inputs_coutputs"): ("autopilot", "outputs"),
        ("plant", "inputs"): ("llc", "outputs"),
        ("autopilot", "inputs_poutputs"): ("plant", "outputs"),
        ("autopilot", "inputs_pstates"): ("plant", "states")
    }

    priority: typing.Optional[typing.Sequence[str]] = None


class F16AirspeedSimple(F16Simple):
    components = {
        "plant": f16c.F16PlantComponent,
        "llc": f16c.F16LlcComponent,
        "autopilot": f16c.F16AutoAirspeedComponent
    }


class F16Shield(System):
    components = {
        "llc": f16c.F16LlcComponent,
        "plant": f16c.F16PlantComponent,
        "autopilot": f16c.F16GcasComponent,
        "autoairspeed": f16c.F16AutoAirspeedComponent,
        "autoaltitude": f16c.F16AutoAltitudeComponent,
        "monitor": f16c.F16MonitorComponent,
        "switch": f16c.F16SwitchComponent
    }

    connections = {
        ("plant", "inputs"): ("llc", "outputs"),

        ("llc", "inputs_pstates"): ("plant", "states"),
        ("llc", "inputs_poutputs"): ("plant", "outputs"),
        ("llc", "inputs_coutputs"): ("switch", "outputs"),

        ("autopilot", "inputs_pstates"): ("plant", "states"),
        ("autopilot", "inputs_poutputs"): ("plant", "outputs"),
        ("autoairspeed", "inputs_pstates"): ("plant", "states"),
        ("autoairspeed", "inputs_poutputs"): ("plant", "outputs"),
        ("autoaltitude", "inputs_pstates"): ("plant", "states"),
        ("autoaltitude", "inputs_poutputs"): ("plant", "outputs"),

        ("monitor", "inputs_pstates"): ("plant", "states"),
        ("monitor", "inputs_poutputs"): ("plant", "outputs"),
        ("monitor", "inputs_gcas"): ("autopilot", "fdas"),

        ("switch", "inputs_0"): ("autopilot", "outputs"),
        ("switch", "inputs_1"): ("autoairspeed", "outputs"),
        ("switch", "inputs_2"): ("autoaltitude", "outputs"),
        ("switch", "inputs_monitors"): ("monitor", "outputs"),
    }


class F16MultiAgentCentral(System):
    from csaf import DiscreteComponent

    class CentralController(DiscreteComponent):
        """NOTE: this doesn't do much as it will be used in a SystemEnv"""

        from f16lib.messages import (EmptyMessage, F16PlantStateMessage,
                                     F16PlantOutputMessage, F16ControllerOutputMessage)

        name = "2 F16 Central Controller"
        sampling_frequency = 10.0
        default_initial_values = {
            "inputs_poutputs_0": [0.0,] * 4,
            "inputs_pstates_0": [0.0,] * 13,
            "inputs_poutputs_1": [0.0,] * 4,
            "inputs_pstates_1": [0.0,] * 13,
            "states": []
        }
        parameters: typing.Dict[str, typing.Any] = {}
        states = EmptyMessage
        inputs = (
            ("inputs_pstates_0", F16PlantStateMessage),
            ("inputs_poutputs_0", F16PlantOutputMessage),
            ("inputs_pstates_1", F16PlantStateMessage),
            ("inputs_poutputs_1", F16PlantOutputMessage),
        )
        outputs = (
            ("outputs_0", F16ControllerOutputMessage),
            ("outputs_1", F16ControllerOutputMessage),
        )
        flows = {
            "outputs_0": lambda m, t, s, y: [0.0,] * 4,
            "outputs_1": lambda m, t, s, y: [0.0,] * 4
        }

    components = {
        "plant_a": f16c.F16PlantComponent,
        "llc_a": f16c.F16LlcComponent,
        "plant_b": f16c.F16PlantComponent,
        "llc_b": f16c.F16LlcComponent,
        "autopilot": CentralController,
    }

    connections = {
        ("llc_a", "inputs_pstates"): ("plant_a", "states"),
        ("llc_a", "inputs_poutputs"): ("plant_a", "outputs"),
        ("llc_a", "inputs_coutputs"): ("autopilot", "outputs_0"),
        ("plant_a", "inputs"): ("llc_a", "outputs"),
        ("autopilot", "inputs_poutputs_0"): ("plant_a", "outputs"),
        ("autopilot", "inputs_pstates_0"): ("plant_a", "states"),

        ("llc_b", "inputs_pstates"): ("plant_b", "states"),
        ("llc_b", "inputs_poutputs"): ("plant_b", "outputs"),
        ("llc_b", "inputs_coutputs"): ("autopilot", "outputs_1"),
        ("plant_b", "inputs"): ("llc_b", "outputs"),
        ("autopilot", "inputs_poutputs_1"): ("plant_b", "outputs"),
        ("autopilot", "inputs_pstates_1"): ("plant_b", "states")
    }


class F16AcasShield(System):
    class F16AcasRecoveryComponent(f16c.create_nagents_acas_xu(1)):
        parameters = {
            **f16c.create_nagents_acas_xu(1).default_parameters,
            "roll_rates": (0, -3.0, 3.0, -6.0, 6.0)
        }

    components = {
        "plant": f16c.F16PlantComponent,
        "llc": f16c.F16LlcComponent,
        "autopilot": f16c.create_nagents_acas_xu(1),
        "autopilot_recovery": F16AcasRecoveryComponent,
        "switch": f16c.F16AcasRecoverySwitchComponent,
        "predictor": f16c.create_collision_predictor(1),
        "intruder_llc": f16c.F16LlcComponent,
        "intruder_plant": f16c.F16PlantComponent,
        "intruder_autopilot": f16c.F16AutoWaypointComponent
    }

    connections = {
        ("plant", "inputs"): ("llc", "outputs"),

        ("llc", "inputs_pstates"): ("plant", "states"),
        ("llc", "inputs_poutputs"): ("plant", "outputs"),
        ("llc", "inputs_coutputs"): ("switch", "outputs"),

        ("autopilot", "inputs_own"): ("plant", "states"),
        ("autopilot", "inputs_intruder0"): ("intruder_plant", "states"),

        ("autopilot_recovery", "inputs_own"): ("plant", "states"),
        ("autopilot_recovery", "inputs_intruder0"): ("intruder_plant", "states"),

        ("predictor", "inputs_own"): ("plant", "states"),
        ("predictor", "inputs_intruder0"): ("intruder_plant", "states"),

        ("switch", "inputs"): ("autopilot", "outputs"),
        ("switch", "inputs_recovery"): ("autopilot_recovery", "outputs"),
        ("switch", "inputs_select"): ("predictor", "outputs"),

        # setup the intruder plane
        ("intruder_llc", "inputs_pstates"): ("intruder_plant", "states"),
        ("intruder_llc", "inputs_poutputs"): ("intruder_plant", "outputs"),
        ("intruder_llc", "inputs_coutputs"): ("intruder_autopilot", "outputs"),
        ("intruder_plant", "inputs"): ("intruder_llc", "outputs"),
        ("intruder_autopilot", "inputs_poutputs"): ("intruder_plant", "outputs"),
        ("intruder_autopilot", "inputs_pstates"): ("intruder_plant", "states")
    }


class F16AcasShieldSurrogate(System):
    components = {
        "plant": f16c.F16PlantComponent,
        "llc": f16c.F16LlcComponent,
        "autopilot": f16c.create_nagents_acas_xu(1),
        "intruder_plant": f16c.F16PlantComponent,
    }

    connections = {
        ("plant", "inputs"): ("llc", "outputs"),

        ("llc", "inputs_pstates"): ("plant", "states"),
        ("llc", "inputs_poutputs"): ("plant", "outputs"),
        ("llc", "inputs_coutputs"): ("autopilot", "outputs"),

        ("autopilot", "inputs_own"): ("plant", "states"),
        ("autopilot", "inputs_intruder0"): ("intruder_plant", "states"),
    }


class F16AcasIntruderBalloon(System):
    components = {
        "plant": f16c.F16PlantComponent,
        "llc": f16c.F16LlcComponent,
        "acas": f16c.create_nagents_acas_xu(2),
        "waypoint": f16c.F16AutoWaypointComponent,
        "switch": f16c.F16AcasSwitchComponent,
        "intruder_llc": f16c.F16LlcComponent,
        "intruder_plant": f16c.F16PlantComponent,
        "intruder_autopilot": f16c.F16AutoWaypointComponent,
        "balloon": f16c.StaticObject
    }

    connections = {
        ("plant", "inputs"): ("llc", "outputs"),

        ("llc", "inputs_pstates"): ("plant", "states"),
        ("llc", "inputs_poutputs"): ("plant", "outputs"),
        ("llc", "inputs_coutputs"): ("switch", "outputs"),

        ("acas", "inputs_own"): ("plant", "states"),
        ("acas", "inputs_intruder1"): ("intruder_plant", "states"),
        ("acas", "inputs_intruder0"): ("balloon", "states"),

        ("waypoint", "inputs_poutputs"): ("plant", "outputs"),
        ("waypoint", "inputs_pstates"): ("plant", "states"),

        ("switch", "inputs"): ("waypoint", "outputs"),
        ("switch", "inputs_recovery"): ("acas", "outputs"),
        ("switch", "inputs_select"): ("acas", "states"),

        # setup the intruder plan
        ("intruder_llc", "inputs_pstates"): ("intruder_plant", "states"),
        ("intruder_llc", "inputs_poutputs"): ("intruder_plant", "outputs"),
        ("intruder_llc", "inputs_coutputs"): ("intruder_autopilot", "outputs"),

        ("intruder_plant", "inputs"): ("intruder_llc", "outputs"),

        ("intruder_autopilot", "inputs_poutputs"): ("intruder_plant", "outputs"),
        ("intruder_autopilot", "inputs_pstates"): ("intruder_plant", "states")
    }


class F16AcasShieldIntruderBalloon(System):
    class F16AcasRecoveryComponent(f16c.create_nagents_acas_xu(2)):
        parameters = {
            **f16c.create_nagents_acas_xu(1).default_parameters,
            "roll_rates": (0, -3.0, 3.0, -6.0, 6.0)
        }

    components = {
        "plant": f16c.F16PlantComponent,
        "llc": f16c.F16LlcComponent,
        "acas": f16c.create_nagents_acas_xu(2),
        "acas_recovery": F16AcasRecoveryComponent,
        "acas_switch": f16c.F16AcasRecoverySwitchComponent,
        "predictor": f16c.create_collision_predictor(2),
        "waypoint": f16c.F16AutoWaypointComponent,
        "switch": f16c.F16AcasSwitchComponent,
        "intruder_llc": f16c.F16LlcComponent,
        "intruder_plant": f16c.F16PlantComponent,
        "intruder_autopilot": f16c.F16AutoWaypointComponent,
        "balloon": f16c.StaticObject
    }

    connections = {
        ("plant", "inputs"): ("llc", "outputs"),

        ("llc", "inputs_pstates"): ("plant", "states"),
        ("llc", "inputs_poutputs"): ("plant", "outputs"),
        ("llc", "inputs_coutputs"): ("switch", "outputs"),

        ("acas", "inputs_own"): ("plant", "states"),
        ("acas", "inputs_intruder1"): ("intruder_plant", "states"),
        ("acas", "inputs_intruder0"): ("balloon", "states"),

        ("acas_recovery", "inputs_own"): ("plant", "states"),
        ("acas_recovery", "inputs_intruder1"): ("intruder_plant", "states"),
        ("acas_recovery", "inputs_intruder0"): ("balloon", "states"),

        ("predictor", "inputs_own"): ("plant", "states"),
        ("predictor", "inputs_intruder1"): ("intruder_plant", "states"),
        ("predictor", "inputs_intruder0"): ("balloon", "states"),

        ("acas_switch", "inputs"): ("acas", "outputs"),
        ("acas_switch", "inputs_recovery"): ("acas_recovery", "outputs"),
        ("acas_switch", "inputs_state"): ("acas", "states"),
        ("acas_switch", "inputs_recovery_state"): ("acas_recovery", "states"),
        ("acas_switch", "inputs_select"): ("predictor", "outputs"),

        ("waypoint", "inputs_poutputs"): ("plant", "outputs"),
        ("waypoint", "inputs_pstates"): ("plant", "states"),

        ("switch", "inputs"): ("waypoint", "outputs"),
        ("switch", "inputs_recovery"): ("acas_switch", "outputs"),
        ("switch", "inputs_select"): ("acas_switch", "outputs_state"),

        # setup the intruder plan
        ("intruder_llc", "inputs_pstates"): ("intruder_plant", "states"),
        ("intruder_llc", "inputs_poutputs"): ("intruder_plant", "outputs"),
        ("intruder_llc", "inputs_coutputs"): ("intruder_autopilot", "outputs"),

        ("intruder_plant", "inputs"): ("intruder_llc", "outputs"),

        ("intruder_autopilot", "inputs_poutputs"): ("intruder_plant", "outputs"),
        ("intruder_autopilot", "inputs_pstates"): ("intruder_plant", "states")
    }
