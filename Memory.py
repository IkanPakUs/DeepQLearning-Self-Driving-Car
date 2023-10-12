import numpy as np
import reverb
from tf_agents.specs import tensor_spec
from tf_agents.replay_buffers import reverb_replay_buffer
from tf_agents.replay_buffers import reverb_utils
from tf_agents.trajectories import trajectory

class ReplayBuffer:
    def __init__(self, Network) -> None:
        self.Network = Network
        self.Agent = self.Network.DQN_network.agent
        self.replay_buffer_max_length = 100000
        
        self.table_name = 'uniform_table'
        
        replay_buffer_signature = tensor_spec.from_spec(self.Agent.collect_data_spec)
        replay_buffer_signature = tensor_spec.add_outer_dim(replay_buffer_signature)
        
        table = reverb.Table(self.table_name, max_size=self.replay_buffer_max_length, sampler=reverb.selectors.Prioritized(.8), remover=reverb.selectors.Fifo(), rate_limiter=reverb.rate_limiters.MinSize(10), signature=replay_buffer_signature)
        
        self.reverb_server = reverb.Server([table])

        self.replay_buffer = reverb_replay_buffer.ReverbReplayBuffer(self.Agent.collect_data_spec, table_name=self.table_name, sequence_length=2, local_server=self.reverb_server)        
        self.rb_observer = reverb_utils.ReverbAddTrajectoryObserver(self.replay_buffer.py_client, self.table_name, sequence_length=2)
        
        self.dataset = self.replay_buffer.as_dataset(num_parallel_calls=3, sample_batch_size=self.Network.batch_size, num_steps=2).prefetch(5)
        self.iterator = iter(self.dataset)