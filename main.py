import argparse
import itertools
import numpy as np

from args import ArgsConfig
from plot import PlotLinesHandler


class Agent:
    _ids = itertools.count(0)

    # set state constant
    NOT_CONCERNED = 0
    INFO_REQUEST = 1
    NO_ADOPTION = 2
    PRE_ADOPTION = 3
    ADOPTION = 4

    # set interest state constant
    NO = 11
    MAYBE = 12
    YES = 13

    def __init__(self, args: argparse.ArgumentParser) -> None:
        self.id = next(self._ids)
        self.args = args

        self.net = list()
        self.is_extrem = False

        # discussion-to-propagate queue
        self.t0_rd_queue = list()

        ## buffer for getting new information to propagate through discussion
        self.t0_rd_queue_new = list()

        ## buffer for getting information through discussion
        self.get_info_discussion = False

        # the first round that the agent started in the PRE_ADOPTION status
        self.yes_rd = None

        self._setup_state_variables(self.args)
    

    def _update_status(self, timestep):
        """
        1. update global opinion
        2. update interest
        3. update decision
        """
        if self.decision == Agent.ADOPTION:
            return

        # 1.
        if self.ind_benefit is None:
            self.glo_op = self.soc_op
            self.glo_U = self.soc_U
        else:
            self.glo_op = (self.soc_op + self.ind_benefit) / 2
            self.glo_U = (self.soc_U + self.ind_U) / 2
        
        # 2.
        if self.glo_op+self.glo_U < 0:
            self.interest = Agent.NO
            self.yes_rd = None
        elif self.glo_op-self.glo_U > 0:
            self.interest = Agent.YES
        else:
            self.interest = Agent.MAYBE
            self.yes_rd = None
        
        # 3.
        if not self.info:
            if self.interest == Agent.MAYBE or self.interest == Agent.YES:
                self.decision = Agent.INFO_REQUEST
            else:
                self.decision = Agent.NOT_CONCERNED
        else:
            if self.interest == Agent.MAYBE or self.interest == Agent.NO:
                self.decision = Agent.NO_ADOPTION
                self.yes_rd = None
            else:
                if self.yes_rd is not None and timestep - self.yes_rd >= self.args.rho:
                    self.decision = Agent.ADOPTION
                else:
                    self.decision = Agent.PRE_ADOPTION
                    if self.yes_rd is None:
                        self.yes_rd = timestep
    

    def _setup_state_variables(self, args):
        # social opinion
        self.soc_op = np.random.normal(loc=args.m_s, scale=args.sd_s)
        self.soc_U = args.U_s
        ## buffer for the changes during disccusion
        self.soc_op_delta = 0
        self.soc_U_delta = 0

        # individual opinion
        self.ind_benefit = None
        self.ind_U = None

        # information
        self.info = False

        # decision
        self.decision = -1

        # update other dependent variables
        self._update_status(timestep=0)
        

    @staticmethod
    def _draw(p) -> bool:
        return True if np.random.uniform() < p else False
    

    def _get_info_and_evaluate_benefit(self):
        self.info = True
        self.ind_benefit = np.random.normal(loc=self.args.m_i, scale=self.args.sd_i)
        self.ind_U = self.args.U_i


    def receive_info_media(self, timestep):
        if self.args.net_media == "low":
            p = 0.1
        elif self.args.net_media == "high":
            p = 0.4
        
        if self._draw(p):
            # receive information
            if not self.info and self.decision == Agent.INFO_REQUEST:
                self._get_info_and_evaluate_benefit()
                self._update_status(timestep)

            self.t0_rd_queue.append(timestep)
    

    def discuss(self, timestep):
        while len(self.t0_rd_queue):
            t0_rd = self.t0_rd_queue.pop(0)
            proportion = max(1-self.args.gamma*(timestep-t0_rd), 0)
            n_to_discuss = round(len(self.net)*proportion)
            if n_to_discuss == 0:
                continue
            
            # to discuss to a proportion of neighbors
            # (direction: self -> ag)
            chosen_ags = [self.net[i] for i in np.random.choice(np.arange(len(self.net)), size=n_to_discuss)]
            for ag in chosen_ags:
                # social influence
                h_ij = min(self.soc_op+self.soc_U, ag.soc_op+ag.soc_U) - max(self.soc_op-self.soc_U, ag.soc_op-ag.soc_U)
                if h_ij > self.soc_U:
                    ag.soc_op_delta += self.args.mu * (h_ij/self.soc_U - 1) * (self.soc_op - ag.soc_op)
                    ag.soc_U_delta += self.args.mu * (h_ij/self.soc_U - 1) * (self.soc_U - ag.soc_U)
                
                # receive information from other agent
                if self.info and (not ag.info and ag.decision == Agent.INFO_REQUEST):
                    if self._draw(self.args.omega):
                        ag.get_info_discussion = True
                
                ag.t0_rd_queue_new.append(t0_rd)
    

    def update(self, timestep):
        self.soc_op += self.soc_op_delta
        self.soc_U += self.soc_U_delta
        self.soc_op_delta = 0
        self.soc_U_delta = 0

        self.t0_rd_queue = self.t0_rd_queue_new
        self.t0_rd_queue_new = list()

        if self.get_info_discussion:
            self._get_info_and_evaluate_benefit()
            self.get_info_discussion = False

        self._update_status(timestep)


class InnovationDiffusion(object):

    def __init__(self, args: argparse.ArgumentParser, rnd_seed: int, verbose=True) -> None:
        super().__init__()
        Agent._ids = itertools.count(0)
        np.random.seed(rnd_seed)

        self.verbose = verbose
        self.args = args
        if self.verbose:
            print("Args: {}".format(args))

        self.ags = self.init_ags()

        # social opinions distribution
        self.soc_op_dis = np.array([[ag.soc_op for ag in self.ags]])
    

    @staticmethod
    def get_randint(low, high, exclude, size:int) -> list:
        """ Sample from [low, high). Return a list of ints. """
        ctr = 0
        s = np.zeros(high)
        s[exclude] = 1.0
        ans = list()
        while ctr < min(size, high-low):
            chosen_ag = np.random.randint(low, high)
            if s[chosen_ag] == 0.0:
                ans.append(chosen_ag)
                s[chosen_ag] = 1.0
                ctr += 1
        return ans


    def init_ags(self) -> list:
        # init agents
        ags = [Agent(self.args) for _ in range(self.args.N)]

        # set extremists
        if self.args.ratio_ex != 0.0:
            n_ex = round(self.args.N * self.args.ratio_ex)
            sorted_ag = sorted(ags, key=lambda ag:ag.soc_op, reverse=True)
            for i in range(n_ex):
                sorted_ag[i].is_extrem = True
                sorted_ag[i].soc_U = self.args.U_s_ex
                sorted_ag[i].update(timestep=0)

        # build net
        # method 1: randomly build ties
        if self.args.net_media == "low":
            n_edges = 1 * self.args.N
        elif self.args.net_media == "high":
            n_edges = 4 * self.args.N
        
        pool = np.arange(self.args.N)
        for _ in range(n_edges):
            ag_u_idx, ag_v_idx = np.random.choice(pool, replace=False, size=2)
            ags[ag_u_idx].net.append(ags[ag_v_idx])

        # method 2: every individual has exactly the same # of ties
        # for ag_idx in range(len(ags)):
        #     if self.args.net_media == "low":
        #         n_edges = 1
        #     elif self.args.net_media == "high":
        #         n_edges = 4
        #     for ag_v_idx in self.get_randint(0, len(ags), exclude=ag_idx, size=n_edges):
        #         ags[ag_idx].net.append(ags[ag_v_idx])
        
        return ags
    

    def get_result(self):
        """
        2 value will be returned.

        1. the ratio of informed agents
        2. the ratio of adopters
        """

        informed = sum([1 for ag in self.ags if ag.info])/self.args.N
        adopters = sum([1 for ag in self.ags if ag.decision == Agent.ADOPTION])/self.args.N
        not_concern = sum([1 for ag in self.ags if ag.decision == Agent.NOT_CONCERNED])/self.args.N
        return informed, adopters, not_concern
    

    def update_soc_op_dis(self):
        dis = np.array([[ag.soc_op for ag in self.ags]])
        self.soc_op_dis = np.concatenate((self.soc_op_dis, dis), axis=0)
    

    def get_soc_op_dis(self):
        return self.soc_op_dis


    def simulate_step(self, timestep):
        """
        Each timestep:
        1. each agent received information from the media a probability
        2. each agent initiates disccusion with its neighbors
        3. each agent update status
        """
        # 1.
        for ag in self.ags:
            ag.receive_info_media(timestep)
        
        # 2.
        for ag in self.ags:
            ag.discuss(timestep)

        # 3.
        for ag in self.ags:
            ag.update(timestep)
        
        self.update_soc_op_dis()
    

    def simulate(self, log_v=1):
        if self.verbose:
            informed, adopters, not_conern = self.get_result()
            print("| iter {} | informed: {:.2f}%; adopters: {:.2f}%; not_concern: {:.2f}%".format("  0", 
                informed*100,adopters*100, not_conern*100))

        for timestep in range(1, self.args.n_steps+1):
            self.simulate_step(timestep)
            if self.verbose and timestep % log_v == 0:
                informed, adopters, not_conern = self.get_result()
                print("| iter {} | informed: {:.2f}%; adopters: {:.2f}%; not_concern: {:.2f}%".format(("  "+str(timestep))[-3:],
                    informed*100, adopters*100, not_conern*100))




if __name__ == "__main__":
    parser = ArgsConfig()
    
    stable_convergence_int = 2
    central_convergence_int = 11
    shift_to_positive_extremism = 13
    central_extrem_convergence = 15
    
    # args = parser.get_exp_args(first_stage_int=11, second_stage_int=0)
    args = parser.get_args()

    soc_op_hd = PlotLinesHandler(xlabel="Time", ylabel="Opinion",
                                 ylabel_show="Opinion", x_lim=args.n_steps)
    game = InnovationDiffusion(args, rnd_seed=args.rnd_seed)
    game.simulate()

    soc_op = game.get_soc_op_dis()
    for ag_idx in range(soc_op.shape[1]):
        ag_soc_op = soc_op[:, ag_idx]
        soc_op_hd.plot_line(ag_soc_op, color="red" if game.ags[ag_idx].is_extrem else "green", linewidth=0.3)
    
    # title_param = "_".join(["rndSeed_{}".format(args.rnd_seed)] + ["{}_{}".format(k, v) for k, v in dict_to_use.items()])
    title_param = "_".join([ArgsConfig.get_args_title_first(args), ArgsConfig.get_args_title_second(args), "rndSeed_{}".format(args.rnd_seed)])    
    soc_op_hd.save_fig(title_param=title_param)