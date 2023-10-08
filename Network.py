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

import numpy as np

from Game import Game
from Memory import ReplayBuffer

class Network:
    def __init__(self, Game) -> None:
        self.Game = Game
        self.Game.newEpisode()
        
        self.state_size = self.Game.Car.CarLine.lines + 4
        self.action_size = self.Game.Car.action_size
        
        self.training = False
        
        self.learning_rate = .00025
        self.possible_actions = np.identity(self.action_size, dtype=int)
        self.total_training_episode = 1000
        
        self.log_interval = 200
        self.eval_interval = 1000
        
        self.max_steps = 300
        
        self.batch_size = 4

        self.pretrain_length = self.batch_size
                
        my_env = MyEnvironment(self.Game, self.state_size, self.action_size)
        env = environments.tf_py_environment.TFPyEnvironment(my_env)
        
        self.DQN_network = DQN(self.Game, self.state_size, self.action_size, self.learning_rate, name='DQ_network', env=env)
        
        self.agent = self.DQN_network.agent
                
        self.time_step = my_env.reset()
        
        self.MemoryBuffer = ReplayBuffer(self)
        self.pretrain_avg = self.pretrain()
        
        self.driver = py_driver.PyDriver(my_env, py_tf_eager_policy.PyTFEagerPolicy(self.agent.collect_policy, use_tf_function=True), [self.MemoryBuffer.rb_observer], max_steps=self.max_steps)

    def pretrain(self):
        total_return = .0
        random_policy = random_tf_policy.RandomTFPolicy(self.DQN_network.env.time_step_spec(), self.DQN_network.env.action_spec())

        for i in range(1):
            time_step = self.DQN_network.env.reset()
            episode_return = .0

            while not time_step.is_last():
                action_step = random_policy.action(time_step)
                
                time_step = self.DQN_network.env.step(action_step.action)
                episode_return += time_step.reward
            
            total_return += episode_return
        
        avg_return = total_return / self.pretrain_length
        
        return avg_return.numpy()[0]
    
    def train(self):
        self.time_step, _ = self.driver.run(self.time_step)
        
        experience, unused_info = next(self.MemoryBuffer.iterator)
        train_loss = self.agent.train(experience).loss
        
        step = self.agent.train_step_counter.numpy()
        
        if step % self.log_interval == 0:
            print('step = {0}: loss = {1}'.format(step, train_loss))
                
class DQN:
    def __init__(self, Game, state_size, action_size, learning_rate, name, env) -> None:
        self.Game = Game
        
        self.units = (16, 16)
        
        self.state_size = state_size
        self.action_size = action_size
        self.learning_rate = learning_rate
        self.train_step_counter = tf.Variable(0)
        self.name = name
        
        self.env = env
        
        self.dense_layers = [self.createDenseLayer(num_unit) for num_unit in self.units]
        self.q_values_layer = tf.keras.layers.Dense(self.action_size, activation=tf.nn.elu, kernel_initializer=tf.keras.initializers.GlorotNormal())
                    
        self.q_net = sequential.Sequential(self.dense_layers + [self.q_values_layer])

        self.optimizer = tf.keras.optimizers.Adam(learning_rate=self.learning_rate)

        self.agent = dqn_agent.DqnAgent(self.env.time_step_spec(), self.env.action_spec(), q_network=self.q_net, optimizer=self.optimizer, td_errors_loss_fn=tf.keras.losses.MeanSquaredError(), train_step_counter=self.train_step_counter)
        
        self.agent.initialize()
            
    def createDenseLayer(self, units):
        return tf.keras.layers.Dense(units, activation=tf.nn.elu, kernel_initializer=tf.keras.initializers.GlorotNormal())
        
class MyEnvironment(environments.py_environment.PyEnvironment):
    def __init__(self, Game, state_size, action_size):
        self.Game = Game
        
        self._state = self.Game.getState()
        self._episode_ended = False
        
        self._action_spec = specs.array_spec.BoundedArraySpec(shape=(), dtype=np.float32, minimum=0, maximum=action_size - 1, name='action')
        self._observation_spec = specs.array_spec.BoundedArraySpec(shape=(34,), dtype=np.float32, minimum=np.array([0] * 34), maximum=np.array([1] * 34), name='observation')
        
    def action_spec(self):
        return self._action_spec

    def observation_spec(self):
        return self._observation_spec
    
    def _reset(self):
        self._episode_ended = False     
        self.Game.newEpisode()
        self._state = self.Game.getState()

        return ts.restart(self._state)

    def _step(self, action):
        self._episode_ended = self.Game.isEpisodeFinished()

        reward = self.Game.makeAction(action)
        self._state = self.Game.getState()

        if self._episode_ended:
            self.reset()
            return ts.termination(self._state, reward)
        else:
            return ts.transition(self._state, reward=reward, discount=1.0)
