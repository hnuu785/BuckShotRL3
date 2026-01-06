import numpy as np
from model import Agent
from utils import plotLearning
import data
import time

if(__name__ == "__main__"):
    load_checkpoint = True

    agent = Agent(gamma=0.99,epsilon=1,lr=4e-4, input_dims=[20],n_actions=7, mem_size=1_000_000, eps_min=0.01, batch_size=64,eps_dec=2e-5,replace=100)

    if load_checkpoint:
        agent.load_models()

    filename = 'BuckshotRoulette-DDDQN-Adam-lr5e4-replace100-1.png'
    scores, eps_history = [],[]
    num_games = 10000

    def on_connection_established(client_socket):
        print("Connection established")

        for i in range(num_games):
            done = False
            score = 0
            

            while not done:
                observation = data.get_state()
                time.sleep(6 / 50) #6 seconds between  actions
                action, was_random = agent.choose_action(observation)
                observation_, reward, done = data.play_step(action)
                print(was_random, ": ", reward)
                score += reward
                agent.store_transition(observation, action, reward, observation_, int(done))
                agent.learn()

            data.reset()
            scores.append(score)
            avg_score = np.mean(scores[-100:])
            print('episode', i, 'score %.lf' % score, 'average score %.lf ' % avg_score, 'epsilon %.2f ' % agent.epsilon)
            if i > 10 and i % 10 == 0:
                agent.save_models()

            eps_history.append(agent.epsilon)

        print("- training process over -")
        print("- creating model graph -")
        x = [i+1 for i in range(num_games)]
        plotLearning(x,scores,eps_history,filename)

            

    data.create_host(on_connection_established)