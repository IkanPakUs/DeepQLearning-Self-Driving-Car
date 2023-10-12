import tensorflow as tf
from tf_agents.networks import sequential
from tf_agents.agents.dqn import dqn_agent
from tf_agents import specs
from tf_agents import environments
from tf_agents.policies import py_tf_eager_policy
from tf_agents.policies import random_tf_policy
from tf_agents.trajectories import time_step as ts
from tf_agents.utils import common
from tf_agents.typing import types
from tf_agents.drivers import py_driver
from tf_agents.policies import PolicySaver
from tf_agents.trajectories import trajectory

import numpy as np

from Game import Game
from Memory import ReplayBuffer

class Network:
    def __init__(self, Game) -> None:
        self.Game = Game
        self.Game.newEpisode()
        
        self.num_episodes = 0
        
        self.state_size = self.Game.Car.CarLine.lines + 3
        self.action_size = self.Game.Car.action_size
        
        self.training = False
        
        self.learning_rate = .00025
        self.possible_actions = np.identity(self.action_size, dtype=int)
        self.total_training_episode = 1000
        
        self.log_interval = 200
        self.save_interval = 50000
                
        self.batch_size = 4

        self.pretrain_length = self.batch_size
                
        self.my_env = MyEnvironment(self.Game, self.state_size, self.action_size)
        self.env = environments.tf_py_environment.TFPyEnvironment(self.my_env)
        
        self.DQN_network = DQN(self.Game, self.state_size, self.action_size, self.learning_rate, name='DQ_network', env=self.env)
        
        self.agent = self.DQN_network.agent
        self.saver = PolicySaver(self.agent.collect_policy, batch_size=self.batch_size)
                
        self.time_step = self.my_env.reset()
        
        self.MemoryBuffer = ReplayBuffer(self)
        
        self.driver = py_driver.PyDriver(self.my_env, py_tf_eager_policy.PyTFEagerPolicy(self.agent.collect_policy, use_tf_function=True), [self.MemoryBuffer.rb_observer], max_steps=20, max_episodes=20)
        self.policy = self.driver.policy
        
        self.is_pretrain = False
        self.total_return = .0
        self.episode_return = .0
        self.avg_return = .0
        
        self.random_policy = random_tf_policy.RandomTFPolicy(self.DQN_network.env.time_step_spec(), self.DQN_network.env.action_spec())
        
        self.pretrain_avg = .0
        
    def pretrain(self, time_step):
        action_step = self.random_policy.action(time_step)
        
        time_step = self.DQN_network.env.step(action_step.action)
        self.episode_return += time_step.reward
        return time_step
    
    def train(self, step):
        if (self.time_step.is_first()):
            self.policy_step = self.policy.get_initial_state(1)
        
        action_step = self.policy.action(self.time_step, self.policy_step)
        next_time_step = self.my_env.step(action_step.action)
        
        if (self.my_env._episode_ended):
            return 4000
        
        action_step_with_previous_state = action_step._replace(state=self.policy_step)
        traj = trajectory.from_transition(self.time_step, action_step_with_previous_state, next_time_step)
        
        for observer in self.driver._transition_observers:
            observer((self.time_step, action_step_with_previous_state, next_time_step))
        for observer in self.driver.observers:
            observer(traj)
        for observer in self.driver.info_observers:
            observer(self.my_env.get_info())
            
        if self.driver._end_episode_on_boundary:
            self.num_episodes += np.sum(traj.is_boundary())
        else:
            self.num_episodes += np.sum(traj.is_last())

        self.time_step = next_time_step
        self.policy_step = action_step.state
        
        return step + np.sum(~traj.is_boundary())
            
    def validate(self):
        print('validate')
        experience, unused_info = next(self.MemoryBuffer.iterator)
        train_loss = self.agent.train(experience).loss
        
        step = self.agent.train_step_counter.numpy()
        
        if step % self.log_interval == 0:
            print('step = {0}: loss = {1}'.format(step, train_loss))
        
        if step % self.save_interval == 0:
            self.saver.save('./models/policy_%d' % step)
            
    def newEpisode(self):
        print('new episode')
        self.my_env.reset()
        self.Game.newEpisode()
                
class DQN:
    def __init__(self, Game, state_size, action_size, learning_rate, name, env) -> None:
        self.Game = Game
        
        self.units = (34, 18)
        
        self.state_size = state_size
        self.action_size = action_size
        self.learning_rate = learning_rate
        self.train_step_counter = tf.Variable(.0)
        self.name = name
        
        self.env = env
        
        self.dense_layers = [self.createDenseLayer(num_unit) for num_unit in self.units]
        self.q_values_layer = tf.keras.layers.Dense(self.action_size, activation=tf.nn.elu, kernel_initializer=tf.keras.initializers.RandomUniform(minval=-0.03, maxval=0.03), bias_initializer=tf.keras.initializers.Constant(-0.2))
                    
        self.q_net = sequential.Sequential(self.dense_layers + [self.q_values_layer])
        
        self.target_dense_layers = [self.createDenseLayer(num_unit) for num_unit in self.units]
        self.target_q_values_layer = tf.keras.layers.Dense(self.action_size, activation=tf.nn.elu, kernel_initializer=tf.keras.initializers.RandomUniform(minval=.03, maxval=.03), bias_initializer=tf.keras.initializers.Constant(-0.2))
        
        self.target_q_net = sequential.Sequential(self.target_dense_layers + [self.target_q_values_layer])

        self.optimizer = tf.keras.optimizers.Adam(learning_rate=self.learning_rate)

        self.agent = dqn_agent.DqnAgent(self.env.time_step_spec(), self.env.action_spec(), q_network=self.q_net, optimizer=self.optimizer, td_errors_loss_fn=common.element_wise_squared_loss, train_step_counter=self.train_step_counter, epsilon_greedy=.01, target_q_network=self.target_q_net, target_update_tau=0, target_update_period=1000, gamma=.9)
        
        self.agent.initialize()
            
    def createDenseLayer(self, units):
        return tf.keras.layers.Dense(units, activation=tf.nn.elu, kernel_initializer=tf.keras.initializers.VarianceScaling(scale=2.0, mode='fan_in', distribution='truncated_normal'))
        
class MyEnvironment(environments.py_environment.PyEnvironment):
    def __init__(self, Game, state_size, action_size):
        self.Game = Game
        
        self._state = self.Game.getState()
        self._episode_ended = False
        
        self._action_spec = specs.array_spec.BoundedArraySpec(shape=(), dtype=np.float32, minimum=0, maximum=action_size - 1, name='action')
        self._observation_spec = specs.array_spec.BoundedArraySpec(shape=(state_size,), dtype=np.float32, minimum=np.array([0] * state_size), maximum=np.array([1] * state_size), name='observation')
        
    def action_spec(self):
        return self._action_spec

    def observation_spec(self):
        return self._observation_spec
    
    def _reset(self):
        self.Game.newEpisode()
        
        self._episode_ended = False     
        self._state = self.Game.getState()

        return ts.restart(self._state)

    def _step(self, action):
        reward = self.Game.makeAction(action)
        self._state = self.Game.getState()

        self._episode_ended = self.Game.isEpisodeFinished()

        if self._episode_ended:
            return ts.termination(self._state, reward)
        else:
            return ts.transition(self._state, reward=reward, discount=.8)
