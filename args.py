import argparse

def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif v.lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise argparse.ArgumentTypeError("Boolean value expected.")


class ArgsConfig(object):
    
    def __init__(self) -> None:
        super().__init__()
    
        parser = argparse.ArgumentParser()

        # individual
        parser.add_argument("--m_s", type=float,
            help="the mean of the normal distribution of social opinions.") # second stage
        parser.add_argument("--sd_s", type=float,
            help="the sd of the normal distribution of social opinions.") # first stage
        parser.add_argument("--U_s", type=float,
            help="the constant value for social opinion uncertainty of the moderates.") # first stage
        parser.add_argument("--m_i", type=float,
            help="the mean of the normal distribution of individual benefit.") # second stage
        parser.add_argument("--sd_i", type=float, default=0.1,
            help="the sd of the normal distribution of individual benefit.")
        parser.add_argument("--U_i", type=float, default=0.01,
            help="the constant value for individual benefit uncertainty.")
        
        # network
        parser.add_argument("--N", type=int, default=1000,
            help="the number of individuals.")
        parser.add_argument("--ratio_ex", type=float,
            help="the ratio of the extremists.") # first stage
        parser.add_argument("--U_s_ex", type=float, default=0.01,
            help="the constant value for social opinion uncertainty of the extremists.")
        
        parser.add_argument("--net_media", type=str,
            help="low or high.") # first stage
        
        # dynamics
        parser.add_argument("--omega", type=float, default=0.5,
            help="the probability of transmitting the knowledge (during discussion).")
        parser.add_argument("--gamma", type=float, default=0.3,
            help="discussion propagation.")
        parser.add_argument("--mu", type=float, default=1.0,
            help="the intensity of the social influence (during discussion).")
        parser.add_argument("--rho", type=int, default=15,
            help="the number of steps necessary for the adoption decision.")
        
        # stages
        parser.add_argument("--first_stage", type=int,
            help="the parameter set of the first stage experiments.")
        parser.add_argument("--second_stage", type=int,
            help="the parameter set of the second stage experiments.")

        # models
        parser.add_argument("--n_steps", type=int, default=350,
            help="the number of individuals.")
        parser.add_argument("--n_runs", type=int, default=20,
            help="the number of runs.")
        parser.add_argument("--rnd_seed", type=int, default=664,
            help="random seed.")
        
        self.parser = parser


    @staticmethod
    def set_config_first(args, first:int) -> argparse.ArgumentParser:
        """
        Set the parameters for the first stage experiment (4 variables, 16 combination in total).
        """

        if not 0 <= int(first) < 16:
            raise ValueError("first should be in [0, 16).")
         
        first = int(first)
        args.first_stage = first

        # ==============
        # FIRST STAGE
        # ==============

        # set net_media
        if first % 2 == 0:
            args.net_media = "low"
        else:
            args.net_media = "high"
        
        # set sd_s
        if int(first / 2) % 2 == 1:
            args.sd_s = 0.3
        else:
            args.sd_s = 0.1
        
        # set ratio_ex
        if int(first/4) == 0 or int(first/4) == 2:
            args.ratio_ex = 0.0
        else:
            args.ratio_ex = 0.15
        
        # set U_s
        if first <= 7:
            args.U_s = 0.05
        else:
            args.U_s = 0.3

        return args
    

    @staticmethod
    def set_config_first_dict(args, dict) -> argparse.ArgumentParser:
        args.first_stage = -1
        args.net_media = dict["net_media"]
        args.sd_s = dict["sd_s"]
        args.ratio_ex = dict["ratio_ex"]
        args.U_s = dict["U_s"]
        return args
    
    
    @staticmethod
    def set_config_second(args, second:int) -> argparse.ArgumentParser:
        """
        Set the parameters for the second stage experiment (2 variables, 8 combination in total).
        """

        if not 0 <= int(second) < 8:
            raise ValueError("second should be in [0, 8).")
        
        second = int(second)
        args.second_stage = second

        if second == 0:
            args.m_s = -0.2
            args.m_i = -0.15
        if second == 1:
            args.m_s = -0.2
            args.m_i = 0.15
        if second == 2:
            args.m_s = -0.15
            args.m_i = -0.2
        if second == 3:
            args.m_s = -0.15
            args.m_i = 0.2
        if second == 4:
            args.m_s = 0.15
            args.m_i = -0.2
        if second == 5:
            args.m_s = 0.15
            args.m_i = 0.2
        if second == 6:
            args.m_s = 0.2
            args.m_i = -0.15
        if second == 7:
            args.m_s = 0.2
            args.m_i = 0.15
        
        return args
    

    @staticmethod
    def set_config_second_dict(args, dict) -> argparse.ArgumentParser:
        args.second_stage = -1
        args.m_s = dict["m_s"]
        args.m_i = dict["m_i"]
        return args


    def get_exp_args(self, first_stage_int=0, second_stage_int=0,
        first_param_dict=None, second_param_dict=None) -> argparse.ArgumentParser:
        """ 
        Set the configuration with a given parameter set (dict) or
        an integer for the configuration (int).
        """
        
        args = self.parser.parse_args()
        
        if first_param_dict is not None:
            args = self.set_config_first_dict(args, first_param_dict)
        else:
            args = self.set_config_first(args, first_stage_int)
        
        if second_param_dict is not None:
            args = self.set_config_second_dict(args, second_param_dict)
        else:
            args = self.set_config_second(args, second_stage_int)

        return args
    

    def get_args(self):
        """
        Set the configuration with the given int in command line.
        """
        args = self.parser.parse_args()
        if args.first_stage is None:
            raise ValueError("first_stage is not given.")
        if args.second_stage is None:
            raise ValueError("second_stage is not given.")
        
        args = self.set_config_first(args, args.first_stage)
        args = self.set_config_second(args, args.second_stage)

        return args

    
    @staticmethod
    def get_args_title_first(args: argparse.ArgumentParser) -> str:
        res = ["first_{}".format(args.first_stage)]
        res += [args.net_media]
        res += ["extrem_{}".format(args.ratio_ex)]
        res += ["sdS_{}".format(args.sd_s)]
        res += ["uS_{}".format(args.U_s)]
        return "_".join(res)
    

    @staticmethod
    def get_args_title_second(args: argparse.ArgumentParser) -> str:
        res = ["second_{}".format(args.second_stage)]
        res += ["mS_{}".format(args.m_s)]
        res += ["mI_{}".format(args.m_i)]
        return "_".join(res)
